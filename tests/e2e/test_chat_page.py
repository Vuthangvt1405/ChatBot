"""Chat page behaviour, US-1 to US-5. Ported from the bUnit ChatPageTests of the C# version.

US-6 and US-7 are in test_chat_page_errors.py and test_chat_page_new_chat.py.
"""

import re
import uuid
from concurrent.futures import Future

from playwright.sync_api import expect

from app.errors import ChatProviderError
from tests.e2e.conftest import ChatPage, FakeChatService, convo, eventually

USER = "message user"
ASSISTANT = "message assistant"
OVER = re.compile(r"\bover\b")


# ---------- US-1 Send a message and get a reply ----------


def test_ac1_send_shows_my_message_then_reply(chat_page: ChatPage, chat: FakeChatService):
    chat.replies.append("Hi")
    chat_page.open()

    chat_page.send("Hello")

    assert len(chat.requests) == 1
    assert chat_page.texts() == ["Hello", "Hi"]


def test_ac1_contrast_nothing_sent_no_messages_no_request(chat_page, chat):
    chat_page.open()

    assert chat.requests == []
    assert chat_page.messages() == []


def test_ac2_messages_are_labelled_and_in_order(chat_page, chat):
    chat.replies.extend(["Hi", "Fine"])
    chat_page.open()

    chat_page.send("Hello")
    chat_page.send("How are you?")

    assert chat_page.messages() == [
        (USER, "You", "Hello"),
        (ASSISTANT, "Assistant", "Hi"),
        (USER, "You", "How are you?"),
        (ASSISTANT, "Assistant", "Fine"),
    ]


def test_ac2_contrast_reply_is_not_styled_as_mine(chat_page, chat):
    chat.replies.append("Hi")
    chat_page.open()

    chat_page.send("Hello")

    css_class, label, _ = chat_page.messages()[1]
    assert css_class != USER
    assert label != "You"


def test_ac3_enter_sends(chat_page, chat):
    chat.replies.append("Hi")
    chat_page.open()
    chat_page.type("Hello")

    chat_page.enter()

    eventually(lambda: len(chat.requests) == 1)
    expect(chat_page.items).to_have_count(2)


def test_ac3_contrast_shift_enter_does_not_send(chat_page, chat):
    chat_page.open()
    chat_page.type("Hello")

    chat_page.enter(shift=True)

    chat_page.assert_nothing_sent()
    assert chat.requests == []


def test_ac4_after_reply_input_is_empty_and_focused(chat_page, chat):
    chat.replies.append("Hi")
    chat_page.open()

    chat_page.send("Hello")

    expect(chat_page.input).to_have_value("")
    expect(chat_page.input).to_be_focused()


def test_ac4_contrast_while_reply_pending_input_is_kept(chat_page, chat):
    start_pending(chat_page, chat)

    expect(chat_page.input).to_have_value("Hello")


def test_ac5_message_is_trimmed(chat_page, chat):
    chat.replies.append("Hi")
    chat_page.open()

    chat_page.send("  Hello  ")

    assert chat.requests[0].message == "Hello"
    assert chat.requests[0].conversation_id is None


def test_ac5_contrast_inner_spaces_are_kept(chat_page, chat):
    chat.replies.append("Hi")
    chat_page.open()

    chat_page.send("Hello  world")

    assert chat.requests[0].message == "Hello  world"


# ---------- US-2 Keep chatting in the same conversation ----------

ABC = uuid.UUID("00000000-0000-0000-0000-000000000abc")
DEF = uuid.UUID("00000000-0000-0000-0000-000000000def")


def test_us2_ac1_first_message_has_no_conversation_id(chat_page, chat):
    chat.replies.append("Hi")
    chat_page.open()

    chat_page.send("Hello")

    assert chat.requests[0].conversation_id is None


def test_us2_ac2_follow_up_reuses_returned_conversation_id(chat_page, chat):
    chat.replies.extend(["Hi", "Fine"])
    chat.conversation_ids.append(ABC)
    chat_page.open()

    chat_page.send("Hello")
    chat_page.send("  How are you?  ")

    assert chat.requests[1].conversation_id == ABC
    assert chat.requests[1].message == "How are you?"


def test_us2_br1_uses_id_from_latest_response(chat_page, chat):
    chat.replies.extend(["1", "2", "3"])
    chat.conversation_ids.extend([ABC, DEF])
    chat_page.open()

    chat_page.send("a")
    chat_page.send("b")
    chat_page.send("c")

    assert chat.requests[2].conversation_id == DEF


def test_us2_ac3_earlier_messages_stay_in_order_new_pair_at_bottom(chat_page, chat):
    chat.replies.extend(["1", "2", "3"])
    chat_page.open()

    chat_page.send("a")
    chat_page.send("b")
    chat_page.send("c")

    assert chat_page.texts() == ["a", "1", "b", "2", "c", "3"]


def test_us2_ac4_new_messages_scroll_to_latest(chat_page, chat):
    chat_page.page.set_viewport_size({"width": 800, "height": 400})
    long_text = "\n".join(f"line {i}" for i in range(40))
    reply = start_pending(chat_page, chat, long_text)

    # My message is shown and scrolled into view before the reply arrives.
    eventually(chat_page.scrolled_to_bottom)

    reply.set_result(long_text)
    expect(chat_page.typing).to_be_hidden()
    expect(chat_page.items).to_have_count(2)

    eventually(chat_page.scrolled_to_bottom)


def test_us2_ac4_contrast_no_new_messages_no_scroll(chat_page, chat):
    chat_page.open()

    assert chat_page.page.evaluate("document.getElementById('chat-scroll').scrollTop") == 0


# ---------- US-3 Block invalid messages ----------

MAX = "a" * 4000
TOO_LONG = "a" * 4001
TOO_LONG_ERROR = "Message must be 4000 characters or fewer"


def try_send_all_ways(chat_page: ChatPage) -> None:
    chat_page.enter()
    chat_page.submit()


def test_us3_ac1_whitespace_only_send_disabled(chat_page, chat):
    chat_page.open()

    chat_page.type("   ")

    expect(chat_page.send_button).to_be_disabled()


def test_us3_ac1_contrast_text_send_enabled(chat_page, chat):
    chat_page.open()

    chat_page.type("Hello")

    expect(chat_page.send_button).to_be_enabled()


def test_us3_ac1_fresh_page_send_disabled(chat_page, chat):
    chat_page.open()

    expect(chat_page.send_button).to_be_disabled()


def test_us3_ac1_whitespace_only_enter_and_submit_do_not_send(chat_page, chat):
    chat_page.open()
    chat_page.type("   ")

    try_send_all_ways(chat_page)

    chat_page.assert_nothing_sent()
    assert chat.requests == []
    assert chat_page.messages() == []


def test_us3_ac2_too_long_send_disabled_error_shown(chat_page, chat):
    chat_page.open()

    chat_page.type(TOO_LONG)

    expect(chat_page.send_button).to_be_disabled()
    expect(chat_page.error).to_have_text(TOO_LONG_ERROR)
    expect(chat_page.hint).to_be_hidden()


def test_us3_ac2_too_long_enter_and_submit_do_not_send_text_kept(chat_page, chat):
    chat_page.open()
    chat_page.type(TOO_LONG)

    try_send_all_ways(chat_page)

    chat_page.assert_nothing_sent()
    assert chat.requests == []
    assert chat_page.messages() == []
    expect(chat_page.input).to_have_value(TOO_LONG)


def test_us3_ac2_shortened_back_to_limit_error_clears(chat_page, chat):
    chat_page.open()
    chat_page.type(TOO_LONG)

    chat_page.type(MAX)

    expect(chat_page.error).to_be_hidden()
    expect(chat_page.hint).to_be_visible()
    expect(chat_page.send_button).to_be_enabled()


def test_us3_ac3_exactly_4000_is_sent(chat_page, chat):
    chat.replies.append("Hi")
    chat_page.open()
    chat_page.type(MAX)

    expect(chat_page.send_button).to_be_enabled()
    expect(chat_page.error).to_be_hidden()

    chat_page.send(MAX)

    assert len(chat.requests[0].message) == 4000


def test_us3_ac3_4000_plus_outer_spaces_is_sent_trimmed(chat_page, chat):
    chat.replies.append("Hi")
    chat_page.open()

    chat_page.send("  " + MAX + "  ")

    assert chat.requests[0].message == MAX


def test_us3_ac4_counter_shows_trimmed_length(chat_page, chat):
    chat_page.open()

    chat_page.type("  Hi  ")

    expect(chat_page.counter).to_have_text("2 / 4000")
    expect(chat_page.counter).not_to_have_class(OVER)


def test_us3_ac4_contrast_over_limit_counter_warns(chat_page, chat):
    chat_page.open()

    chat_page.type(TOO_LONG)

    expect(chat_page.counter).to_have_text("4001 / 4000")
    expect(chat_page.counter).to_have_class(OVER)


def test_us3_ac4_contrast_empty_or_whitespace_no_counter(chat_page, chat):
    chat_page.open()
    expect(chat_page.counter).to_be_hidden()

    chat_page.type("   ")

    expect(chat_page.counter).to_be_hidden()


# ---------- US-4 Show that the assistant is working ----------
# Baseline: open, type "Hello", submit with the reply unresolved (request in flight).


def start_pending(chat_page: ChatPage, chat: FakeChatService, text: str = "Hello") -> Future:
    reply: Future = Future()
    chat.pending = reply
    chat_page.open()
    chat_page.type(text)
    chat_page.submit()
    eventually(lambda: len(chat.requests) == 1)
    return reply


def finish(chat_page: ChatPage) -> None:
    expect(chat_page.typing).to_be_hidden()


# Group 1 - indicator while waiting (AC1, AC6)


def test_us4_ac1_while_pending_typing_indicator_shown(chat_page, chat):
    start_pending(chat_page, chat)

    expect(chat_page.typing).to_be_visible()
    expect(chat_page.typing).to_have_text("Assistant is typing")
    expect(chat_page.typing).to_have_attribute("role", "status")
    assert chat_page.messages() == [(USER, "You", "Hello")]


def test_us4_ac1_contrast_fresh_page_no_indicator(chat_page, chat):
    chat_page.open()

    expect(chat_page.typing).to_be_hidden()
    assert chat.requests == []


def test_us4_ac1_contrast_blocked_send_no_indicator(chat_page, chat):
    chat_page.open()
    chat_page.type("   ")

    chat_page.submit()

    expect(chat_page.typing).to_be_hidden()
    chat_page.assert_nothing_sent()
    assert chat.requests == []


def test_us4_ac1_contrast_indicator_is_not_a_message(chat_page, chat):
    start_pending(chat_page, chat)

    expect(chat_page.items).to_have_count(1)


# Group 2 - no double send (AC2)


def test_us4_ac2_while_pending_send_disabled(chat_page, chat):
    start_pending(chat_page, chat)

    expect(chat_page.send_button).to_be_disabled()


def test_us4_ac2_while_pending_enter_does_not_send_again(chat_page, chat):
    start_pending(chat_page, chat)

    chat_page.enter()

    chat_page.page.wait_for_timeout(200)
    assert len(chat.requests) == 1
    expect(chat_page.page.locator("#messages li.user")).to_have_count(1)


def test_us4_ac2_while_pending_submit_does_not_send_again(chat_page, chat):
    start_pending(chat_page, chat)

    chat_page.submit()

    chat_page.page.wait_for_timeout(200)
    assert len(chat.requests) == 1
    assert len(chat_page.send_requests) == 1


def test_us4_ac2_while_pending_new_valid_text_still_disabled(chat_page, chat):
    start_pending(chat_page, chat)

    chat_page.type("Next")

    expect(chat_page.send_button).to_be_disabled()


# Group 3 - indicator clears when done (AC3)


def test_us4_ac3_on_success_indicator_removed_send_reenabled_when_valid(chat_page, chat):
    reply = start_pending(chat_page, chat)

    reply.set_result("Hi")
    finish(chat_page)
    chat_page.type("Next")

    expect(chat_page.typing).to_be_hidden()
    expect(chat_page.send_button).to_be_enabled()


def test_us4_ac3_on_success_empty_input_send_stays_disabled(chat_page, chat):
    reply = start_pending(chat_page, chat)

    reply.set_result("Hi")
    finish(chat_page)

    expect(chat_page.send_button).to_be_disabled()


def test_us4_ac3_on_provider_error_indicator_removed_send_reenabled(chat_page, chat):
    reply = start_pending(chat_page, chat)

    reply.set_exception(ChatProviderError("boom"))
    finish(chat_page)

    expect(chat_page.send_button).to_be_enabled()
    expect(chat_page.input).to_have_value("Hello")
    expect(chat_page.page.locator("#messages li.assistant")).to_have_count(0)


def test_us4_ac3_on_timeout_indicator_removed(chat_page, chat):
    reply = start_pending(chat_page, chat)

    reply.set_exception(TimeoutError())
    finish(chat_page)

    expect(chat_page.send_button).to_be_enabled()
    expect(chat_page.page.locator("#messages li.assistant")).to_have_count(0)


def test_us4_ac3_after_failure_can_send_again(chat_page, chat):
    reply = start_pending(chat_page, chat)
    reply.set_exception(ChatProviderError("boom"))
    finish(chat_page)

    chat.pending = None
    chat.replies.append("Hi")
    with chat_page.page.expect_response("**/ui/send"):
        chat_page.submit()
    finish(chat_page)

    assert len(chat.requests) == 2
    expect(chat_page.page.locator("#messages li.assistant")).to_have_count(1)


# Group 4 - typing while waiting (AC4, AC7)


def test_us4_ac4_while_pending_input_editable(chat_page, chat):
    start_pending(chat_page, chat)

    expect(chat_page.input).to_be_editable()
    chat_page.type("Next")
    expect(chat_page.input).to_have_value("Next")


def test_us4_ac7_draft_typed_while_pending_kept_after_reply(chat_page, chat):
    reply = start_pending(chat_page, chat)
    chat_page.type("Next")

    reply.set_result("Hi")
    finish(chat_page)

    expect(chat_page.input).to_have_value("Next")


def test_us4_ac7_contrast_unchanged_text_cleared_after_reply(chat_page, chat):
    reply = start_pending(chat_page, chat)

    reply.set_result("Hi")
    finish(chat_page)

    expect(chat_page.input).to_have_value("")


# Group S1 - double submit guard (AC5)


def test_us4_ac5_forced_submit_while_pending_single_request(chat_page, chat):
    chat.pending = Future()
    chat_page.open()
    chat_page.type("Hello")

    chat_page.page.evaluate(
        """() => { const form = document.getElementById('chat-form');
                   form.requestSubmit(); form.requestSubmit(); }"""
    )

    eventually(lambda: len(chat.requests) == 1)
    chat_page.page.wait_for_timeout(200)
    assert len(chat.requests) == 1
    expect(chat_page.page.locator("#messages li.user")).to_have_count(1)


# Group S2 - no leakage on failure (SEC3)


def test_us4_sec3_on_error_no_exception_text_shown(chat_page, chat):
    reply = start_pending(chat_page, chat)

    reply.set_exception(ChatProviderError("secret-detail"))
    finish(chat_page)

    assert "secret-detail" not in chat_page.page.content()


# ---------- US-5 Keep the conversation after reloading ----------

SAVED_A = uuid.UUID("3f2b8c1e-6a4d-4e0f-9b7a-2c5d1e8f4a90")


def open_restored(chat_page: ChatPage, chat: FakeChatService) -> None:
    chat.conversations[SAVED_A] = convo(
        SAVED_A,
        ("user", "Hi"),
        ("assistant", "Hello!"),
        ("user", "How are you?"),
        ("assistant", "Fine."),
    )
    chat_page.open(str(SAVED_A))
    expect(chat_page.items).to_have_count(4)
    expect(chat_page.restore_indicator).to_be_hidden()


def settle(chat_page: ChatPage) -> None:
    chat_page.page.wait_for_load_state("networkidle")


# Group 1 - id is saved (AC1, BR-1)


def test_us5_ac1_after_reply_id_is_saved(chat_page, chat):
    conversation_id = uuid.uuid4()
    chat.replies.append("Hi")
    chat.conversation_ids.append(conversation_id)
    chat_page.open()

    chat_page.send("Hello")

    assert chat_page.stored_id() == str(conversation_id)


def test_us5_ac1_follow_up_saves_latest_id(chat_page, chat):
    latest = uuid.uuid4()
    chat.replies.extend(["Hi", "Again"])
    chat.conversation_ids.extend([uuid.uuid4(), latest])
    chat_page.open()

    chat_page.send("Hello")
    chat_page.send("More")

    assert chat_page.stored_id() == str(latest)


def test_us5_ac1_contrast_failed_send_nothing_saved(chat_page, chat):
    failed: Future = Future()
    failed.set_exception(ChatProviderError("boom"))
    chat.pending = failed
    chat_page.open()

    chat_page.send("Hello")

    assert chat_page.stored_id() is None


def test_us5_ac1_contrast_fresh_page_nothing_saved(chat_page, chat):
    chat_page.open()
    settle(chat_page)

    assert chat_page.stored_id() is None


def test_us5_br1_only_id_is_stored(chat_page, chat):
    chat.replies.append("Hi")
    chat_page.open()

    chat_page.send("Hello")

    entries = chat_page.page.evaluate("Object.entries(localStorage)")
    assert len(entries) == 1
    uuid.UUID(entries[0][1])


# Group 2 - history reloads (AC2, AC7)


def test_us5_ac2_saved_id_shows_history_in_order_with_labels(chat_page, chat):
    open_restored(chat_page, chat)

    assert chat_page.messages() == [
        (USER, "You", "Hi"),
        (ASSISTANT, "Assistant", "Hello!"),
        (USER, "You", "How are you?"),
        (ASSISTANT, "Assistant", "Fine."),
    ]
    assert chat.get_requests == [SAVED_A]


def test_us5_ac2_restored_history_scrolls_to_latest(chat_page, chat):
    chat_page.page.set_viewport_size({"width": 800, "height": 400})
    long_text = "\n".join(f"line {i}" for i in range(20))
    chat.conversations[SAVED_A] = convo(SAVED_A, ("user", long_text), ("assistant", long_text))

    chat_page.open(str(SAVED_A))
    expect(chat_page.items).to_have_count(2)

    eventually(chat_page.scrolled_to_bottom)


def test_us5_ac2_contrast_no_saved_id_no_fetch(chat_page, chat):
    chat_page.open()
    settle(chat_page)

    assert chat.get_requests == []
    expect(chat_page.empty).to_be_visible()


def test_us5_ac7_invalid_saved_id_no_fetch_cleared(chat_page, chat):
    chat_page.open("abc")

    eventually(lambda: chat_page.stored_id() is None)
    settle(chat_page)
    assert chat.get_requests == []
    assert chat_page.messages() == []


def test_us5_ac2_contrast_empty_history_shows_empty_state(chat_page, chat):
    chat.conversations[SAVED_A] = convo(SAVED_A)

    chat_page.open(str(SAVED_A))

    eventually(lambda: len(chat.get_requests) == 1)
    expect(chat_page.restore_indicator).to_be_hidden()
    expect(chat_page.empty).to_be_visible()
    assert chat_page.stored_id() == str(SAVED_A)


# Group 3 - next send continues (AC3)


def test_us5_ac3_after_restore_send_uses_saved_id(chat_page, chat):
    chat.replies.append("Sure")
    open_restored(chat_page, chat)

    chat_page.send("More")

    assert chat.requests[0].conversation_id == SAVED_A


def test_us5_ac3_contrast_not_found_send_has_no_id(chat_page, chat):
    chat.replies.append("Hi")
    chat_page.open(str(SAVED_A))
    eventually(lambda: chat_page.stored_id() is None)
    expect(chat_page.restore_indicator).to_be_hidden()

    chat_page.send("Hello")

    assert chat.requests[0].conversation_id is None


# Group 4 - missing conversation (AC4)


def test_us5_ac4_not_found_clears_id_empty_chat_no_error(chat_page, chat):
    chat_page.open(str(SAVED_A))

    eventually(lambda: chat_page.stored_id() is None)
    expect(chat_page.restore_indicator).to_be_hidden()
    expect(chat_page.empty).to_be_visible()
    expect(chat_page.error).to_be_hidden()


def test_us5_ac4_contrast_found_id_not_cleared(chat_page, chat):
    open_restored(chat_page, chat)

    assert chat_page.stored_id() == str(SAVED_A)


# Group 5 - loading state (AC5)


def start_restoring(chat_page: ChatPage, chat: FakeChatService) -> Future:
    restore: Future = Future()
    chat.pending_conversation = restore
    chat_page.open(str(SAVED_A))
    expect(chat_page.restore_indicator).to_be_visible()
    return restore


def test_us5_ac5_while_restoring_indicator_shown_send_disabled(chat_page, chat):
    start_restoring(chat_page, chat)
    chat_page.type("Hello")

    expect(chat_page.restore_indicator).to_have_attribute("role", "status")
    expect(chat_page.restore_indicator).to_contain_text("Loading conversation")
    expect(chat_page.empty).to_be_hidden()
    expect(chat_page.send_button).to_be_disabled()


def test_us5_ac5_after_restore_indicator_cleared_send_enabled(chat_page, chat):
    restore = start_restoring(chat_page, chat)
    chat_page.type("Hello")

    restore.set_result(convo(SAVED_A, ("user", "Hi"), ("assistant", "Hello!")))

    expect(chat_page.restore_indicator).to_be_hidden()
    expect(chat_page.send_button).to_be_enabled()


def test_us5_ac5_while_restoring_enter_and_submit_do_not_send(chat_page, chat):
    start_restoring(chat_page, chat)
    chat_page.type("Hello")

    chat_page.enter()
    chat_page.submit()

    chat_page.assert_nothing_sent()
    assert chat.requests == []


def test_us5_ac5_contrast_no_saved_id_no_indicator(chat_page, chat):
    chat_page.open()
    settle(chat_page)

    expect(chat_page.restore_indicator).to_be_hidden()


# Group 6 - restore failure (AC6; decision D2: keep the saved id)


def test_us5_ac6_restore_throws_empty_chat_indicator_cleared_send_works(chat_page, chat):
    chat.throw_on_get = True
    chat.replies.append("Hi")

    chat_page.open(str(SAVED_A))

    eventually(lambda: len(chat.get_requests) == 1)
    expect(chat_page.restore_indicator).to_be_hidden()
    expect(chat_page.empty).to_be_visible()
    assert chat_page.stored_id() == str(SAVED_A)
    assert "db down" not in chat_page.page.content()

    chat_page.send("Hello")

    assert chat.requests[0].conversation_id == SAVED_A
    assert chat_page.texts() == ["Hello", "Hi"]


# Group S1 - encoding (SEC1)


def test_us5_sec1_restored_html_rendered_as_text(chat_page, chat):
    chat.conversations[SAVED_A] = convo(SAVED_A, ("user", "Hi"), ("assistant", "<b>x</b>"))

    chat_page.open(str(SAVED_A))

    expect(chat_page.items).to_have_count(2)
    assert chat_page.messages()[1][2] == "<b>x</b>"
    expect(chat_page.page.locator("#messages b")).to_have_count(0)
