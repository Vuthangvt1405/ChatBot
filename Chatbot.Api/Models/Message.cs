namespace Chatbot.Api.Models;

/// <summary>
/// A single message in a <see cref="Conversation"/>.
/// </summary>
public class Message
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public Guid ConversationId { get; set; }

    public Conversation? Conversation { get; set; }

    /// <summary>One of the values in <see cref="MessageRoles"/>.</summary>
    public required string Role { get; set; }

    public required string Content { get; set; }

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}

public static class MessageRoles
{
    public const string System = "system";
    public const string User = "user";
    public const string Assistant = "assistant";
}
