namespace Chatbot.Api.DTOs;

public record MessageDto(
    Guid Id,
    string Role,
    string Content,
    DateTime CreatedAt);

public record ConversationDto(
    Guid Id,
    string Title,
    DateTime CreatedAt,
    IReadOnlyList<MessageDto> Messages);
