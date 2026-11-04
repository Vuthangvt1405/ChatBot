// Stop Enter from adding a newline in the chat box; Blazor's @onkeydown does the send.
// Shift+Enter keeps the default (new line).
document.addEventListener('keydown', e => {
  if (e.target.id === 'chat-input' && e.key === 'Enter' && !e.shiftKey) e.preventDefault();
});

// Scroll the message list to the newest message (US-2 AC-4).
window.chatScroll = {
  toBottom: el => { if (el) el.scrollTop = el.scrollHeight; }
};
