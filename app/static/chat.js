// Chat page behaviour. HTMX posts the form to /ui/send and appends the reply;
// this script handles validation, the indicators, the user's own bubble, errors,
// "New chat" and reload restore.
(() => {
  'use strict';

  const maxLength = Number(document.currentScript.dataset.maxLength);
  const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

  const byId = id => document.getElementById(id);
  const form = byId('chat-form');
  const input = byId('chat-input');
  const sendButton = form.querySelector('.send');
  const newChatButton = byId('new-chat');
  const conversationId = byId('conversation-id');
  const messages = byId('messages');
  const scroller = byId('chat-scroll');
  const emptyState = byId('empty-state');
  const typing = byId('typing-indicator');
  const restoring = byId('restore-indicator');
  const error = byId('chat-error');
  const hint = byId('chat-hint');
  const counter = byId('char-count');

  // US-6: the only texts a send error can show. Picked from the status code, never from the
  // response body or an exception, so raw server errors never reach the visitor (BR-1).
  const errorTexts = {
    unavailable: 'The assistant is unavailable right now. Please try again.', // 502 (AC-1, AC-8)
    notFound: 'This conversation no longer exists.',                          // 404 (AC-2)
    offline: "Can't reach the server. Check your connection and try again.",  // no answer (AC-3)
    unexpected: 'Something went wrong. Please try again.'                     // anything else (AC-10)
  };

  const errorFor = status =>
    status === 0 ? 'offline'
      : status === 404 ? 'notFound'
        : status === 502 ? 'unavailable'
          : 'unexpected';

  // US-5: remember only the conversation id across reloads (BR-1: never message text).
  // localStorage can throw (private mode, storage disabled); treat that as "nothing saved".
  const store = (() => {
    const key = 'chatbot.conversationId';
    return {
      get: () => { try { return localStorage.getItem(key); } catch { return null; } },
      set: id => { try { localStorage.setItem(key, id); } catch { } },
      clear: () => { try { localStorage.removeItem(key); } catch { } }
    };
  })();

  const state = {
    sending: false,   // US-4: a request is in flight
    restoring: false, // US-5: the saved history is loading
    sentText: null,   // the trimmed text of the request in flight
    sentItem: null    // the <li> of the message in flight (US-6: marked "Not sent" on failure)
  };

  // US-3 BR-1: length is measured on the trimmed text, which is what gets sent.
  const length = () => input.value.trim().length;
  const canSend = () => length() > 0 && length() <= maxLength && !state.sending && !state.restoring;
  // US-7 AC-4, AC-5: "New chat" waits for a send or restore, so nothing late lands in the new chat.
  const canStartNewChat = () => !state.sending && !state.restoring;

  function render() {
    const n = length();
    const tooLong = n > maxLength;

    sendButton.disabled = !canSend();
    newChatButton.disabled = !canStartNewChat();
    error.hidden = !tooLong;
    hint.hidden = tooLong;
    counter.hidden = n === 0;
    counter.textContent = `${n} / ${maxLength}`;
    counter.classList.toggle('over', tooLong);
    typing.hidden = !state.sending;
    restoring.hidden = !state.restoring;
    emptyState.hidden = state.restoring || messages.children.length > 0;
  }

  // US-2 AC-4: keep the newest message in view.
  const scrollToBottom = () => { scroller.scrollTop = scroller.scrollHeight; };

  function element(tag, className, text) {
    const el = document.createElement(tag);
    el.className = className;
    if (text !== undefined) el.textContent = text; // textContent keeps it plain text
    return el;
  }

  // The user's own bubble.
  function appendUserMessage(text) {
    const li = element('li', 'message user');
    li.append(element('span', 'label', 'You'), element('div', 'text', text));
    messages.append(li);
    return li;
  }

  // US-6 Q10: the error is shown in the chat, right after the failed message. It has no
  // label and isn't styled as a reply, so it never looks like the assistant said it.
  function showSendError(kind) {
    const li = element('li', 'message error');
    li.id = 'send-error';
    li.setAttribute('role', 'alert');
    li.append(element('div', 'text', errorTexts[kind]));
    if (kind === 'notFound') {
      // AC-2: offer a fresh chat, keeping the typed text (Q11).
      const button = element('button', 'new-chat', 'Start a new chat');
      button.id = 'send-error-new-chat';
      button.type = 'button';
      button.addEventListener('click', () => startNewChat({ keepInput: true }));
      li.append(button);
    }
    messages.append(li);
  }

  // US-6 Q5, AC-6: a new send replaces the earlier failed message, and the old error goes away.
  function clearFailure() {
    messages.querySelectorAll('li.failed, #send-error').forEach(li => li.remove());
  }

  // US-7 (sidebar, keepInput false) and US-6 AC-2 (error button, keepInput true).
  // Client-side only: the old conversation stays on the server (US-7 AC-6).
  function startNewChat({ keepInput }) {
    messages.replaceChildren();
    conversationId.value = '';
    store.clear();
    if (!keepInput) {
      input.value = '';
    }
    render();
    input.focus();
  }

  input.addEventListener('input', render);

  // Enter sends, Shift+Enter adds a new line (US-1 AC3).
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      form.requestSubmit();
    }
  });

  newChatButton.addEventListener('click', () => {
    // Checked here too, so a click that beats the disabled state can't reset mid-request (SEC1).
    if (canStartNewChat()) {
      startNewChat({ keepInput: false });
    }
  });

  // Every send path (button, Enter, a forced submit) goes through this guard.
  form.addEventListener('htmx:configRequest', e => {
    if (!canSend()) {
      e.preventDefault();
      return;
    }
    state.sentText = input.value.trim();
    e.detail.parameters.message = state.sentText; // US-1 AC5: send the trimmed text
  });

  form.addEventListener('htmx:beforeRequest', () => {
    state.sending = true;
    clearFailure();
    state.sentItem = appendUserMessage(state.sentText);
    render();
    scrollToBottom();
  });

  form.addEventListener('htmx:afterRequest', e => {
    state.sending = false;

    if (e.detail.successful) {
      const id = e.detail.xhr.getResponseHeader('X-Conversation-Id');
      if (id) {
        conversationId.value = id; // US-2 BR-1: always the id from the latest reply
        store.set(id);             // US-5 AC1
      }
      // US-4 AC7: keep a draft typed while waiting.
      if (input.value.trim() === state.sentText) {
        input.value = '';
      }
    } else {
      // US-6 AC-5: my message is marked "Not sent" and no reply is added.
      // The conversation id is kept, even when it's gone (AC-12).
      state.sentItem.classList.add('failed');
      state.sentItem.append(element('span', 'not-sent', 'Not sent'));
      // A network failure has no status (0).
      showSendError(errorFor(e.detail.xhr ? e.detail.xhr.status : 0));
      // AC-4, AC-9: put the failed text back, unless a new draft was typed while waiting.
      if (input.value.trim() === '') {
        input.value = state.sentText;
      }
    }

    state.sentText = null;
    state.sentItem = null;
    render();
    scrollToBottom();
    input.focus();
  });

  messages.addEventListener('htmx:afterSwap', scrollToBottom);

  // US-5: reload the saved conversation, if any.
  async function restore() {
    const saved = store.get();
    if (saved === null) {
      return;
    }
    // AC7 / SEC2: a tampered value is dropped without calling the server.
    if (!uuidPattern.test(saved)) {
      store.clear();
      return;
    }

    // AC5: show the indicator and block sending until the history is in.
    state.restoring = true;
    render();

    try {
      const response = await fetch(`/ui/conversations/${encodeURIComponent(saved)}`);

      if (response.status === 404) {
        // AC4: the conversation is gone; start fresh without an error.
        store.clear();
        return;
      }
      if (!response.ok) {
        throw new Error(`Restore failed with ${response.status}`);
      }

      // Server-rendered by Jinja with autoescaping, so message text is never HTML (SEC1).
      messages.innerHTML = await response.text();
      conversationId.value = saved;
    } catch {
      // AC6 / D2: keep the saved id so a later reload can recover, and keep sending into it.
      conversationId.value = saved;
    } finally {
      state.restoring = false;
      render();
      scrollToBottom();
    }
  }

  render();
  restore();
})();
