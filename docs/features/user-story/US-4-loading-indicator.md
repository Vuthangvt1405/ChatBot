# US-4 Show that the assistant is working

> Feature: [Chatbot web UI](../chat-web-ui.md) · Stack assumption: plain HTML + JS served from `wwwroot` at `/`

- **Priority:** Should
- **Status:** AC drafted, not yet confirmed

**Story:** As a visitor, I want to see that the assistant is working, so that I know to wait and don't send twice.

## Acceptance Criteria

- **AC-1 Typing indicator while waiting**
  Given I have sent a message
  While the request is in flight
  Then an "Assistant is typing…" indicator shows below my message
- **AC-2 No double send**
  Given a request is in flight
  When I click Send or press Enter
  Then no second request is made (Send is disabled)
- **AC-3 Indicator clears when done**
  Given a request is in flight
  When it succeeds or fails
  Then the indicator is removed and Send is enabled again (if the input is valid)
- **AC-4 I can keep typing while waiting**
  Given a request is in flight
  Then the input stays editable so I can draft my next message
