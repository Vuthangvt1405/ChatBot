# US-7 Start a new chat

> Feature: [Chatbot web UI](../chat-web-ui.md) · Stack assumption: plain HTML + JS served from `wwwroot` at `/`

- **Priority:** Should
- **Status:** AC drafted, not yet confirmed

**Story:** As a visitor, I want to start a new chat, so that I can change topic with a clean context.

## Acceptance Criteria

- **AC-1 New chat clears the page**
  Given I have an active conversation
  When I click "New chat"
  Then the message list is empty, the input is empty and focused, and any error is cleared
- **AC-2 New chat forgets the old id**
  Given I clicked "New chat"
  Then the active and saved `conversationId` are cleared
  And my next message is sent without `conversationId`, creating a new conversation
- **AC-3 Reload after new chat stays empty**
  Given I clicked "New chat" and sent nothing
  When I reload
  Then the old conversation is not restored
- **AC-4 Disabled while waiting**
  Given a request is in flight
  Then "New chat" is disabled, so a late reply can't land in the new chat
