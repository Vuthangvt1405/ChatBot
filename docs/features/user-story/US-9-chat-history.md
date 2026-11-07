# Epic: Chat history

> Feature: [Chatbot web UI](../chat-web-ui.md) · Stack: FastAPI chat page ([index.html](../../../app/templates/index.html) + [chat.js](../../../app/static/chat.js)), which posts to `/ui/send`

**Raw requirement:** "i want show history of all chat and load again to continue"

## Requirement Analysis

| Item | Finding |
|---|---|
| Actors | Visitor (anonymous, no login) |
| Goals | See a list of earlier chats; open one and keep chatting in it |
| Business value | *(assumed)* Visitors can come back to an earlier topic instead of repeating it, which saves time and tokens |
| Rules & constraints | Stated: "all chat", "load again to continue". Code: no login, `Conversation` has no owner; `Title` = first message, max 60 chars (`build_title` in [base.py](../../../app/services/base.py)); the browser saves only the **current** conversation id (US-5) |
| Data involved | `Conversation` (Id, Title, CreatedAt), `Message` (Role, Content, CreatedAt); `chatStore` in localStorage |
| Ambiguities | **"all chat" = whose chats?** With no login, "all conversations in the database" would show every visitor's chats to everyone. This draft assumes **"all chats started in this browser"** (Q1). Also: sort order, how many to show, delete/rename (not stated) |

## Estimation Log

| Candidate story | Complexity | Uncertainty | Effort | Points | Action |
|---|---|---|---|---|---|
| Show history and continue a past chat | Medium | Medium | High | 8–13 | ✂️ Split by workflow step → US-9 + US-10 |
| ↳ US-9: Show my past chats in the sidebar | Medium | Medium | Medium | 5 | ✅ Keep |
| ↳ US-10: Open a past chat and continue it | Medium | Low | Low | 3 | ✅ Keep (reuses US-5 restore) |

## Ticket Structure

```
Epic: Chat history  (total: 8 points)
├── US-9:  List my past chats in the sidebar        (5 pts, Should, depends on: US-7 sidebar)
└── US-10: Open a past chat and continue chatting   (3 pts, Should, depends on: US-9)
```

---

## US-9 List my past chats in the sidebar

**Summary:** List this browser's past chats in the sidebar, newest first
**Type:** Story | **Epic:** Chat history | **Priority:** Should | **Labels:** chat-ui, history | **Components:** Web UI
**Story points (suggested):** 5 — Complexity M, Uncertainty M, Effort M — new list UI, browser now keeps several ids, needs titles from the server
**Status:** Drafted, to confirm

### User Story
As a **visitor**, I want **to see a list of the chats I started in this browser**, so that **I can find an earlier topic again**.

### Background
Today the browser remembers only the current chat (US-5). After "New chat" (US-7), the old chat can't be reached again even though it's still in the database. The sidebar from US-7 has room for a list.

### Acceptance Criteria
**AC-1 — Past chats are listed**
Given I have had 3 chats in this browser
When I open the page
Then the sidebar lists 3 items under "New chat", each showing the chat's title

**AC-2 — Newest first**
Given several chats
Then the list is ordered by last message time, newest at the top *(assumption, Q3)*

**AC-3 — New chat appears after its first reply**
Given I click "New chat" and send a message
When the reply arrives
Then the new chat appears at the top of the list; before the first reply, nothing is added

**AC-4 — Current chat is highlighted**
Given I'm in one of the listed chats
Then that item is visibly marked as active (and has `aria-current="true"`)

**AC-5 — Empty state**
Given I have never chatted in this browser (or the saved list is empty/invalid)
Then the list shows "No chats yet" and no error

**AC-6 — Missing chats are dropped**
Given a saved chat no longer exists on the server
Then it is not shown, and it is removed from the saved list

**AC-7 — Only my chats, shown safely**
Given chats from other browsers exist in the database
Then my list never shows them; titles are shown as plain text (HTML is not rendered)

**AC-8 — List load failure**
Given the server can't be reached while loading the list
Then the sidebar shows "Couldn't load your chats" and the current chat still works

### Developer Notes
- **Context & intent:** there is no login, so "mine" can only mean "ids this browser saved". Never add an endpoint that lists all conversations: that would expose every visitor's chats.
- **Affected areas (likely):** `store` in `app/static/chat.js` (keep a list of ids, not one), the sidebar in `index.html` / `chat.js`, and a way to fetch titles for several ids at once (avoid one call per chat).
- **Data:** store **ids only** in localStorage, never message text (US-5 BR-1). Titles come from the server (`Conversation.Title`, max 60 chars).
- **Edge cases:** the localStorage key changes from one id to a list; the existing single saved id from US-5 should be carried over, not lost. Tampered or non-GUID values are ignored (like US-5 AC7).
- **Security:** ids are unguessable GUIDs and act as the "key" to a chat. Don't log titles or message text.
- **Testing hints:** bUnit with `FakeChatService` and `chatStore` JS stubs, as in US-5/US-7.

### Out of Scope
- Showing chats from other browsers/devices (needs login)
- Search, rename, delete, pin, folders
- Paging / infinite scroll *(assumption: cap at 50, Q4)*
- Opening a chat from the list (US-10)

### Dependencies
- US-7 (sidebar), US-5 (saved id, restore)

### Open Questions
- [ ] Q1: "All chat" means chats started **in this browser**, not every chat in the database? (@PO)
- [ ] Q2: Should the list survive clearing browser data? (If yes, it needs login, which is a separate epic.) (@PO)
- [ ] Q3: Sort by last message time, or by when the chat was created? (@PO)
- [ ] Q4: Max number of chats in the list: 50? (@PO)
- [ ] Q5: Show a date/time next to each title? (@PO / design)

---

## US-10 Open a past chat and continue chatting

**Summary:** Open a past chat from the sidebar and continue the conversation
**Type:** Story | **Epic:** Chat history | **Priority:** Should | **Labels:** chat-ui, history | **Components:** Web UI
**Story points (suggested):** 3 — Complexity M, Uncertainty L, Effort L — reuses US-5 restore and US-7 busy rules
**Status:** Drafted, to confirm

### User Story
As a **visitor**, I want **to open a chat from my history and keep writing in it**, so that **I can pick up an earlier topic with its full context**.

### Background
US-5 can already load a chat's messages after a reload. This story lets the visitor choose which chat to load, then continue it as the current chat.

### Acceptance Criteria
**AC-1 — Open shows the full chat**
Given my list has "Trip to Japan"
When I click it
Then all its messages appear in order, and it becomes the active item

**AC-2 — Continue in the same chat**
Given I opened "Trip to Japan"
When I send a message
Then it's sent with that chat's `conversationId`, and the reply continues the same conversation

**AC-3 — Reload keeps the opened chat**
Given I opened a past chat
When I reload
Then that chat is restored (not the one I was in before)

**AC-4 — Clean switch**
Given I have unsent text, an error, or a "Not sent" message in the current chat
When I open another chat
Then the input is empty, and no error or "Not sent" message carries over

**AC-5 — Loading state**
Given I clicked a chat
While its messages load
Then "Loading conversation…" shows and sending is blocked

**AC-6 — Blocked while busy**
Given a reply is on its way or a chat is loading
Then the history items can't be clicked, so a late reply can't land in another chat

**AC-7 — Chat no longer exists**
Given the clicked chat was deleted on the server
Then I see "This conversation no longer exists.", it is removed from the list, and my current chat is kept

**AC-8 — Load fails**
Given the server can't be reached when I click a chat
Then I see "Couldn't open this chat. Please try again." and my current chat is kept *(assumption)*

### Developer Notes
- **Context & intent:** behave like US-5 restore, but triggered by a click. Reuse its loading indicator, plus US-6 error texts and US-7 busy rules, instead of new versions.
- **Affected areas (likely):** `chat.js` (click handler, active id), `store` (set current id). The existing `GET /api/chat/{id}/messages` / `get_conversation` should be enough.
- **Edge cases:** clicking the chat that's already open (no reload needed *(assumption)*), fast clicks on two chats (only the last one should win).
- **Security:** only ids from this browser's list are opened; message text is shown as plain text (as today).

### Out of Scope
- Delete or rename from the list
- Opening a chat by pasting a link or id
- Moving messages between chats

### Dependencies
- US-9 (the list)

### Open Questions
- [ ] Q6: On AC-7/AC-8, keep the current chat (draft default), or switch to an empty chat? (@PO)
- [ ] Q7: Clicking the chat that's already open: do nothing, or reload it from the server? (@PO)

---

## Open Questions (all stories)
1. Q1: "All chat" = chats started in **this browser** only? (Recommended; anything wider needs login.)
2. Q2: Must history survive clearing browser data / another device? (If yes → login epic first.)
3. Q3: Sort by last message time or by created time?
4. Q4: Max chats in the list: 50?
5. Q5: Show a date/time next to each title?
6. Q6: If opening a chat fails, keep the current chat?
7. Q7: Clicking the already-open chat: do nothing?
