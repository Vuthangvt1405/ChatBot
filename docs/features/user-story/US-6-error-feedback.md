# US-6 Clear feedback on failure

> Feature: [Chatbot web UI](../chat-web-ui.md) · Stack: Blazor Server page ([Chat.razor](../../../Chatbot.Api/Components/Pages/Chat.razor)) + HTTP API · Plan: [US-6 plan](../plans/US-6-error-feedback-plan.md)

- **Priority:** Must
- **Status:** AC confirmed (2026-11-05), not implemented

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
- **AC-7 A failed send isn't saved**
  Given a send fails
  Then the server has not stored my message (or a new empty conversation), so a reload doesn't show it as delivered and a retry doesn't store it twice
- **AC-8 Provider timeouts and outages count as "unavailable"**
  Given the AI provider times out, can't be reached, or returns unreadable data
  Then I see the AC-1 message, and the HTTP API returns 502
- **AC-9 A draft is never overwritten**
  Given I typed new text while the reply was pending
  When the send fails
  Then my new text stays in the input, and the failed text is still visible in the "not sent" message
- **AC-10 Unknown errors get a general message**
  Given a send fails for any other reason (e.g. the database is down)
  Then an error shows "Something went wrong. Please try again."
- **AC-11 The HTTP API always answers with a safe error**
  Given any error happens while handling `/api/*`
  Then the response is ProblemDetails JSON (404 not found, 502 provider error, 500 anything else with detail "Something went wrong. Please try again."), never exception text or a stack trace, also in Development
- **AC-12 Sending again after "not found" keeps the old id**
  Given the "conversation no longer exists" error is showing
  When I press Send instead of "Start a new chat"
  Then the message goes to the same conversation and the same error shows again

## Business rules

- BR-1 Raw server errors or stack traces are never shown to the visitor.
