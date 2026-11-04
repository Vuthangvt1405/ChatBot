namespace Chatbot.Api.DTOs;

/// <summary>
/// Result of a chat turn: the assistant's reply plus the identifiers needed to continue.
/// </summary>
public record ChatResponse(
    Guid ConversationId,
    Guid MessageId,
    string Reply,
    DateTime CreatedAt);
