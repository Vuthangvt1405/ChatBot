# US-5 Keep the conversation after reloading

> Stack: Blazor Server page ([Chat.razor](../../../Chatbot.Api/Components/Pages/Chat.razor)) + `window.chatStore` in [chat-keys.js](../../../Chatbot.Api/wwwroot/chat-keys.js) · Plan: [US-5 plan](../plans/US-5-restore-after-reload-plan.md)

- **Priority:** Should
- **Status:** Confirmed, implemented

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
- **AC-6 Restore failure doesn't break the page**
  Given restoring fails for a reason other than "not found"
  Then the page shows an empty chat, the indicator clears, Send works, and the saved id is kept (the next message continues that conversation)
- **AC-7 Tampered saved value**
  Given the saved value is not a valid id
  Then nothing is fetched, the value is cleared, and the page starts fresh

## Business rules

- BR-1 Only the `conversationId` is stored in the browser; message content always comes from the API.

## Known limitations

- A-1 There are no accounts, so the conversation id is the only key: anyone who has it can read the conversation (`GET /api/chat/{id}/messages`). Accepted for now; GUIDs are not guessable.
- A-2 The whole history loads at once (no paging).
