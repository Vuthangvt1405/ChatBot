# Chatbot API

A small chat app in Python: a [FastAPI](https://fastapi.tiangolo.com) API and a chat page (Jinja2 + HTMX), persisted with SQLAlchemy + SQLite (migrations by Alembic) and backed by [OpenRouter](https://openrouter.ai). Includes Swagger UI, a health check, a Dockerfile and pytest tests (API, service and Playwright browser tests).

## Layout

```
app/
├─ main.py          # create_app(): settings, DB, routers, error handlers
├─ config.py        # Settings (.env / environment)
├─ db.py            # engine, migrations on startup, session dependency
├─ errors.py        # exceptions + ProblemDetails error handling
├─ models.py        # SQLAlchemy models (Conversation, Message)
├─ schemas.py       # request/response models (camelCase JSON)
├─ routers/         # api.py (/api/chat), pages.py (chat page + /ui fragments), health.py
├─ services/        # ChatServiceBase (persistence) + OpenRouterChatService
├─ templates/       # index.html and message fragments
└─ static/          # chat.js, chat.css, htmx.min.js
migrations/         # Alembic migrations
tests/              # pytest: API, OpenRouter service, page fragments; e2e/ = Playwright
```

## Requirements

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Docker (optional, for the container image)

## Run locally

```powershell
uv sync
copy .env.example .env      # then set OPENROUTER__API_KEY in .env
uv run uvicorn app.main:app --reload --port 5008
```

- Chat page: <http://localhost:5008/>
- Swagger UI: <http://localhost:5008/swagger>
- Health: <http://localhost:5008/health>
- Chat: `POST http://localhost:5008/api/chat`

On startup the app applies the Alembic migrations and creates `chatbot.db` in the working directory. Start the server from the project root: `.env` is read from the current folder.

### Configuration

Set in `.env` or as environment variables. Nested keys use a double underscore.

| Key | Default | Notes |
|---|---|---|
| `OPENROUTER__API_KEY` | *empty* | **Secret, required.** The app stops at startup with a clear error if it is missing |
| `OPENROUTER__MODEL` | `stealth/crouton-alpha` | Any OpenRouter model id |
| `OPENROUTER__SUPPORTED_MODELS` | *empty* | JSON list of models an Agent Studio agent may use, e.g. `["openai/gpt-4o-mini"]`. The default model is always added, so by default it's the only choice |
| `OPENROUTER__BASE_URL` | `https://openrouter.ai/api/v1/` | |
| `OPENROUTER__SYSTEM_PROMPT` | `You are a helpful, concise assistant.` | |
| `OPENROUTER__MAX_HISTORY_MESSAGES` | `20` | Recent messages sent as context |
| `OPENROUTER__SITE_URL` / `OPENROUTER__APP_NAME` | *empty* | Optional attribution headers |
| `DATABASE_URL` | `sqlite+aiosqlite:///chatbot.db` | |
| `DEBUG` | `false` | FastAPI debug mode. `/api/*` still never returns a stack trace |

Never put the key in code, `.env.example` or the Dockerfile. `.env` is gitignored. Tests don't need a key; they use a test-only `EchoChatService` ([tests/echo.py](tests/echo.py)).

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
  "createdAt": "2026-11-04T10:15:30.123000Z"
}
```

Omit `conversationId` to start a new conversation; pass it on later calls to continue. Errors are ProblemDetails JSON (`application/problem+json`):

| Status | When |
|---|---|
| `400` | Empty, blank or longer than 4000 characters |
| `404` | Unknown `conversationId` |
| `502` | OpenRouter failed: rejected, timed out, unreachable or unreadable |
| `500` | Anything else, with the fixed detail "Something went wrong. Please try again." |

A failed send stores nothing, so a retry never saves the message twice.

### Read history

```http
GET /api/chat/{conversationId}/messages
```

Returns the conversation with its ordered messages, or `404`.

### Agent Studio

```http
GET  /api/agents                    # saved agents, by name
POST /api/agents                    # create  { name, systemPrompt, modelId, enabledTools, thinkingLevel }
GET  /api/agents/{agentId}
PUT  /api/agents/{agentId}          # replace the editable fields; the last save wins
GET  /api/agent-studio/options      # presets, supported models, tools, thinking levels, limits
```

`POST /api/chat` also takes an optional `agentId`: that agent's instructions, model and thinking level answer the message. An unknown `agentId` is `404` and nothing is saved. Design: [plan](docs/features/plans/ai-data-studio/STORY-01-agent-studio-plan.md).

### Health

```http
GET /health
```

Plain-text `Healthy` while the process is up.

[chatbot.http](chatbot.http) has these requests ready to send from VS Code (REST Client extension).

## Database migrations

```powershell
uv run alembic revision --autogenerate -m "<name>"
uv run alembic upgrade head
```

The CLI uses `DATABASE_URL` from `.env`. The app runs `upgrade head` itself on startup.

## Tests

```powershell
uv run playwright install chromium   # once, for the browser tests
uv run pytest
uv run ruff check . ; uv run ruff format --check .
```

API tests boot the app with a temporary SQLite file and the echo provider, so they never call OpenRouter. `test_openrouter.py` mocks OpenRouter with `respx` to check the payload, auth header, reply parsing and failure handling. `tests/e2e/` drives the chat page in Chromium with a controllable fake chat service; those tests always run last.

## Docker

```powershell
docker build -t chatbot-api .
docker run --rm -p 127.0.0.1:8080:8080 `
  -e OPENROUTER__API_KEY="sk-or-v1-..." `
  -v chatbot-data:/app/data `
  chatbot-api
```

The image runs as the non-root `app` user on port 8080 with the SQLite file at `/app/data/chatbot.db` (mount a volume to persist it). `127.0.0.1:` keeps the app reachable from this machine only; the app has no sign-in.

> `stealth/crouton-alpha` is a temporary stealth model on OpenRouter; set `OPENROUTER__MODEL` to a stable model id for anything long-lived.
