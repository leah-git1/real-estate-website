using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.AspNetCore.Mvc;
using Repository;

[ApiController]
[Route("api/search")]
public class VoiceSearchController : ControllerBase
{
    private readonly HttpClient _aiService;
    private readonly IProductRepository _products;

    public VoiceSearchController(IHttpClientFactory factory, IProductRepository products)
    {
        _aiService = factory.CreateClient("ai_service");
        _products  = products;
    }

    [HttpPost("voice")]
    public async Task<IActionResult> VoiceSearch([FromBody] VoiceSearchRequest req)
    {
        if (string.IsNullOrWhiteSpace(req.Transcript))
            return BadRequest("Transcript is required.");

        // ── Forward to Python ai_service ──────────────────────────────────
        var payload = new StringContent(
            JsonSerializer.Serialize(new { transcript = req.Transcript }),
            Encoding.UTF8,
            "application/json"
        );

        var aiResponse = await _aiService.PostAsync("/parse-search", payload);
        if (!aiResponse.IsSuccessStatusCode)
            return StatusCode(502, "AI service failed to parse the transcript.");

        var filters = await aiResponse.Content.ReadFromJsonAsync<PropertySearchFilters>(
            new JsonSerializerOptions { PropertyNameCaseInsensitive = true }
        );

        if (filters is null)
            return StatusCode(502, "AI service returned an empty response.");

        // ── Query real DB via existing repository ─────────────────────────
        var (allMatches, total) = await _products.GetProducts(
            categoryIds: [],
            title:       null,
            city:        filters.City,
            minPrice:    null,
            maxPrice:    filters.MaxPrice,
            rooms:       filters.Rooms,
            beds:        null,
            position:    1,
            skip:        50       // return up to 50 voice-search results
        );

        return Ok(new { filters, results = allMatches });
    }
}

// ── DTOs ──────────────────────────────────────────────────────────────────────

public record VoiceSearchRequest(string Transcript);

public class PropertySearchFilters
{
    [JsonPropertyName("city")]        public string?  City       { get; set; }
    [JsonPropertyName("rooms")]       public int?     Rooms      { get; set; }
    [JsonPropertyName("max_price")]   public decimal? MaxPrice   { get; set; }
    [JsonPropertyName("has_balcony")] public bool?    HasBalcony { get; set; }
    [JsonPropertyName("has_parking")] public bool?    HasParking { get; set; }
}
