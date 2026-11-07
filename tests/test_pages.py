"""The HTML fragments HTMX swaps into the chat page."""

import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.errors import ChatProviderError, ConversationNotFoundError
from app.services import get_chat_service


def test_send_fragment_returns_reply_as_text_with_conversation_header(client: TestClient):
    response = client.post("/ui/send", data={"message": "<b>x</b>"})

    assert response.status_code == 200
    assert '<li class="message assistant">' in response.text
    assert "&lt;b&gt;x&lt;/b&gt;" in response.text
    assert "<b>" not in response.text
    uuid.UUID(response.headers["X-Conversation-Id"])


def test_send_fragment_rejects_blank_and_too_long_messages(client: TestClient):
    assert client.post("/ui/send", data={"message": "   "}).status_code == 400
    assert client.post("/ui/send", data={"message": "a" * 4001}).status_code == 400


# US-6: the page picks its message from the status code; the body is always empty (BR-1).


def test_send_fragment_with_unknown_conversation_returns_404_without_details(
    client: TestClient,
):
    conversation_id = str(uuid.uuid4())

    response = client.post(
        "/ui/send", data={"message": "Hello", "conversation_id": conversation_id}
    )

    assert response.status_code == 404
    assert response.text == ""


class FailingChatService:
    def __init__(self, error: Exception) -> None:
        self.error = error

    async def send_message(self, request):
        raise self.error

    async def get_conversation(self, conversation_id):
        raise self.error


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (ChatProviderError("secret-detail"), 502),
        (ConversationNotFoundError(uuid.UUID(int=1)), 404),
        (RuntimeError("secret-detail"), 500),
    ],
)
def test_send_fragment_failure_maps_to_status_with_empty_body(
    app: FastAPI, client: TestClient, error: Exception, status: int
):
    app.dependency_overrides[get_chat_service] = lambda: FailingChatService(error)

    response = client.post("/ui/send", data={"message": "Hello"})

    assert response.status_code == status
    assert response.text == ""
    assert "X-Conversation-Id" not in response.headers


def test_history_fragment_lists_messages_in_order(client: TestClient):
    first = client.post("/ui/send", data={"message": "Hi"})
    conversation_id = first.headers["X-Conversation-Id"]

    response = client.get(f"/ui/conversations/{conversation_id}")

    assert response.status_code == 200
    assert response.text.count("<li ") == 2
    assert response.text.index("message user") < response.text.index("message assistant")


def test_history_fragment_for_unknown_conversation_returns_404(client: TestClient):
    assert client.get(f"/ui/conversations/{uuid.uuid4()}").status_code == 404


def test_history_fragment_failure_returns_500_without_details(app: FastAPI, client: TestClient):
    app.dependency_overrides[get_chat_service] = lambda: FailingChatService(
        RuntimeError("secret-detail")
    )

    response = client.get(f"/ui/conversations/{uuid.uuid4()}")

    assert response.status_code == 500
    assert response.text == ""
