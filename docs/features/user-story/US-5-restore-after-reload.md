# US-5 Keep the conversation after reloading

> Feature: [Chatbot web UI](../chat-web-ui.md) · Stack assumption: plain HTML + JS served from `wwwroot` at `/`

- **Priority:** Should
- **Status:** AC drafted, not yet confirmed

**Story:** As a returning visitor, I want my conversation to still be there after reloading, so that I don't lose my chat.

## Acceptance Criteria

- **AC-1 Conversation id is remembered**
  Given I have an active conversation
  Then its `conversationId` is saved in the browser's `localStorage`
- **AC-2 History reloads**
  Given a saved `conversationId` exists
  When I reload or reopen the page
  Then the page calls `GET /api/chat/{id}/messages` and shows all messages in order with the same "You" / "Assistant" styling
- **AC-3 Next message continues the restored conversation**
  Given the history was restored
  When I send a message
  Then the request uses the saved `conversationId`
- **AC-4 Missing conversation starts fresh**
  Given the saved id returns 404
  Then the saved id is cleared, the page shows an empty chat, and no error is shown
- **AC-5 Loading state on restore**
  Given history is being fetched
  Then a loading indicator shows and Send is disabled until it finishes

## Business rules

- BR-1 Only the `conversationId` is stored in the browser; message content always comes from the API.
