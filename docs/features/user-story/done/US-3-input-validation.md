# US-3 Block invalid messages

> Feature: [Chatbot web UI](../../chat-web-ui.md) · Stack: FastAPI chat page ([index.html](../../../../app/templates/index.html) + [chat.js](../../../../app/static/chat.js)), which posts to `/ui/send`

- **Priority:** Must
- **Status:** Implemented 2026-11-04 (AC-5 dropped; see [chat-web-ui.md §9](../../chat-web-ui.md#9-us-3-block-invalid-messages))

**Story:** As a visitor, I want to be stopped from sending invalid messages, so that I don't waste a request or get a confusing error.

## Acceptance Criteria

- **AC-1 Empty message cannot be sent**
  Given the input is empty or only whitespace
  Then the Send button is disabled
  And pressing Enter (or submitting) sends nothing and `IChatService` is not called
- **AC-2 Over-length message cannot be sent**
  Given the trimmed input is longer than 4000 characters
  Then Send is disabled, Enter sends nothing, `IChatService` is not called
  And the message "Message must be 4000 characters or fewer" is shown
  And the typed text stays in the input
  And when the text is shortened to 4000 or fewer, the message disappears and Send is enabled again
- **AC-3 Exactly 4000 characters is allowed**
  Given the trimmed input is exactly 4000 characters (with or without extra leading/trailing spaces)
  Then Send is enabled and the message is sent
- **AC-4 Character counter**
  Given the input is not empty
  Then a counter shows `n / 4000`, where n is the trimmed length
  And it switches to a warning style when n is above 4000
  And it is hidden when the input is empty
- ~~**AC-5 Server-side 400 is still handled**~~ Dropped: the page doesn't call the HTTP API, so it can't receive a 400. The check in `SendAsync` already runs on the server (Blazor Server), and AC-1/AC-2 cover it.

## Business rules

- BR-1 Length is measured on the trimmed text, matching what is sent (US-1 AC-5).
- BR-2 Allowed length: 1 to 4000 characters, same as `POST /api/chat`.

## Assumptions

- A-1 "Characters" means .NET `string.Length` (UTF-16 code units), the same as the API's `[MaxLength(4000)]`. An emoji may count as 2.
- A-2 The textarea has no hard `maxlength`, so pasted text isn't silently cut off. The user sees the warning and edits the text instead.
- A-3 The validation message replaces the "Enter to send" hint line while it is shown.
- A-4 Disabling Send while a reply is pending belongs to US-4, not this story.
