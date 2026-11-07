import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import MissingApiKeyError, OpenRouterSettings
from app.errors import ChatProviderError
from app.main import create_app
from app.schemas import ChatRequest, ChatResponse, ConversationOut
from app.services import get_chat_service
from tests.conftest import make_settings


def post_chat(client: TestClient, body: dict) -> dict:
    response = client.post("/api/chat", json=body)
    assert response.status_code == 200, response.text
    return response.json()


def test_health_returns_healthy(client: TestClient):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.text == "Healthy"


def test_root_serves_chat_page(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'id="chat-form"' in response.text


def test_swagger_is_served(client: TestClient):
    assert client.get("/swagger").status_code == 200


def test_api_routes_are_not_replaced_by_chat_page(client: TestClient):
    response = client.get(f"/api/chat/{uuid.uuid4()}/messages")

    assert response.status_code == 404
    assert not response.headers["content-type"].startswith("text/html")


def test_send_message_starts_conversation_and_returns_reply(client: TestClient):
    chat = post_chat(client, {"message": "Hello there"})

    assert uuid.UUID(chat["conversationId"]) != uuid.UUID(int=0)
    assert uuid.UUID(chat["messageId"]) != uuid.UUID(int=0)
    assert "Hello there" in chat["reply"]
    assert "[echo]" in chat["reply"]
    assert chat["createdAt"]


def test_send_message_continues_conversation_and_persists_history(client: TestClient):
    first = post_chat(client, {"message": "First message"})
    second = post_chat(
        client, {"conversationId": first["conversationId"], "message": "Second message"}
    )

    assert second["conversationId"] == first["conversationId"]

    history = client.get(f"/api/chat/{first['conversationId']}/messages")
    assert history.status_code == 200

    conversation = history.json()
    assert conversation["id"] == first["conversationId"]
    assert conversation["title"] == "First message"
    roles = [m["role"] for m in conversation["messages"]]
    assert roles == ["user", "assistant", "user", "assistant"]
    assert conversation["messages"][0]["content"] == "First message"
    assert conversation["messages"][2]["content"] == "Second message"


def test_send_message_with_empty_message_returns_400(client: TestClient):
    response = client.post("/api/chat", json={"message": ""})

    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"


def test_send_message_with_whitespace_message_returns_400(client: TestClient):
    response = client.post("/api/chat", json={"message": "   "})

    assert response.status_code == 400


def test_send_message_without_message_returns_400(client: TestClient):
    response = client.post("/api/chat", json={})

    assert response.status_code == 400


def test_send_message_with_malformed_json_returns_400(client: TestClient):
    response = client.post(
        "/api/chat", content="{not json", headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 400


# US-3 BR-2: the API and the chat page share MAX_MESSAGE_LENGTH (4000).
def test_send_message_with_4000_chars_returns_200(client: TestClient):
    response = client.post("/api/chat", json={"message": "a" * 4000})

    assert response.status_code == 200


def test_send_message_with_4001_chars_returns_400(client: TestClient):
    response = client.post("/api/chat", json={"message": "a" * 4001})

    assert response.status_code == 400
    # The rejected text is not echoed back.
    assert "a" * 100 not in response.text


def test_send_message_with_unknown_conversation_returns_404(client: TestClient):
    response = client.post(
        "/api/chat",
        json={"conversationId": str(uuid.uuid4()), "message": "Does this conversation exist?"},
    )

    assert response.status_code == 404
    assert response.json()["title"] == "Conversation not found"


def test_get_messages_with_unknown_conversation_returns_404(client: TestClient):
    response = client.get(f"/api/chat/{uuid.uuid4()}/messages")

    assert response.status_code == 404


def test_long_message_title_is_truncated(client: TestClient):
    chat = post_chat(client, {"message": "x" * 100})

    title = client.get(f"/api/chat/{chat['conversationId']}/messages").json()["title"]

    assert title == "x" * 60 + "…"


def test_startup_without_api_key_fails_with_clear_error(tmp_path: Path):
    settings = make_settings(tmp_path / "no-key.db", openrouter=OpenRouterSettings(api_key=" "))
    app = create_app(settings)

    with pytest.raises(MissingApiKeyError, match="OPENROUTER__API_KEY"), TestClient(app):
        pass


# ---------- US-6 Clear feedback on failure ----------
# Plan: docs/features/plans/US-6-error-feedback-plan.md §7

# Group 9 - API errors are safe ProblemDetails (AC-11, SEC2)
# Baseline: the chat service is replaced by one that always raises.


class ThrowingChatService:
    def __init__(self, error: Exception) -> None:
        self.error = error

    async def send_message(self, request: ChatRequest) -> ChatResponse:
        raise self.error

    async def get_conversation(self, conversation_id: uuid.UUID) -> ConversationOut | None:
        raise self.error


@pytest.fixture
def client_that_throws(tmp_path: Path):
    """Builds a client whose chat service raises `error`; `debug` turns on FastAPI debug mode."""
    clients: list[TestClient] = []

    def build(error: Exception, debug: bool = False) -> TestClient:
        app = create_app(make_settings(tmp_path / f"throws-{len(clients)}.db", debug=debug))
        app.dependency_overrides[get_chat_service] = lambda: ThrowingChatService(error)
        client = TestClient(app)
        client.__enter__()
        clients.append(client)
        return client

    yield build

    for client in clients:
        client.__exit__(None, None, None)


def problem_body(response) -> dict:
    assert response.headers["content-type"] == "application/problem+json"
    return response.json()


def test_us6_ac11_unexpected_error_returns_500_problem_details(client_that_throws):
    client = client_that_throws(RuntimeError("secret-detail"))

    response = client.post("/api/chat", json={"message": "Hello"})

    assert response.status_code == 500
    problem = problem_body(response)
    assert problem["status"] == 500
    assert problem["title"] == "Unexpected error"
    assert problem["detail"] == "Something went wrong. Please try again."


def test_us6_ac11_get_messages_unexpected_error_returns_500_problem_details(client_that_throws):
    client = client_that_throws(RuntimeError("secret-detail"))

    response = client.get(f"/api/chat/{uuid.uuid4()}/messages")

    assert response.status_code == 500
    assert problem_body(response)["detail"] == "Something went wrong. Please try again."


def test_us6_ac11_provider_error_returns_502_problem_details(client_that_throws):
    client = client_that_throws(ChatProviderError("The chat provider did not respond in time."))

    response = client.post("/api/chat", json={"message": "Hello"})

    assert response.status_code == 502
    problem = problem_body(response)
    assert problem["title"] == "Chat provider error"
    assert problem["detail"] == "The chat provider did not respond in time."


def test_us6_ac11_not_found_returns_404_problem_details(client: TestClient):
    conversation_id = uuid.uuid4()

    response = client.post(
        "/api/chat", json={"conversationId": str(conversation_id), "message": "Hello"}
    )

    assert response.status_code == 404
    problem = problem_body(response)
    assert problem["title"] == "Conversation not found"
    assert problem["detail"] == f"Conversation '{conversation_id}' was not found."


def test_us6_sec2_unexpected_error_no_exception_text_or_stack_trace(client_that_throws):
    client = client_that_throws(RuntimeError("secret-detail"))

    response = client.post("/api/chat", json={"message": "Hello"})

    assert response.status_code == 500
    assert "secret-detail" not in response.text
    assert "RuntimeError" not in response.text
    assert "Traceback" not in response.text


def test_us6_sec2_debug_mode_unexpected_error_still_problem_details(client_that_throws):
    # Debug mode would normally answer with a traceback page.
    client = client_that_throws(RuntimeError("secret-detail"), debug=True)

    response = client.post("/api/chat", json={"message": "Hello"})

    assert response.status_code == 500
    problem = problem_body(response)
    assert problem["detail"] == "Something went wrong. Please try again."
    assert "secret-detail" not in response.text
