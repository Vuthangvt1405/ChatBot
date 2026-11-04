using System.Net;
using System.Net.Http.Json;
using Chatbot.Api.DTOs;

namespace Chatbot.Api.Tests;

public sealed class ChatEndpointTests(ChatbotApiFactory factory) : IClassFixture<ChatbotApiFactory>
{
    private readonly HttpClient _client = factory.CreateClient();

    [Fact]
    public async Task Health_ReturnsHealthy()
    {
        var response = await _client.GetAsync("/health");

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.Equal("Healthy", await response.Content.ReadAsStringAsync());
    }

    [Fact]
    public async Task Root_ServesChatPage()
    {
        var response = await _client.GetAsync("/");

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        Assert.Equal("text/html", response.Content.Headers.ContentType?.MediaType);
        Assert.Contains("id=\"chat-form\"", await response.Content.ReadAsStringAsync());
    }

    [Fact]
    public async Task ApiRoutes_AreNotReplacedByChatPage()
    {
        var response = await _client.GetAsync($"/api/chat/{Guid.NewGuid()}/messages");

        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
        Assert.NotEqual("text/html", response.Content.Headers.ContentType?.MediaType);
    }

    [Fact]
    public async Task SendMessage_StartsConversation_AndReturnsReply()
    {
        var response = await _client.PostAsJsonAsync("/api/chat", new { message = "Hello there" });

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var chat = await response.Content.ReadFromJsonAsync<ChatResponse>();

        Assert.NotNull(chat);
        Assert.NotEqual(Guid.Empty, chat.ConversationId);
        Assert.NotEqual(Guid.Empty, chat.MessageId);
        Assert.Contains("Hello there", chat.Reply);
        Assert.Contains("[mock]", chat.Reply);
    }

    [Fact]
    public async Task SendMessage_ContinuesConversation_AndPersistsHistory()
    {
        var first = await PostChatAsync(new { message = "First message" });
        var second = await PostChatAsync(new { conversationId = first.ConversationId, message = "Second message" });

        Assert.Equal(first.ConversationId, second.ConversationId);

        var historyResponse = await _client.GetAsync($"/api/chat/{first.ConversationId}/messages");
        Assert.Equal(HttpStatusCode.OK, historyResponse.StatusCode);

        var conversation = await historyResponse.Content.ReadFromJsonAsync<ConversationDto>();

        Assert.NotNull(conversation);
        Assert.Equal(first.ConversationId, conversation.Id);
        Assert.Equal(4, conversation.Messages.Count);
        Assert.Equal("user", conversation.Messages[0].Role);
        Assert.Equal("First message", conversation.Messages[0].Content);
        Assert.Equal("assistant", conversation.Messages[1].Role);
        Assert.Equal("user", conversation.Messages[2].Role);
        Assert.Equal("Second message", conversation.Messages[2].Content);
        Assert.Equal("assistant", conversation.Messages[3].Role);
    }

    [Fact]
    public async Task SendMessage_WithEmptyMessage_Returns400()
    {
        var response = await _client.PostAsJsonAsync("/api/chat", new { message = "" });

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
    }

    // US-3 BR-2: the API and the chat page share ChatRequest.MaxMessageLength (4000).
    [Fact]
    public async Task SendMessage_With4000Chars_Returns200()
    {
        var response = await _client.PostAsJsonAsync("/api/chat", new { message = new string('a', 4000) });

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }

    [Fact]
    public async Task SendMessage_With4001Chars_Returns400()
    {
        var response = await _client.PostAsJsonAsync("/api/chat", new { message = new string('a', 4001) });

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
    }

    [Fact]
    public async Task SendMessage_WithUnknownConversation_Returns404()
    {
        var response = await _client.PostAsJsonAsync("/api/chat", new
        {
            conversationId = Guid.NewGuid(),
            message = "Does this conversation exist?"
        });

        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    [Fact]
    public async Task GetMessages_WithUnknownConversation_Returns404()
    {
        var response = await _client.GetAsync($"/api/chat/{Guid.NewGuid()}/messages");

        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    private async Task<ChatResponse> PostChatAsync(object body)
    {
        var response = await _client.PostAsJsonAsync("/api/chat", body);
        response.EnsureSuccessStatusCode();

        var chat = await response.Content.ReadFromJsonAsync<ChatResponse>();
        Assert.NotNull(chat);
        return chat;
    }
}
