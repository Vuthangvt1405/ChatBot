# US-8 Show replies as plain text

> Feature: [Chatbot web UI](../chat-web-ui.md) · Stack assumption: plain HTML + JS served from `wwwroot` at `/`

- **Priority:** Must
- **Status:** AC drafted, not yet confirmed

**Story:** As the site owner, I want replies shown as plain text, so that a reply can't inject markup or scripts into the page.

## Acceptance Criteria

- **AC-1 HTML is shown literally**
  Given the reply is `<b>hi</b>`
  Then the page shows the text `<b>hi</b>`, not bold "hi"
- **AC-2 Scripts never run**
  Given the reply is `<img src=x onerror=alert(1)>` or contains `<script>`
  Then no script runs and the text shows literally
- **AC-3 Same for user and restored messages**
  Given my own message, or a message restored via `GET /api/chat/{id}/messages`, contains HTML
  Then it is also shown as plain text
- **AC-4 Line breaks are kept**
  Given a reply contains newlines
  Then they show as line breaks

## Business rules

- BR-1 Message content is inserted with `textContent` (never `innerHTML`); line breaks via CSS `white-space: pre-wrap`.
- BR-2 Markdown is not rendered (out of scope).
