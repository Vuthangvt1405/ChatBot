using Chatbot.Api.Data;
using Chatbot.Api.DTOs;
using Chatbot.Api.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;

namespace Chatbot.Api.Services;

/// <summary>
/// Shared conversation persistence. Providers only implement <see cref="GenerateReplyAsync"/>.
/// </summary>
public abstract class ChatServiceBase(ChatbotDbContext db, ILogger logger) : IChatService
{
    public async Task<ChatResponse> SendMessageAsync(ChatRequest request, CancellationToken cancellationToken)
    {
        Conversation conversation;

        if (request.ConversationId is { } conversationId)
        {
            conversation = await db.Conversations
                .FindAsync([conversationId], cancellationToken)
                ?? throw new ConversationNotFoundException(conversationId);
        }
        else
        {
            conversation = new Conversation { Title = BuildTitle(request.Message) };
            db.Conversations.Add(conversation);
        }

        db.Messages.Add(new Message
        {
            ConversationId = conversation.Id,
            Role = MessageRoles.User,
            Content = request.Message
        });

        await db.SaveChangesAsync(cancellationToken);

        var history = await db.Messages
            .AsNoTracking()
            .Where(m => m.ConversationId == conversation.Id)
            .OrderBy(m => m.CreatedAt)
            .ToListAsync(cancellationToken);

        var reply = await GenerateReplyAsync(conversation, history, cancellationToken);

        var assistantMessage = new Message
        {
            ConversationId = conversation.Id,
            Role = MessageRoles.Assistant,
            Content = reply
        };

        db.Messages.Add(assistantMessage);
        await db.SaveChangesAsync(cancellationToken);

        logger.LogInformation(
            "Conversation {ConversationId} handled a turn ({MessageCount} messages).",
            conversation.Id,
            history.Count + 1);

        return new ChatResponse(
            conversation.Id,
            assistantMessage.Id,
            assistantMessage.Content,
            assistantMessage.CreatedAt);
    }

    public async Task<ConversationDto?> GetConversationAsync(Guid conversationId, CancellationToken cancellationToken)
    {
        var conversation = await db.Conversations
            .AsNoTracking()
            .Include(c => c.Messages.OrderBy(m => m.CreatedAt))
            .FirstOrDefaultAsync(c => c.Id == conversationId, cancellationToken);

        if (conversation is null)
        {
            return null;
        }

        return new ConversationDto(
            conversation.Id,
            conversation.Title,
            conversation.CreatedAt,
            conversation.Messages
                .Select(m => new MessageDto(m.Id, m.Role, m.Content, m.CreatedAt))
                .ToList());
    }

    protected abstract Task<string> GenerateReplyAsync(
        Conversation conversation,
        IReadOnlyList<Message> history,
        CancellationToken cancellationToken);

    private static string BuildTitle(string message)
    {
        const int maxTitleLength = 60;
        var title = message.Trim();

        if (title.Length <= maxTitleLength)
        {
            return title;
        }

        return string.Concat(title.AsSpan(0, maxTitleLength).TrimEnd(), "…");
    }
}
