using Chatbot.Api.DTOs;

namespace Chatbot.Api.Services;

public interface IChatService
{
    Task<ChatResponse> SendMessageAsync(ChatRequest request, CancellationToken cancellationToken);

    Task<ConversationDto?> GetConversationAsync(Guid conversationId, CancellationToken cancellationToken);
}
