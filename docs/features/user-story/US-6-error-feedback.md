# US-6 Clear feedback on failure

> Feature: [Chatbot web UI](../chat-web-ui.md) · Stack assumption: plain HTML + JS served from `wwwroot` at `/`

- **Priority:** Must
- **Status:** AC drafted, not yet confirmed

**Story:** As a visitor, I want clear feedback when something fails, so that I can retry without retyping.

## Acceptance Criteria

- **AC-1 Assistant unavailable (502)**
  Given the API returns 502
  Then an error shows "The assistant is unavailable right now. Please try again."
- **AC-2 Conversation not found (404)**
  Given I send with a `conversationId` and the API returns 404
  Then an error says the conversation no longer exists and offers to start a new chat (US-7)
- **AC-3 Network failure**
  Given the API cannot be reached
  Then an error shows "Can't reach the server. Check your connection and try again."
- **AC-4 Text is kept for retry**
  Given any send fails
  Then my message text is back in the input (or a Retry button resends it), so I don't retype it
- **AC-5 Failed message is not shown as delivered**
  Given a send fails
  Then no assistant reply is added and my message is marked as not sent
- **AC-6 Error clears on success**
  Given an error is showing
  When the next send succeeds
  Then the error is removed

## Business rules

- BR-1 Raw server errors or stack traces are never shown to the visitor.
