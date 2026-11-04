using Chatbot.Api.DTOs;
using Chatbot.Api.Services;
using Microsoft.AspNetCore.Mvc;

namespace Chatbot.Api.Controllers;

[ApiController]
[Route("api/chat")]
[Produces("application/json")]
public sealed class ChatController(IChatService chatService, ILogger<ChatController> logger) : ControllerBase
{
    /// <summary>Sends a message and returns the assistant's reply.</summary>
    /// <remarks>Omit <c>conversationId</c> to start a new conversation.</remarks>
    [HttpPost]
    [ProducesResponseType<ChatResponse>(StatusCodes.Status200OK)]
    [ProducesResponseType<ValidationProblemDetails>(StatusCodes.Status400BadRequest)]
    [ProducesResponseType<ProblemDetails>(StatusCodes.Status404NotFound)]
    [ProducesResponseType<ProblemDetails>(StatusCodes.Status502BadGateway)]
    public async Task<ActionResult<ChatResponse>> SendMessage(
        [FromBody] ChatRequest request,
        CancellationToken cancellationToken)
    {
        try
        {
            var response = await chatService.SendMessageAsync(request, cancellationToken);
            return Ok(response);
        }
        catch (ConversationNotFoundException ex)
        {
            return NotFound(new ProblemDetails
            {
                Title = "Conversation not found",
                Detail = ex.Message,
                Status = StatusCodes.Status404NotFound
            });
        }
        catch (ChatProviderException ex)
        {
            logger.LogWarning(ex, "Chat provider failed.");
            return Problem(
                title: "Chat provider error",
                detail: ex.Message,
                statusCode: StatusCodes.Status502BadGateway);
        }
    }

    /// <summary>Returns the stored message history for a conversation.</summary>
    [HttpGet("{conversationId:guid}/messages")]
    [ProducesResponseType<ConversationDto>(StatusCodes.Status200OK)]
    [ProducesResponseType<ProblemDetails>(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<ConversationDto>> GetMessages(
        Guid conversationId,
        CancellationToken cancellationToken)
    {
        var conversation = await chatService.GetConversationAsync(conversationId, cancellationToken);

        if (conversation is null)
        {
            return NotFound(new ProblemDetails
            {
                Title = "Conversation not found",
                Detail = $"Conversation '{conversationId}' was not found.",
                Status = StatusCodes.Status404NotFound
            });
        }

        return Ok(conversation);
    }
}
