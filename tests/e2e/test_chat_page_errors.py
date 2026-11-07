"""US-6 Clear feedback on failure, on the chat page.

Plan: docs/features/plans/US-6-error-feedback-plan.md §7
Baseline: the next send fails with an error (chat.fail), then send "Hello".
"""

from concurrent.futures import Future

from playwright.sync_api import expect

from app.errors import ChatProviderError, ConversationNotFoundError
from tests.e2e.conftest import ChatPage, FakeChatService, eventually
from tests.e2e.test_chat_page import ABC, TOO_LONG, finish, start_pending, try_send_all_ways

UNAVAILABLE_TEXT = "The assistant is unavailable right now. Please try again."
NOT_FOUND_TEXT = "This conversation no longer exists."
UNEXPECTED_TEXT = "Something went wrong. Please try again."
OFFLINE_TEXT = "Can't reach the server. Check your connection and try again."


def resubmit(chat_page: ChatPage) -> None:
    """Presses Send again with whatever is in the input, and waits for the round trip."""
    with chat_page.page.expect_response("**/ui/send"):
        chat_page.submit()
    finish(chat_page)


def start_in_gone_conversation(chat_page: ChatPage, chat: FakeChatService) -> None:
    """G2 baseline: conversation ABC is active, then sending "Hello" gets "not found"."""
    chat.succeed("Hi")
    chat.conversation_ids.append(ABC)
    chat_page.open()
    chat_page.send("First")

    chat.fail(ConversationNotFoundError(ABC))
    chat_page.send("Hello")


def start_with_error(chat_page: ChatPage, chat: FakeChatService) -> None:
    chat.fail(ChatProviderError("boom"))
    chat_page.open()
    chat_page.send("Hello")
    expect(chat_page.send_error).to_be_visible()


# Group 1 - right message per failure (AC-1, AC-3, AC-10)


def test_us6_ac1_provider_error_shows_unavailable_message(chat_page, chat):
    chat.fail(ChatProviderError("boom"))
    chat_page.open()

    chat_page.send("Hello")

    expect(chat_page.send_error).to_have_attribute("role", "alert")
    expect(chat_page.send_error_text).to_have_text(UNAVAILABLE_TEXT)


def test_us6_ac10_unexpected_error_shows_something_went_wrong(chat_page, chat):
    chat.fail(RuntimeError("db down"))
    chat_page.open()

    chat_page.send("Hello")

    expect(chat_page.send_error_text).to_have_text(UNEXPECTED_TEXT)


def test_us6_ac3_server_unreachable_shows_cant_reach_server(chat_page, chat):
    chat_page.open()
    chat_page.page.route("**/ui/send", lambda route: route.abort())
    chat_page.type("Hello")

    chat_page.submit()

    expect(chat_page.send_error_text).to_have_text(OFFLINE_TEXT)
    finish(chat_page)
    expect(chat_page.input).to_have_value("Hello")
    expect(chat_page.page.locator("#messages li.user.failed")).to_have_count(1)
    assert chat.requests == []


def test_us6_ac1_contrast_success_no_error(chat_page, chat):
    chat.succeed("Hi")
    chat_page.open()

    chat_page.send("Hello")

    expect(chat_page.page.locator("#messages li.assistant")).to_have_count(1)
    expect(chat_page.send_error).to_have_count(0)


def test_us6_ac1_contrast_too_long_no_send_error(chat_page, chat):
    chat.fail(ChatProviderError("boom"))
    chat_page.open()
    chat_page.type(TOO_LONG)

    try_send_all_ways(chat_page)

    expect(chat_page.error).to_be_visible()
    chat_page.assert_nothing_sent()
    expect(chat_page.send_error).to_have_count(0)
    assert chat.requests == []


def test_us6_ac2_contrast_provider_error_no_new_chat_button(chat_page, chat):
    chat.fail(ChatProviderError("boom"))
    chat_page.open()

    chat_page.send("Hello")

    expect(chat_page.send_error).to_be_visible()
    expect(chat_page.send_error_new_chat).to_have_count(0)


# Group 2 - conversation gone (AC-2, AC-12)


def test_us6_ac2_not_found_shows_gone_message_and_new_chat_button(chat_page, chat):
    start_in_gone_conversation(chat_page, chat)

    expect(chat_page.send_error_text).to_have_text(NOT_FOUND_TEXT)
    expect(chat_page.send_error_new_chat).to_have_text("Start a new chat")


def test_us6_ac2_new_chat_clears_chat_error_and_id_keeps_text(chat_page, chat):
    start_in_gone_conversation(chat_page, chat)
    assert chat_page.stored_id() == str(ABC)

    chat_page.send_error_new_chat.click()

    expect(chat_page.items).to_have_count(0)
    expect(chat_page.send_error).to_have_count(0)
    assert chat_page.stored_id() is None
    expect(chat_page.input).to_have_value("Hello")
    expect(chat_page.input).to_be_focused()

    chat.succeed("Hi again")
    resubmit(chat_page)

    assert chat.requests[-1].conversation_id is None
    assert chat.requests[-1].message == "Hello"


def test_us6_ac12_send_again_without_new_chat_same_id_same_error(chat_page, chat):
    start_in_gone_conversation(chat_page, chat)

    resubmit(chat_page)

    assert len(chat.requests) == 3
    assert chat.requests[1].conversation_id == ABC
    assert chat.requests[2].conversation_id == ABC
    expect(chat_page.send_error_text).to_have_text(NOT_FOUND_TEXT)
    assert chat_page.stored_id() == str(ABC)


# Group 3 - text kept for retry (AC-4, AC-9)


def test_us6_ac4_failure_text_stays_in_input(chat_page, chat):
    chat.fail(ChatProviderError("boom"))
    chat_page.open()

    chat_page.send("Hello")

    expect(chat_page.input).to_have_value("Hello")


def test_us6_ac4_input_cleared_while_waiting_failed_text_restored(chat_page, chat):
    reply = start_pending(chat_page, chat)
    chat_page.type("")

    reply.set_exception(ChatProviderError("boom"))
    finish(chat_page)

    expect(chat_page.input).to_have_value("Hello")


def test_us6_ac9_draft_typed_while_waiting_draft_kept(chat_page, chat):
    reply = start_pending(chat_page, chat)
    chat_page.type("Next")

    reply.set_exception(ChatProviderError("boom"))
    finish(chat_page)

    expect(chat_page.send_error).to_be_visible()
    expect(chat_page.input).to_have_value("Next")
    expect(chat_page.page.locator("#messages li.user.failed .text")).to_have_text("Hello")


def test_us6_ac4_resend_sends_same_text(chat_page, chat):
    chat.fail(ChatProviderError("boom"))
    chat_page.open()
    chat_page.send("Hello")

    resubmit(chat_page)

    assert len(chat.requests) == 2
    assert chat.requests[1].message == "Hello"
    assert chat.requests[1].conversation_id == chat.requests[0].conversation_id


# Group 4 - not shown as delivered, error in the chat (AC-5, Q10)


def test_us6_ac5_failure_message_marked_not_sent_no_reply(chat_page, chat):
    chat.fail(ChatProviderError("boom"))
    chat_page.open()

    chat_page.send("Hello")

    failed = chat_page.page.locator("#messages li.user.failed")
    expect(failed).to_have_count(1)
    expect(failed.locator(".not-sent")).to_have_text("Not sent")
    expect(chat_page.page.locator("#messages li.assistant")).to_have_count(0)


def test_us6_ac5_resend_replaces_failed_message(chat_page, chat):
    chat.fail(ChatProviderError("boom"))
    chat_page.open()
    chat_page.send("Hello")

    chat.succeed("Hi")
    resubmit(chat_page)

    assert chat_page.texts() == ["Hello", "Hi"]
    expect(chat_page.page.locator("#messages li.failed")).to_have_count(0)


def test_us6_ac5_error_message_follows_failed_message(chat_page, chat):
    chat.fail(ChatProviderError("boom"))
    chat_page.open()

    chat_page.send("Hello")

    rows = chat_page.items.evaluate_all(
        """lis => lis.map(li => ({ id: li.id, classes: [...li.classList],
                                   hasLabel: li.querySelector('.label') !== null,
                                   text: li.textContent }))"""
    )
    assert len(rows) == 2
    assert {"user", "failed"} <= set(rows[0]["classes"])
    assert rows[1]["id"] == "send-error"
    assert {"message", "error"} <= set(rows[1]["classes"])
    assert "assistant" not in rows[1]["classes"]
    assert not rows[1]["hasLabel"]
    assert "Assistant" not in rows[1]["text"]


def test_us6_ac5_failure_scrolls_to_error(chat_page, chat):
    chat_page.page.set_viewport_size({"width": 800, "height": 400})
    long_text = "\n".join(f"line {i}" for i in range(40))
    reply = start_pending(chat_page, chat, long_text)

    reply.set_exception(ChatProviderError("boom"))
    finish(chat_page)

    expect(chat_page.send_error).to_be_visible()
    eventually(chat_page.scrolled_to_bottom)


def test_us6_ac5_contrast_success_message_not_marked(chat_page, chat):
    chat.succeed("Hi")
    chat_page.open()

    chat_page.send("Hello")

    expect(chat_page.page.locator("#messages li.failed")).to_have_count(0)
    expect(chat_page.page.locator(".not-sent")).to_have_count(0)


# Group 5 - error clears (AC-6)


def test_us6_ac6_next_send_succeeds_error_removed(chat_page, chat):
    start_with_error(chat_page, chat)

    chat.succeed("Hi")
    resubmit(chat_page)

    expect(chat_page.send_error).to_have_count(0)


def test_us6_ac6_while_retry_pending_error_hidden(chat_page, chat):
    start_with_error(chat_page, chat)
    reply: Future = Future()
    chat.pending = reply

    chat_page.submit()

    eventually(lambda: len(chat.requests) == 2)
    expect(chat_page.send_error).to_have_count(0)
    expect(chat_page.typing).to_be_visible()

    reply.set_result("Hi")
    finish(chat_page)


def test_us6_ac6_contrast_second_failure_error_shown_again(chat_page, chat):
    start_with_error(chat_page, chat)

    chat.fail(ConversationNotFoundError(ABC))
    resubmit(chat_page)

    expect(chat_page.send_error).to_have_count(1)
    expect(chat_page.send_error_text).to_have_text(NOT_FOUND_TEXT)


def test_us6_ac6_contrast_typing_alone_does_not_clear_error(chat_page, chat):
    start_with_error(chat_page, chat)

    chat_page.type("x")

    expect(chat_page.send_error_text).to_have_text(UNAVAILABLE_TEXT)


# Group S1 - no raw errors shown (BR-1, SEC1)


def test_us6_br1_not_found_no_exception_text_shown(chat_page, chat):
    start_in_gone_conversation(chat_page, chat)

    expect(chat_page.send_error).to_be_visible()
    # The id is only kept in a hidden field so a retry can reuse it (AC-12); it's never shown.
    assert str(ABC) not in chat_page.page.locator("body").inner_text()
    assert "was not found" not in chat_page.page.content()


def test_us6_br1_unexpected_error_no_exception_text_shown(chat_page, chat):
    chat.fail(RuntimeError("secret-detail"))
    chat_page.open()

    chat_page.send("Hello")

    expect(chat_page.send_error).to_be_visible()
    assert "secret-detail" not in chat_page.page.content()
