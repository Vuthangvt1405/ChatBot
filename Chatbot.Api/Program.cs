using System.Reflection;
using Chatbot.Api.Components;
using Chatbot.Api.Data;
using Chatbot.Api.Services;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;
using Microsoft.OpenApi;
using Radzen;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddControllers();
builder.Services.AddRazorComponents().AddInteractiveServerComponents();
builder.Services.AddRadzenComponents();

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new OpenApiInfo
    {
        Title = "Chatbot API",
        Version = "v1",
        Description = "A small chat API with persisted conversations, backed by OpenRouter."
    });

    var xmlFile = $"{Assembly.GetExecutingAssembly().GetName().Name}.xml";
    var xmlPath = Path.Combine(AppContext.BaseDirectory, xmlFile);

    if (File.Exists(xmlPath))
    {
        options.IncludeXmlComments(xmlPath);
    }
});

var connectionString = builder.Configuration.GetConnectionString("Chatbot")
    ?? "Data Source=chatbot.db";

builder.Services.AddDbContext<ChatbotDbContext>(options => options.UseSqlite(connectionString));

builder.Services.AddOptions<OpenRouterOptions>()
    .Bind(builder.Configuration.GetSection(OpenRouterOptions.SectionName))
    .Validate(
        o => !string.IsNullOrWhiteSpace(o.BaseUrl) && !string.IsNullOrWhiteSpace(o.Model),
        "OpenRouter:BaseUrl and OpenRouter:Model are required.")
    .ValidateOnStart();

var openRouterApiKey = builder.Configuration[$"{OpenRouterOptions.SectionName}:ApiKey"];

if (string.IsNullOrWhiteSpace(openRouterApiKey))
{
    // No key configured (tests, fresh clone): fall back to a local echo provider.
    builder.Services.AddScoped<IChatService, MockChatService>();
}
else
{
    builder.Services.AddHttpClient<IChatService, OpenRouterChatService>((sp, client) =>
    {
        var options = sp.GetRequiredService<IOptions<OpenRouterOptions>>().Value;

        client.BaseAddress = new Uri(options.BaseUrl.TrimEnd('/') + "/");
        client.Timeout = TimeSpan.FromSeconds(60);
    });
}

builder.Services.AddHealthChecks();

var app = builder.Build();

using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<ChatbotDbContext>();
    db.Database.Migrate();
}

app.UseSwagger();
app.UseSwaggerUI();

app.UseAntiforgery();

app.MapStaticAssets();
app.MapControllers();
app.MapRazorComponents<App>().AddInteractiveServerRenderMode();
app.MapHealthChecks("/health");

app.Run();

public partial class Program { }
