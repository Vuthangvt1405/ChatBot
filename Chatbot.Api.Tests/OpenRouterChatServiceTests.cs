using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using Chatbot.Api.Data;
using Chatbot.Api.DTOs;
using Chatbot.Api.Services;
using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Options;

namespace Chatbot.Api.Tests;

public sealed class OpenRouterChatServiceTests
{
    [Fact]
    public async Task SendMessageAsync_SendsConfiguredModelAndAuth_AndReturnsReply()
    {
        await using var database = await TestDatabase.CreateAsync();

        HttpRequestMessage? capturedRequest = null;
        string? capturedBody = null;

        using var httpClient = new HttpClient(new StubHttpMessageHandler(async request =>
        {
            capturedRequest = request;
            capturedBody = request.Content is null ? null : await request.Content.ReadAsStringAsync();

            return new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = JsonContent.Create(new
                {
                    choices = new[]
                    {
                        new { message = new { role = "assistant", content = "Hi from the model." } }
                    }
                })
            };
        }))
        {
            BaseAddress = new Uri("https://openrouter.ai/api/v1/")
        };

        var service = CreateService(database.Context, httpClient);

        var response = await service.SendMessageAsync(
            new ChatRequest { Message = "Hello" },
            CancellationToken.None);

        Assert.Equal("Hi from the model.", response.Reply);
        Assert.NotEqual(Guid.Empty, response.MessageId);

        Assert.NotNull(capturedRequest);
        Assert.Equal("Bearer test-key", capturedRequest.Headers.Authorization?.ToString());
        Assert.Equal("https://openrouter.ai/api/v1/chat/completions", capturedRequest.RequestUri?.ToString());

        using var payload = JsonDocument.Parse(capturedBody!);
        Assert.Equal("stealth/crouton-alpha", payload.RootElement.GetProperty("model").GetString());

        var messages = payload.RootElement.GetProperty("messages");
        Assert.Equal(2, messages.GetArrayLength());
        Assert.Equal("system", messages[0].GetProperty("role").GetString());
        Assert.Equal("Be concise.", messages[0].GetProperty("content").GetString());
        Assert.Equal("user", messages[1].GetProperty("role").GetString());
        Assert.Equal("Hello", messages[1].GetProperty("content").GetString());
    }

    [Fact]
    public async Task SendMessageAsync_WhenProviderFails_ThrowsChatProviderException()
    {
        await using var database = await TestDatabase.CreateAsync();

        using var httpClient = new HttpClient(new StubHttpMessageHandler(_ =>
            Task.FromResult(new HttpResponseMessage(HttpStatusCode.Unauthorized)
            {
                Content = new StringContent("{\"error\":\"invalid key\"}")
            })))
        {
            BaseAddress = new Uri("https://openrouter.ai/api/v1/")
        };

        var service = CreateService(database.Context, httpClient);

        await Assert.ThrowsAsync<ChatProviderException>(() =>
            service.SendMessageAsync(new ChatRequest { Message = "Hello" }, CancellationToken.None));

        Assert.Empty(database.Context.Messages.Where(m => m.Role == "assistant"));
    }

    private static OpenRouterChatService CreateService(ChatbotDbContext db, HttpClient httpClient) =>
        new(
            db,
            httpClient,
            Options.Create(new OpenRouterOptions
            {
                ApiKey = "test-key",
                Model = "stealth/crouton-alpha",
                SystemPrompt = "Be concise.",
                MaxHistoryMessages = 20
            }),
            NullLogger<OpenRouterChatService>.Instance);

    private sealed class StubHttpMessageHandler(
        Func<HttpRequestMessage, Task<HttpResponseMessage>> responder) : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(
            HttpRequestMessage request,
            CancellationToken cancellationToken) => responder(request);
    }

    private sealed class TestDatabase : IAsyncDisposable
    {
        private readonly SqliteConnection _connection;

        private TestDatabase(SqliteConnection connection, ChatbotDbContext context)
        {
            _connection = connection;
            Context = context;
        }

        public ChatbotDbContext Context { get; }

        public static async Task<TestDatabase> CreateAsync()
        {
            var connection = new SqliteConnection("Data Source=:memory:");
            await connection.OpenAsync();

            var options = new DbContextOptionsBuilder<ChatbotDbContext>()
                .UseSqlite(connection)
                .Options;

            var context = new ChatbotDbContext(options);
            await context.Database.EnsureCreatedAsync();

            return new TestDatabase(connection, context);
        }

        public async ValueTask DisposeAsync()
        {
            await Context.DisposeAsync();
            await _connection.DisposeAsync();
        }
    }
}
