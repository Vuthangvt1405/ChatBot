# Chatbot API

A small ASP.NET Core Web API (.NET 10, controllers) for chat conversations, persisted with EF Core + SQLite and backed by [OpenRouter](https://openrouter.ai). Includes Swagger UI, a health check, a Dockerfile and xUnit tests.

## Layout

```
Chatbot.sln
├─ Chatbot.Api/            # Web API
│  ├─ Controllers/         # ChatController
│  ├─ DTOs/                # Request/response contracts
│  ├─ Models/              # EF entities (Conversation, Message)
│  ├─ Data/                # ChatbotDbContext
│  ├─ Services/            # IChatService, OpenRouterChatService, MockChatService
│  └─ Migrations/          # EF Core migrations
└─ Chatbot.Api.Tests/      # xUnit integration + unit tests
```

## Requirements

- .NET SDK 10.0.301+ (pinned in `global.json`)
- Docker (optional, for the container image)

## Run locally

```powershell
dotnet run --project Chatbot.Api
```

Defaults to `http://localhost:5008`:

- Chat page (Blazor Server): <http://localhost:5008/>
- Swagger UI: <http://localhost:5008/swagger>
- Health: <http://localhost:5008/health>
- Chat: `POST http://localhost:5008/api/chat`

On startup the app applies EF Core migrations and creates `chatbot.db` in the working directory.

### Configuration

| Key | Default | Notes |
|---|---|---|
| `ConnectionStrings:Chatbot` | `Data Source=chatbot.db` | Override with `ConnectionStrings__Chatbot` |
| `OpenRouter:BaseUrl` | `https://openrouter.ai/api/v1/` | |
| `OpenRouter:Model` | `stealth/crouton-alpha` | Any OpenRouter model id |
| `OpenRouter:SystemPrompt` | `You are a helpful, concise assistant.` | |
| `OpenRouter:MaxHistoryMessages` | `20` | Recent messages sent as context |
| `OpenRouter:ApiKey` | *empty* | **Secret** — see below |
| `OpenRouter:SiteUrl` / `AppName` | *empty* | Optional attribution headers |

If `OpenRouter:ApiKey` is empty, the API uses `MockChatService` (echoes your message) so the app and tests run without a key.

## API key (user secrets)

Never put the key in `appsettings*.json` or the Dockerfile. In development:

```powershell
dotnet user-secrets init --project Chatbot.Api      # already done
dotnet user-secrets set "OpenRouter:ApiKey" "sk-or-v1-..." --project Chatbot.Api
dotnet user-secrets list --project Chatbot.Api      # verify
```

Secrets live in `%APPDATA%\Microsoft\UserSecrets\<UserSecretsId>\secrets.json` and load only in the `Development` environment.

For Docker/production, pass it as an environment variable (double underscore nests config sections):

```powershell
docker run --rm -p 8080:8080 `
  -e OpenRouter__ApiKey="sk-or-v1-..." `
  -v chatbot-data:/app/data `
  chatbot-api
```

## Endpoints

### Send a message

```http
POST /api/chat
Content-Type: application/json

{ "message": "Hello!", "conversationId": null }
```

```json
{
  "conversationId": "3f6c9d2e-...",
  "messageId": "9a1b0c7d-...",
  "reply": "Hi! How can I help?",
  "createdAt": "2026-11-04T10:15:30.123+00:00"
}
```

Omit `conversationId` to start a new conversation; pass it on later calls to continue. Invalid input returns `400`, an unknown conversation returns `404`, and provider failures return `502` (ProblemDetails).

### Read history

```http
GET /api/chat/{conversationId}/messages
```

Returns the conversation with its ordered messages.

### Health

```http
GET /health
```

Plain-text `Healthy` while the process is up.

## Database migrations

`dotnet-ef` is a repo-local tool (`dotnet-tools.json`), so no global install is needed.

```powershell
dotnet tool restore
dotnet tool run dotnet-ef migrations add <Name> --project Chatbot.Api --output-dir Migrations
dotnet tool run dotnet-ef database update --project Chatbot.Api
```

## Tests

```powershell
dotnet test
```

Integration tests boot the API with a temporary SQLite file and the mock provider, so they never call OpenRouter. `OpenRouterChatServiceTests` uses a stub `HttpMessageHandler` to verify the request payload, auth header, reply parsing and failure handling.

## Docker

```powershell
docker build -t chatbot-api .
docker run --rm -p 8080:8080 `
  -e OpenRouter__ApiKey="sk-or-v1-..." `
  -v chatbot-data:/app/data `
  chatbot-api
```

The image runs as the non-root `app` user on port 8080 with the SQLite file at `/app/data/chatbot.db` (mount a volume to persist it).

> `stealth/crouton-alpha` is a temporary stealth model on OpenRouter; set `OpenRouter__Model` to a stable model id for anything long-lived.
