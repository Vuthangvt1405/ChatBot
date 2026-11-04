# US-4 Show that the assistant is working

> Feature: [Chatbot web UI](../chat-web-ui.md) · Stack: Blazor Server page `Components/Pages/Chat.razor` (Radzen), which calls `IChatService` directly

- **Priority:** Should
- **Status:** AC confirmed 2026-11-04, scaffolded (see [plan](../plans/US-4-loading-indicator-plan.md))

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
- **AC-5 Server-side guard**
  Given a request is in flight
  When the form is submitted anyway (e.g. `disabled` removed in devtools)
  Then no second request is made
- **AC-6 No indicator without a send**
  Given a fresh page, or a send blocked by US-3 validation
  Then no indicator shows
- **AC-7 Draft is kept**
  Given I typed a new draft while waiting
  When the reply arrives
  Then my draft is not wiped (the input clears only if it still holds the sent text)

## Assumptions

- A-1 On failure the indicator clears and the text stays in the input, but no error message shows yet (US-6).
