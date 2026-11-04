namespace Chatbot.Api.Services;

/// <summary>
/// Thrown when a request targets a conversation that does not exist.
/// </summary>
public sealed class ConversationNotFoundException(Guid conversationId)
    : Exception($"Conversation '{conversationId}' was not found.")
{
    public Guid ConversationId { get; } = conversationId;
}

/// <summary>
/// Thrown when the upstream chat provider fails. The message is safe to return to clients.
/// </summary>
public sealed class ChatProviderException(string message) : Exception(message);
