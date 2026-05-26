using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.AspNetCore.Mvc;

[ApiController]
[Route("api/search")]
public class VoiceSearchController : ControllerBase
{
    private readonly HttpClient _aiService;

    public VoiceSearchController(IHttpClientFactory factory)
        => _aiService = factory.CreateClient("ai_service");

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

        // ── Mock LINQ query — swap List for real DbContext.Properties ─────
        var mockProperties = new List<PropertyRecord>
        {
            new(1, "Tel Aviv",   4, 2_800_000m, true,  true),
            new(2, "Jerusalem",  3, 1_500_000m, false, true),
            new(3, "Tel Aviv",   5, 3_200_000m, true,  false),
            new(4, "Haifa",      3, 1_200_000m, true,  true),
            new(5, "Tel Aviv",   4, 2_400_000m, false, false),
        };

        var results = mockProperties
            .Where(p => filters.City       == null || p.City.Contains(filters.City, StringComparison.OrdinalIgnoreCase))
            .Where(p => filters.Rooms      == null || p.Rooms == filters.Rooms)
            .Where(p => filters.MaxPrice   == null || p.Price <= filters.MaxPrice)
            .Where(p => filters.HasBalcony == null || p.HasBalcony == filters.HasBalcony)
            .Where(p => filters.HasParking == null || p.HasParking == filters.HasParking)
            .ToList();

        return Ok(new { filters, results });
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

public record PropertyRecord(int Id, string City, int Rooms, decimal Price, bool HasBalcony, bool HasParking);
