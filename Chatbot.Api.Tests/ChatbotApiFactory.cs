using Chatbot.Api.Data;
using Chatbot.Api.Services;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;

namespace Chatbot.Api.Tests;

/// <summary>
/// Boots the API with a throwaway SQLite file and the mock provider, so tests never touch OpenRouter.
/// </summary>
public sealed class ChatbotApiFactory : WebApplicationFactory<Program>
{
    private readonly string _databasePath =
        Path.Combine(Path.GetTempPath(), $"chatbot-tests-{Guid.NewGuid():N}.db");

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.UseEnvironment("Testing");

        builder.ConfigureServices(services =>
        {
            services.RemoveAll<DbContextOptions<ChatbotDbContext>>();
            services.RemoveAll<ChatbotDbContext>();
            services.AddDbContext<ChatbotDbContext>(options =>
                options.UseSqlite($"Data Source={_databasePath}"));

            services.RemoveAll<IChatService>();
            services.AddScoped<IChatService, MockChatService>();
        });
    }

    protected override void Dispose(bool disposing)
    {
        base.Dispose(disposing);

        if (!disposing)
        {
            return;
        }

        SqliteConnection.ClearAllPools();

        if (File.Exists(_databasePath))
        {
            File.Delete(_databasePath);
        }
    }
}
