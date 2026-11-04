namespace Chatbot.Api.Models;

/// <summary>
/// A chat conversation, owning an ordered set of messages.
/// </summary>
public class Conversation
{
    public Guid Id { get; set; } = Guid.NewGuid();

    public string Title { get; set; } = string.Empty;

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    public List<Message> Messages { get; set; } = [];
}
