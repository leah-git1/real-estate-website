using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.Configuration;

namespace AI_SERVICE;

public class VoiceSearchAIService : IVoiceSearchService
{
    private const string OpenAiUrl = "https://api.openai.com/v1/chat/completions";
    private const string Model      = "gpt-4o-mini";

    private const string SystemPrompt = """
        You are a real estate search assistant. The user will send a search query in Hebrew or English.
        Extract the search intent and return ONLY a valid JSON object — no markdown, no explanation — with exactly these fields:
        {
          "City":       <string | null>,
          "Rooms":      <integer | null>,
          "MaxPrice":   <number | null>,
          "HasBalcony": <true | false | null>,
          "HasParking": <true | false | null>
        }
        Rules:
        - Prices are in ILS. Convert spoken amounts: "מיליון" / "million" → ×1,000,000. "אלף" / "thousand" → ×1,000.
        - If a feature (balcony / מרפסת, parking / חניה) is mentioned, set it to true.
        - If a feature is explicitly excluded, set it to false.
        - If a feature is not mentioned at all, set it to null.
        - Respond with the JSON object only.
        """;

    private readonly HttpClient    _http;
    private readonly string        _apiKey;

    public VoiceSearchAIService(IHttpClientFactory factory, IConfiguration config)
    {
        _http   = factory.CreateClient("openai");
        _apiKey = config["OpenAI:ApiKey"] ?? throw new InvalidOperationException("OpenAI:ApiKey is not configured.");
    }

    public async Task<PropertySearchParams> ParseAsync(string transcript)
    {
        var requestBody = new
        {
            model    = Model,
            messages = new[]
            {
                new { role = "system", content = SystemPrompt },
                new { role = "user",   content = transcript   }
            },
            temperature    = 0,
            max_tokens     = 256,
            response_format = new { type = "json_object" }
        };

        using var request = new HttpRequestMessage(HttpMethod.Post, OpenAiUrl);
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _apiKey);
        request.Content = new StringContent(
            JsonSerializer.Serialize(requestBody),
            Encoding.UTF8,
            "application/json"
        );

        var response = await _http.SendAsync(request);
        response.EnsureSuccessStatusCode();

        var raw  = await response.Content.ReadAsStringAsync();
        var json = JsonNode.Parse(raw)?["choices"]?[0]?["message"]?["content"]?.GetValue<string>() ?? "{}";

        return JsonSerializer.Deserialize<PropertySearchParams>(json, new JsonSerializerOptions
        {
            PropertyNameCaseInsensitive = true
        }) ?? new PropertySearchParams();
    }
}
