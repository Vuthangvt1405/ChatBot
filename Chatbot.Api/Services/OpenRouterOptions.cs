namespace Chatbot.Api.Services;

public sealed class OpenRouterOptions
{
    public const string SectionName = "OpenRouter";

    /// <summary>Set via user secrets in development or the OpenRouter__ApiKey environment variable elsewhere.</summary>
    public string ApiKey { get; set; } = string.Empty;

    public string BaseUrl { get; set; } = "https://openrouter.ai/api/v1/";

    public string Model { get; set; } = "stealth/crouton-alpha";

    public string SystemPrompt { get; set; } = "You are a helpful, concise assistant.";

    /// <summary>Optional site URL forwarded to OpenRouter for attribution.</summary>
    public string? SiteUrl { get; set; }

    /// <summary>Optional app name forwarded to OpenRouter for attribution.</summary>
    public string? AppName { get; set; }

    /// <summary>How many recent messages to send as context.</summary>
    public int MaxHistoryMessages { get; set; } = 20;
}
