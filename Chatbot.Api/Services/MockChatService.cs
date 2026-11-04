using Chatbot.Api.Data;
using Chatbot.Api.Models;
using Microsoft.Extensions.Logging;

namespace Chatbot.Api.Services;

/// <summary>
/// Local stand-in used when no OpenRouter API key is configured (tests, fresh clones).
/// </summary>
public sealed class MockChatService(ChatbotDbContext db, ILogger<MockChatService> logger)
    : ChatServiceBase(db, logger)
{
    protected override Task<string> GenerateReplyAsync(
        Conversation conversation,
        IReadOnlyList<Message> history,
        CancellationToken cancellationToken)
    {
        var prompt = history.Count > 0 ? history[^1].Content : string.Empty;
        var reply = $"[mock] You said: \"{prompt}\". Configure OpenRouter:ApiKey to use a real model.";
        return Task.FromResult(reply);
    }
}
