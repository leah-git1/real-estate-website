namespace AI_SERVICE;

public interface IVoiceSearchService
{
    Task<PropertySearchParams> ParseAsync(string transcript);
}
