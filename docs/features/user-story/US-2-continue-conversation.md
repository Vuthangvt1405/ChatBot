# US-2 Keep chatting in the same conversation

> Feature: [Chatbot web UI](../chat-web-ui.md) · Stack assumption: plain HTML + JS served from `wwwroot` at `/`

- **Priority:** Must
- **Status:** Implemented

**Story:** As a visitor, I want to keep chatting in the same conversation, so that the assistant remembers the context.

## Acceptance Criteria

- **AC-1 First message starts a conversation**
  Given no conversation is active
  When I send my first message
  Then the request has no `conversationId`, and the page stores the `conversationId` returned in the response
- **AC-2 Follow-up messages reuse the conversation**
  Given a conversation is active with id "abc"
  When I send another message
  Then the request body is `{ "conversationId": "abc", "message": "<trimmed text>" }`
- **AC-3 History stays on screen**
  Given I have exchanged several messages
  When I send another one
  Then earlier messages stay visible in order and the new pair is added at the bottom
- **AC-4 Auto-scroll to latest**
  Given the message list is taller than the view
  When a new message or reply is added
  Then the list scrolls to show the newest message

## Business rules

- BR-1 The active `conversationId` always comes from the latest API response; the client never generates one.
