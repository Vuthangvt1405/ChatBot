import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import OpenRouterSettings
from app.errors import ChatProviderError
from app.models import Base, Conversation, Message
from app.schemas import ChatRequest
from app.services.openrouter import OpenRouterChatService, create_http_client

BASE_URL = "https://openrouter.ai/api/v1/"
COMPLETIONS = f"{BASE_URL}chat/completions"
SETTINGS = OpenRouterSettings(
    api_key="test-key",
    base_url=BASE_URL,
    model="stealth/crouton-alpha",
    system_prompt="Be concise.",
    max_history_messages=20,
)


def reply_with(content: str) -> httpx.Response:
    return httpx.Response(
        200, json={"choices": [{"message": {"role": "assistant", "content": content}}]}
    )


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as db:
        yield db
    await engine.dispose()


@pytest.fixture
async def http() -> AsyncIterator[httpx.AsyncClient]:
    async with create_http_client(SETTINGS) as client:
        yield client


@pytest.fixture
def service(session: AsyncSession, http: httpx.AsyncClient) -> OpenRouterChatService:
    return OpenRouterChatService(session, http, SETTINGS)


async def count(session: AsyncSession, model, *where) -> int:
    return await session.scalar(select(func.count()).select_from(model).where(*where))


async def seed_conversation(session: AsyncSession) -> uuid.UUID:
    now = datetime.now(UTC)
    conversation = Conversation(title="Seeded")
    session.add(conversation)
    session.add_all(
        [
            Message(
                conversation_id=conversation.id,
                role="user",
                content="Hi",
                created_at=now - timedelta(minutes=2),
            ),
            Message(
                conversation_id=conversation.id,
                role="assistant",
                content="Hello!",
                created_at=now - timedelta(minutes=1),
            ),
        ]
    )
    await session.commit()
    session.expunge_all()
    return conversation.id


@respx.mock
async def test_send_message_sends_configured_model_and_auth_and_returns_reply(service):
    route = respx.post(COMPLETIONS).mock(return_value=reply_with("Hi from the model."))

    response = await service.send_message(ChatRequest(message="Hello"))

    assert response.reply == "Hi from the model."
    assert response.message_id is not None

    request = route.calls.last.request
    assert request.headers["Authorization"] == "Bearer test-key"
    assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"

    payload = json.loads(request.content)
    assert payload["model"] == "stealth/crouton-alpha"
    assert payload["messages"] == [
        {"role": "system", "content": "Be concise."},
        {"role": "user", "content": "Hello"},
    ]


@respx.mock
async def test_send_message_when_provider_fails_raises_chat_provider_error(service, session):
    respx.post(COMPLETIONS).respond(401, json={"error": "invalid key"})

    with pytest.raises(ChatProviderError, match="rejected the request"):
        await service.send_message(ChatRequest(message="Hello"))

    assert await count(session, Message, Message.role == "assistant") == 0


@respx.mock
async def test_send_message_with_empty_completion_raises_chat_provider_error(service):
    respx.post(COMPLETIONS).respond(200, json={"choices": []})

    with pytest.raises(ChatProviderError, match="empty response"):
        await service.send_message(ChatRequest(message="Hello"))


@respx.mock
async def test_send_message_sends_only_recent_history_and_attribution_headers(session, http):
    route = respx.post(COMPLETIONS).mock(return_value=reply_with("ok"))
    settings = SETTINGS.model_copy(
        update={"max_history_messages": 2, "site_url": "https://example.test", "app_name": "Bot"}
    )
    service = OpenRouterChatService(session, http, settings)

    first = await service.send_message(ChatRequest(message="one"))
    await service.send_message(ChatRequest(message="two", conversation_id=first.conversation_id))

    request = route.calls.last.request
    sent = json.loads(request.content)["messages"]
    assert [m["content"] for m in sent] == ["Be concise.", "ok", "two"]
    assert request.headers["HTTP-Referer"] == "https://example.test"
    assert request.headers["X-Title"] == "Bot"


# ---------- US-6 Clear feedback on failure ----------
# Plan: docs/features/plans/US-6-error-feedback-plan.md §7

# Group 6 - a failed send isn't saved (AC-7, SEC4)
# Baseline: the provider returns 500.


@respx.mock
async def test_us6_ac7_provider_fails_new_conversation_nothing_saved(service, session):
    respx.post(COMPLETIONS).respond(500, text="oops")

    with pytest.raises(ChatProviderError):
        await service.send_message(ChatRequest(message="Hello"))

    assert await count(session, Conversation) == 0
    assert await count(session, Message) == 0


@respx.mock
async def test_us6_ac7_provider_fails_existing_conversation_history_unchanged(service, session):
    conversation_id = await seed_conversation(session)
    respx.post(COMPLETIONS).respond(500, text="oops")

    with pytest.raises(ChatProviderError):
        await service.send_message(ChatRequest(message="Hello", conversation_id=conversation_id))

    assert await count(session, Message, Message.conversation_id == conversation_id) == 2


@respx.mock
async def test_us6_ac7_retry_after_failure_saves_one_user_message(service, session):
    respx.post(COMPLETIONS).mock(side_effect=[httpx.Response(500, text="oops"), reply_with("Hi")])

    with pytest.raises(ChatProviderError):
        await service.send_message(ChatRequest(message="Hello"))
    await service.send_message(ChatRequest(message="Hello"))

    assert await count(session, Conversation) == 1
    assert await count(session, Message, Message.role == "user") == 1
    assert await count(session, Message, Message.role == "assistant") == 1


@respx.mock
async def test_us6_ac7_success_sends_new_message_to_provider(service, session):
    conversation_id = await seed_conversation(session)
    route = respx.post(COMPLETIONS).mock(return_value=reply_with("Sure"))

    await service.send_message(ChatRequest(message="New question", conversation_id=conversation_id))

    sent = json.loads(route.calls.last.request.content)["messages"]
    assert [m["role"] for m in sent] == ["system", "user", "assistant", "user"]
    assert sent[-1]["content"] == "New question"
    assert await count(session, Message, Message.conversation_id == conversation_id) == 4


# Group 7 - provider errors become "unavailable" (AC-8, SEC2)


@respx.mock
async def test_us6_ac8_provider_unreachable_raises_chat_provider_error(service):
    respx.post(COMPLETIONS).mock(side_effect=httpx.ConnectError("No such host is known."))

    with pytest.raises(ChatProviderError) as error:
        await service.send_message(ChatRequest(message="Hello"))

    assert str(error.value) == "The chat provider could not be reached."


@respx.mock
async def test_us6_ac8_provider_timeout_raises_chat_provider_error(service):
    respx.post(COMPLETIONS).mock(side_effect=httpx.ReadTimeout("timed out"))

    with pytest.raises(ChatProviderError) as error:
        await service.send_message(ChatRequest(message="Hello"))

    assert str(error.value) == "The chat provider did not respond in time."


@respx.mock
async def test_us6_ac8_provider_invalid_json_raises_chat_provider_error(service):
    respx.post(COMPLETIONS).respond(
        200, content=b"not json", headers={"Content-Type": "application/json"}
    )

    with pytest.raises(ChatProviderError) as error:
        await service.send_message(ChatRequest(message="Hello"))

    assert str(error.value) == "The chat provider returned an unreadable response."


@respx.mock
async def test_us6_ac8_contrast_cancelled_not_wrapped(service):
    # A real cancel isn't reported as an outage.
    def cancelled(request: httpx.Request) -> httpx.Response:
        raise asyncio.CancelledError()

    respx.post(COMPLETIONS).mock(side_effect=cancelled)

    with pytest.raises(asyncio.CancelledError):
        await service.send_message(ChatRequest(message="Hello"))
