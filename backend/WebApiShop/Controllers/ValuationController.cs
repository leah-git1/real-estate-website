using System.Net.Http.Headers;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.AspNetCore.Mvc;

[ApiController]
[Route("api/[controller]")]
[DisableRequestSizeLimit]
[RequestFormLimits(MultipartBodyLengthLimit = 209_715_200)] // 200 MB
public class ValuationController : ControllerBase
{
    private static readonly HashSet<string> AllowedMime =
        ["image/jpeg", "image/png", "image/webp", "image/gif"];

    private readonly HttpClient _aiService;

    public ValuationController(IHttpClientFactory factory)
        => _aiService = factory.CreateClient("ai_service");

    [HttpPost("upload")]
    public async Task<IActionResult> Upload([FromForm] ValuationFormRequest req)
    {
        if (string.IsNullOrWhiteSpace(req.Address) || string.IsNullOrWhiteSpace(req.City))
            return BadRequest("Address and city are required.");

        // ── Validate every uploaded file is an image ──────────────────────
        var imageFiles = req.Images ?? [];
        foreach (var file in imageFiles)
        {
            if (!AllowedMime.Contains(file.ContentType))
                return BadRequest($"File '{file.FileName}' is not a supported image type. " +
                                  "Only JPEG, PNG, WebP and GIF are accepted.");
        }

        // ── Resolve user identity ─────────────────────────────────────────
        var userIdHeader = Request.Headers["UserId"].FirstOrDefault();
        var isGuest      = string.IsNullOrWhiteSpace(userIdHeader) || userIdHeader == "0";

        // ── Build multipart request to Python ─────────────────────────────
        using var multipart = new MultipartFormDataContent();
        multipart.Add(new StringContent(req.Address),        "address");
        multipart.Add(new StringContent(req.City),           "city");
        multipart.Add(new StringContent(req.Rooms.ToString()), "rooms");
        multipart.Add(new StringContent(req.Sqm.ToString()),   "sqm");

        // Stream each image directly — no base64, no full buffering
        var streams = new List<Stream>();
        foreach (var file in imageFiles.Take(4))
        {
            var stream  = file.OpenReadStream();
            streams.Add(stream);
            var content = new StreamContent(stream);
            content.Headers.ContentType = new MediaTypeHeaderValue(file.ContentType);
            multipart.Add(content, "images", file.FileName);
        }

        try
        {
            var aiResponse = await _aiService.PostAsync("/analyze-property-multipart", multipart);

            if (!aiResponse.IsSuccessStatusCode)
            {
                var err = await aiResponse.Content.ReadAsStringAsync();
                return StatusCode(502, $"AI service error: {err}");
            }

            var full = await aiResponse.Content.ReadFromJsonAsync<ValuationResult>(
                new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
            );

            if (full is null)
                return StatusCode(502, "AI service returned an empty response.");

            // ── Gate: guests only get the price range ─────────────────────
            if (isGuest)
                return Ok(new GuestValuationResponse { IsGuest = true, PriceRange = full.PriceRange });

            return Ok(new FullValuationResponse
            {
                IsGuest    = false,
                Valuation  = full.Valuation,
                Confidence = full.Confidence,
                PriceRange = full.PriceRange,
                Details    = full.Details
            });
        }
        finally
        {
            // Dispose all opened streams regardless of outcome
            foreach (var s in streams) await s.DisposeAsync();
        }
    }
}

// ── Form request (multipart) ──────────────────────────────────────────────────

public class ValuationFormRequest
{
    [FromForm] public string          Address { get; set; } = "";
    [FromForm] public string          City    { get; set; } = "";
    [FromForm] public int             Rooms   { get; set; }
    [FromForm] public int             Sqm     { get; set; }
    [FromForm] public List<IFormFile>? Images  { get; set; }
}

// ── AI service response (internal) ───────────────────────────────────────────

public class ValuationResult
{
    [JsonPropertyName("valuation")]   public decimal?          Valuation  { get; set; }
    [JsonPropertyName("confidence")]  public double?           Confidence { get; set; }
    [JsonPropertyName("price_range")] public PriceRange?       PriceRange { get; set; }
    [JsonPropertyName("details")]     public ValuationDetails? Details    { get; set; }
}

public class PriceRange
{
    [JsonPropertyName("min")] public decimal Min { get; set; }
    [JsonPropertyName("max")] public decimal Max { get; set; }
}

public class ValuationDetails
{
    [JsonPropertyName("kitchen")]     public string Kitchen     { get; set; } = "";
    [JsonPropertyName("lighting")]    public string Lighting    { get; set; } = "";
    [JsonPropertyName("renovations")] public string Renovations { get; set; } = "";
    [JsonPropertyName("flooring")]    public string Flooring    { get; set; } = "";
    [JsonPropertyName("overall")]     public string Overall     { get; set; } = "";
}

// ── API responses ─────────────────────────────────────────────────────────────

public class GuestValuationResponse
{
    public bool        IsGuest    { get; set; }
    public PriceRange? PriceRange { get; set; }
}

public class FullValuationResponse
{
    public bool              IsGuest    { get; set; }
    public decimal?          Valuation  { get; set; }
    public double?           Confidence { get; set; }
    public PriceRange?       PriceRange { get; set; }
    public ValuationDetails? Details    { get; set; }
}
