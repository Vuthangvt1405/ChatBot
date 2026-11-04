# US-1 Send a message and see the reply

> Feature: [Chatbot web UI](../chat-web-ui.md) · Stack assumption: plain HTML + JS served from `wwwroot` at `/`

- **Priority:** Must
- **Status:** Implemented

**Story:** As a visitor, I want to send a message and see the assistant's reply, so that I can get answers.

## Acceptance Criteria

- **AC-1 Send and receive**
  Given the chat page is open and the API is reachable
  When I type "Hello" and click Send
  Then "Hello" appears as my message, and the assistant's `reply` from `POST /api/chat` appears below it as an assistant message
- **AC-2 Messages are visually distinct and in order**
  Given I have sent a message and received a reply
  Then my message is aligned right and labelled "You", the reply is aligned left and labelled "Assistant", and they show in send order
- **AC-3 Enter sends, Shift+Enter adds a new line**
  Given I am typing in the input
  When I press Enter
  Then the message is sent
  But when I press Shift+Enter, a new line is added and nothing is sent
- **AC-4 Input resets after a successful send**
  Given the reply has arrived
  Then the input is empty and keeps focus, so I can type the next message
- **AC-5 Message text is trimmed**
  Given I type "  Hello  "
  When I send it
  Then the request body `message` is "Hello"

## Business rules

- BR-1 The request body is `{ "message": "<trimmed text>" }`. `conversationId` is handled in US-2.
