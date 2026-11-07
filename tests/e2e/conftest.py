"""Browser tests: a live uvicorn server plus a controllable fake chat service, via Playwright."""

import asyncio
import json
import socket
import threading
import time
import uuid
from collections import deque
from collections.abc import Callable, Iterator
from concurrent.futures import Future
from datetime import UTC, datetime, timedelta

import pytest
import uvicorn
from fastapi import FastAPI
from playwright.sync_api import Page, expect

from app.main import create_app
from app.schemas import ChatRequest, ChatResponse, ConversationOut, MessageOut
from app.services import get_chat_service
from tests.conftest import make_settings


class FakeChatService:
    """Records calls. Set `pending` / `pending_conversation` to a Future to hold a request open.

    A `pending` Future that holds an exception makes the send fail with it (US-6).
    """

    def __init__(self) -> None:
        self.requests: list[ChatRequest] = []
        self.replies: deque[str] = deque()
        self.pending: Future[str] | None = None
        self.conversation_ids: deque[uuid.UUID] = deque()

        # US-5 restore setup.
        self.conversations: dict[uuid.UUID, ConversationOut] = {}
        self.pending_conversation: Future[ConversationOut | None] | None = None
        self.throw_on_get = False
        self.get_requests: list[uuid.UUID] = []

    async def send_message(self, request: ChatRequest) -> ChatResponse:
        self.requests.append(request)
        if self.pending is not None:
            reply = await asyncio.wrap_future(self.pending)
        else:
            reply = self.replies.popleft()
        if self.conversation_ids:
            conversation_id = self.conversation_ids.popleft()
        else:
            conversation_id = request.conversation_id or uuid.uuid4()
        return ChatResponse(
            conversation_id=conversation_id,
            message_id=uuid.uuid4(),
            reply=reply,
            created_at=datetime.now(UTC),
        )

    async def get_conversation(self, conversation_id: uuid.UUID) -> ConversationOut | None:
        self.get_requests.append(conversation_id)
        if self.throw_on_get:
            raise RuntimeError("db down")
        if self.pending_conversation is not None:
            return await asyncio.wrap_future(self.pending_conversation)
        return self.conversations.get(conversation_id)

    def fail(self, error: Exception) -> None:
        """US-6: the next sends fail with `error`."""
        failed: Future[str] = Future()
        failed.set_exception(error)
        self.pending = failed

    def succeed(self, reply: str) -> None:
        """US-6: the next send succeeds with `reply`."""
        self.pending = None
        self.replies.append(reply)

    def release(self) -> None:
        """Let any held request finish so the server can shut down cleanly."""
        if self.pending is not None and not self.pending.done():
            self.pending.set_result("released")
        if self.pending_conversation is not None and not self.pending_conversation.done():
            self.pending_conversation.set_result(None)


def convo(conversation_id: uuid.UUID, *messages: tuple[str, str]) -> ConversationOut:
    now = datetime.now(UTC)
    return ConversationOut(
        id=conversation_id,
        title="title",
        created_at=now,
        messages=[
            MessageOut(
                id=uuid.uuid4(), role=role, content=text, created_at=now + timedelta(seconds=i)
            )
            for i, (role, text) in enumerate(messages)
        ],
    )


def eventually(predicate: Callable[[], bool], timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() > deadline:
            raise AssertionError("condition was not met in time")
        time.sleep(0.02)


class ChatPage:
    """Page object for the chat page, mirroring the helpers in the old bUnit tests."""

    STORE_KEY = "chatbot.conversationId"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.input = page.locator("#chat-input")
        self.send_button = page.locator("button[aria-label=Send]")
        self.typing = page.locator("#typing-indicator")
        self.restore_indicator = page.locator("#restore-indicator")
        self.empty = page.locator(".empty")
        self.error = page.locator("#chat-error")
        self.hint = page.locator(".hint")
        self.counter = page.locator("#char-count")
        self.items = page.locator("#messages li")
        # US-6: the error shown after a failed send, and its "Start a new chat" button.
        self.send_error = page.locator("#send-error")
        self.send_error_text = page.locator("#send-error .text")
        self.send_error_new_chat = page.locator("#send-error-new-chat")
        # US-7: the sidebar button.
        self.new_chat = page.locator("#new-chat")
        self.send_requests: list[str] = []
        page.on("request", self._on_request)

    def _on_request(self, request) -> None:
        if "/ui/send" in request.url:
            self.send_requests.append(request.url)

    def open(self, saved_id: str | None = None) -> "ChatPage":
        if saved_id is not None:
            self.page.add_init_script(
                f"localStorage.setItem({json.dumps(self.STORE_KEY)}, {json.dumps(saved_id)})"
            )
        self.page.goto("/")
        return self

    def type(self, text: str) -> None:
        self.input.fill(text)

    def submit(self) -> None:
        """Submits the form directly, even when the Send button is disabled."""
        self.page.evaluate("document.getElementById('chat-form').requestSubmit()")

    def enter(self, shift: bool = False) -> None:
        self.input.press("Shift+Enter" if shift else "Enter")

    def send(self, text: str) -> None:
        """Types and submits, then waits for the round trip to finish."""
        self.type(text)
        with self.page.expect_response("**/ui/send"):
            self.submit()
        expect(self.typing).to_be_hidden()

    def assert_nothing_sent(self) -> None:
        self.page.wait_for_timeout(200)
        assert self.send_requests == []

    def messages(self) -> list[tuple[str, str, str]]:
        # The US-6 error isn't a message (no label), so it's left out here.
        rows = self.page.locator("#messages li:not(#send-error)").evaluate_all(
            # htmx-* classes are HTMX's short-lived swap/settle markers, not page styling.
            """lis => lis.map(li => [
                [...li.classList].filter(c => !c.startsWith('htmx-')).join(' '),
                li.querySelector('.label').textContent,
                li.querySelector('.text').textContent])"""
        )
        return [tuple(row) for row in rows]

    def texts(self) -> list[str]:
        return [text for _, _, text in self.messages()]

    def stored_id(self) -> str | None:
        return self.page.evaluate(f"localStorage.getItem({json.dumps(self.STORE_KEY)})")

    def scrolled_to_bottom(self) -> bool:
        return self.page.evaluate(
            """() => { const s = document.getElementById('chat-scroll');
                       return s.scrollHeight > s.clientHeight
                           && s.scrollHeight - s.scrollTop - s.clientHeight <= 1; }"""
        )


@pytest.fixture(scope="session")
def live_app(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[FastAPI, str]]:
    app = create_app(make_settings(tmp_path_factory.mktemp("e2e") / "e2e.db"))

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    eventually(lambda: server.started, timeout=15)

    yield app, f"http://127.0.0.1:{port}"

    server.should_exit = True
    thread.join(timeout=10)


@pytest.fixture(scope="session")
def base_url(live_app: tuple[FastAPI, str]) -> str:
    return live_app[1]


@pytest.fixture
def chat(live_app: tuple[FastAPI, str]) -> Iterator[FakeChatService]:
    app, _ = live_app
    fake = FakeChatService()
    app.dependency_overrides[get_chat_service] = lambda: fake
    yield fake
    fake.release()
    app.dependency_overrides.pop(get_chat_service, None)


@pytest.fixture
def chat_page(page: Page, chat: FakeChatService) -> ChatPage:
    page.set_default_timeout(5000)
    expect.set_options(timeout=5000)
    return ChatPage(page)
