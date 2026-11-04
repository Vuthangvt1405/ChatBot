using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using Chatbot.Api.Data;
using Chatbot.Api.Models;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace Chatbot.Api.Services;

/// <summary>
/// Sends the conversation to OpenRouter's <c>/chat/completions</c> endpoint and returns the reply.
/// </summary>
public sealed class OpenRouterChatService(
    ChatbotDbContext db,
    HttpClient httpClient,
    IOptions<OpenRouterOptions> options,
    ILogger<OpenRouterChatService> logger) : ChatServiceBase(db, logger)
{
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    private readonly OpenRouterOptions _options = options.Value;

    protected override async Task<string> GenerateReplyAsync(
        Conversation conversation,
        IReadOnlyList<Message> history,
        CancellationToken cancellationToken)
    {
        var messages = new List<OpenRouterMessage>();

        if (!string.IsNullOrWhiteSpace(_options.SystemPrompt))
        {
            messages.Add(new OpenRouterMessage(MessageRoles.System, _options.SystemPrompt));
        }

        var maxHistory = Math.Max(1, _options.MaxHistoryMessages);
        messages.AddRange(history
            .TakeLast(maxHistory)
            .Select(m => new OpenRouterMessage(m.Role, m.Content)));

        using var httpRequest = new HttpRequestMessage(HttpMethod.Post, "chat/completions")
        {
            Content = JsonContent.Create(
                new OpenRouterRequest(_options.Model, messages),
                options: JsonOptions)
        };

        httpRequest.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _options.ApiKey);

        if (!string.IsNullOrWhiteSpace(_options.SiteUrl))
        {
            httpRequest.Headers.TryAddWithoutValidation("HTTP-Referer", _options.SiteUrl);
        }

        if (!string.IsNullOrWhiteSpace(_options.AppName))
        {
            httpRequest.Headers.TryAddWithoutValidation("X-Title", _options.AppName);
        }

        using var response = await httpClient.SendAsync(httpRequest, cancellationToken);

        if (!response.IsSuccessStatusCode)
        {
            var body = await response.Content.ReadAsStringAsync(cancellationToken);
            logger.LogError(
                "OpenRouter request failed with {StatusCode}: {Body}",
                (int)response.StatusCode,
                Truncate(body));

            throw new ChatProviderException(
                "The chat provider rejected the request. Check the API key, model name, and quota.");
        }

        var completion = await response.Content.ReadFromJsonAsync<OpenRouterResponse>(JsonOptions, cancellationToken);
        var content = completion?.Choices?.FirstOrDefault()?.Message?.Content;

        if (string.IsNullOrWhiteSpace(content))
        {
            logger.LogError("OpenRouter returned an empty completion for model {Model}.", _options.Model);
            throw new ChatProviderException("The chat provider returned an empty response.");
        }

        return content;
    }

    private static string Truncate(string value) => value.Length <= 1000 ? value : value[..1000];

    private sealed record OpenRouterMessage(string Role, string Content);

    private sealed record OpenRouterRequest(string Model, IReadOnlyList<OpenRouterMessage> Messages);

    private sealed record OpenRouterResponse(List<OpenRouterChoice>? Choices);

    private sealed record OpenRouterChoice(OpenRouterMessage? Message);
}
