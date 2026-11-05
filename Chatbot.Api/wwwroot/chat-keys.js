// Stop Enter from adding a newline in the chat box; Blazor's @onkeydown does the send.
// Shift+Enter keeps the default (new line).
document.addEventListener('keydown', e => {
  if (e.target.id === 'chat-input' && e.key === 'Enter' && !e.shiftKey) e.preventDefault();
});

// Scroll the message list to the newest message (US-2 AC-4).
window.chatScroll = {
  toBottom: el => { if (el) el.scrollTop = el.scrollHeight; }
};

// US-5: remember only the conversation id across reloads (BR-1: never message text).
// localStorage can throw (private mode, storage disabled); treat that as "nothing saved".
window.chatStore = (() => {
  const key = 'chatbot.conversationId';
  return {
    key,
    get: () => { try { return localStorage.getItem(key); } catch { return null; } },
    set: id => { try { localStorage.setItem(key, id); } catch { } },
    clear: () => { try { localStorage.removeItem(key); } catch { } }
  };
})();
