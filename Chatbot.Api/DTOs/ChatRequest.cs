using System.ComponentModel.DataAnnotations;

namespace Chatbot.Api.DTOs;

/// <summary>
/// Request body for <c>POST /api/chat</c>.
/// </summary>
public record ChatRequest
{
    /// <summary>Longest allowed message, shared by the API and the chat page.</summary>
    public const int MaxMessageLength = 4000;

    /// <summary>Existing conversation to continue. Omit to start a new conversation.</summary>
    public Guid? ConversationId { get; init; }

    /// <summary>The user's message.</summary>
    [Required(AllowEmptyStrings = false)]
    [MaxLength(MaxMessageLength)]
    public required string Message { get; init; }
}
