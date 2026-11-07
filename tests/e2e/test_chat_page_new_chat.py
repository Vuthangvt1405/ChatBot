"""US-7 Start a new chat, on the chat page.

Plan: docs/features/plans/US-7-new-chat-plan.md §7
"""

from playwright.sync_api import expect

from app.errors import ChatProviderError
from tests.e2e.conftest import ChatPage, FakeChatService, convo
from tests.e2e.test_chat_page import (
    ABC,
    DEF,
    SAVED_A,
    finish,
    settle,
    start_pending,
    start_restoring,
)
from tests.e2e.test_chat_page_errors import start_in_gone_conversation


def force_click_new_chat(chat_page: ChatPage) -> None:
    """A click that beats the disabled state (SEC1): re-enable the button, then click it."""
    chat_page.page.evaluate(
        "() => { const b = document.getElementById('new-chat'); b.disabled = false; b.click(); }"
    )


def start_with_exchange_and_unsent_text(chat_page: ChatPage, chat: FakeChatService) -> None:
    """G1 baseline: one exchange "Hello"/"Hi", then "unsent" typed but not sent."""
    chat.replies.append("Hi")
    chat_page.open()
    chat_page.send("Hello")
    chat_page.type("unsent")


def start_in_conversation_abc(chat_page: ChatPage, chat: FakeChatService) -> None:
    """G2 baseline: one exchange in conversation ABC (so ABC is saved)."""
    chat.replies.append("Hi")
    chat.conversation_ids.append(ABC)
    chat_page.open()
    chat_page.send("Hello")


# Group 1: New chat clears the page (AC-1, AC-7)


def test_us7_ac1_new_chat_clears_messages_and_input_focuses_input(chat_page, chat):
    start_with_exchange_and_unsent_text(chat_page, chat)

    chat_page.new_chat.click()

    assert chat_page.messages() == []
    expect(chat_page.empty).to_be_visible()
    expect(chat_page.input).to_have_value("")
    expect(chat_page.input).to_be_focused()


def test_us7_ac7_after_failed_send_clears_failed_message_and_error(chat_page, chat):
    chat.fail(ChatProviderError("down"))
    chat_page.open()
    chat_page.send("Hello")
    expect(chat_page.send_error).to_be_visible()
    expect(chat_page.input).to_have_value("Hello")

    chat_page.new_chat.click()

    expect(chat_page.page.locator("li.failed")).to_have_count(0)
    expect(chat_page.send_error).to_have_count(0)
    expect(chat_page.input).to_have_value("")


def test_us7_ac1_not_found_sidebar_button_clears_text_too(chat_page, chat):
    start_in_gone_conversation(chat_page, chat)

    chat_page.new_chat.click()

    expect(chat_page.items).to_have_count(0)
    expect(chat_page.input).to_have_value("")


def test_us7_ac1_contrast_no_click_conversation_stays(chat_page, chat):
    start_with_exchange_and_unsent_text(chat_page, chat)

    assert chat_page.texts() == ["Hello", "Hi"]
    expect(chat_page.input).to_have_value("unsent")
    assert chat_page.stored_id() is not None


# Group 2: Old conversation forgotten (AC-2, AC-3, AC-6, SEC2)


def test_us7_ac2_new_chat_next_send_has_no_conversation_id(chat_page, chat):
    start_in_conversation_abc(chat_page, chat)
    chat_page.new_chat.click()

    chat.replies.append("Sure")
    chat_page.send("New topic")

    assert chat.requests[-1].conversation_id is None
    assert chat_page.texts() == ["New topic", "Sure"]


def test_us7_ac2_new_chat_clears_saved_id(chat_page, chat):
    start_in_conversation_abc(chat_page, chat)
    assert chat_page.stored_id() == str(ABC)

    chat_page.new_chat.click()

    assert chat_page.stored_id() is None


def test_us7_ac2_after_new_chat_second_send_uses_new_id(chat_page, chat):
    start_in_conversation_abc(chat_page, chat)
    chat_page.new_chat.click()

    chat.conversation_ids.append(DEF)
    chat.replies.extend(["One", "Two"])
    chat_page.send("First")
    chat_page.send("Second")

    assert chat.requests[-2].conversation_id is None
    assert chat.requests[-1].conversation_id == DEF
    assert chat_page.stored_id() == str(DEF)


def test_us7_ac3_reload_after_new_chat_nothing_restored(chat_page, chat):
    start_in_conversation_abc(chat_page, chat)
    chat_page.new_chat.click()

    chat_page.page.reload()
    settle(chat_page)

    assert chat.get_requests == []
    assert chat_page.messages() == []
    expect(chat_page.restore_indicator).to_be_hidden()


def test_us7_ac6_new_chat_makes_no_server_call(chat_page, chat):
    start_in_conversation_abc(chat_page, chat)
    sends, gets = len(chat.requests), len(chat.get_requests)
    calls: list[str] = []
    chat_page.page.on("request", lambda request: calls.append(request.url))

    chat_page.new_chat.click()
    chat_page.page.wait_for_timeout(200)

    assert calls == []
    assert len(chat.requests) == sends
    assert len(chat.get_requests) == gets


def test_us7_ac2_contrast_no_new_chat_next_send_keeps_id(chat_page, chat):
    start_in_conversation_abc(chat_page, chat)

    chat.replies.append("Ok")
    chat_page.send("More")

    assert chat.requests[-1].conversation_id == ABC
    assert chat_page.stored_id() == str(ABC)


# Group 3: Disabled while busy (AC-4, AC-5, SEC1)


def test_us7_ac4_idle_new_chat_enabled(chat_page, chat):
    start_in_conversation_abc(chat_page, chat)

    expect(chat_page.new_chat).to_be_enabled()


def test_us7_ac4_after_reply_new_chat_enabled_again(chat_page, chat):
    reply = start_pending(chat_page, chat)
    expect(chat_page.new_chat).to_be_disabled()

    reply.set_result("Hi")
    finish(chat_page)

    expect(chat_page.new_chat).to_be_enabled()


def test_us7_ac4_after_failure_new_chat_enabled(chat_page, chat):
    reply = start_pending(chat_page, chat)

    reply.set_exception(ChatProviderError("down"))
    finish(chat_page)

    expect(chat_page.send_error).to_be_visible()
    expect(chat_page.new_chat).to_be_enabled()


def test_us7_q3_empty_chat_new_chat_enabled(chat_page, chat):
    chat_page.open()

    expect(chat_page.page.locator("aside.sidebar #new-chat")).to_have_count(1)
    expect(chat_page.new_chat).to_be_enabled()

    chat_page.new_chat.click()

    assert chat_page.messages() == []
    expect(chat_page.send_error).to_have_count(0)
    expect(chat_page.empty).to_be_visible()


def test_us7_ac4_while_sending_new_chat_disabled(chat_page, chat):
    start_pending(chat_page, chat)

    expect(chat_page.typing).to_be_visible()
    expect(chat_page.new_chat).to_be_disabled()


def test_us7_ac4_while_sending_click_does_nothing_late_reply_stays(chat_page, chat):
    reply = start_pending(chat_page, chat)
    chat.conversation_ids.append(ABC)

    force_click_new_chat(chat_page)
    reply.set_result("Late")
    finish(chat_page)

    expect(chat_page.items).to_have_count(2)
    assert chat_page.texts() == ["Hello", "Late"]
    assert chat_page.stored_id() == str(ABC)

    chat.pending = None
    chat.replies.append("Ok")
    chat_page.send("Again")
    assert chat.requests[-1].conversation_id == ABC


def test_us7_ac5_while_restoring_new_chat_disabled(chat_page, chat):
    start_restoring(chat_page, chat)

    expect(chat_page.new_chat).to_be_disabled()


def test_us7_ac5_while_restoring_click_does_nothing(chat_page, chat):
    restore = start_restoring(chat_page, chat)

    force_click_new_chat(chat_page)
    restore.set_result(convo(SAVED_A, ("user", "Hi"), ("assistant", "Hello!")))

    expect(chat_page.items).to_have_count(2)
    assert chat_page.texts() == ["Hi", "Hello!"]
    assert chat_page.stored_id() == str(SAVED_A)
