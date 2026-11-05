# Scaffold Report: US-5 Keep the conversation after reloading

Status: Implemented — all 20 US-5 tests pass · Plan: [US-5-restore-after-reload-plan.md](US-5-restore-after-reload-plan.md) · Date: 2026-11-04

## 9. Scaffold report

### File tree

```
Chatbot.Api/
  Components/Pages/Chat.razor        ✏️ Restoring property, RestoreAsync stub (NotImplementedException, not called yet), indicator placeholder + TODOs
  wwwroot/chat-keys.js               ✏️ window.chatStore { key, get, set, clear } — each throws "Not implemented"
  wwwroot/chat.css                   ✏️ .typing.restoring (centered, where the empty-state text sits)
Chatbot.Api.Tests/
  Components/ChatPageTests.cs        ✏️ 20 US-5 test stubs (Assert.Fail); FakeChatService gets Conversations, PendingConversation, ThrowOnGet, GetRequests
docs/features/plans/
  US-5-restore-after-reload-plan.md  🆕 the plan
  US-5-scaffold-report.md            🆕 this file
```

The story file and README status update are left for after implementation, as planned.

### Build and tests

- `dotnet build`: succeeded, 0 warnings, 0 errors.
- `dotnet test`: 78 total. **20 failed** (all new US-5 stubs), **58 passed** (all existing). Nothing skipped.

### TODO map

| TODO | Where | Covers |
|---|---|---|
| Render `#restore-indicator` in place of `.empty` while `Restoring` | [Chat.razor:12](../../../Chatbot.Api/Components/Pages/Chat.razor#L12) | AC5 · G5 |
| `!Restoring` in `CanSend` | [Chat.razor:77](../../../Chatbot.Api/Components/Pages/Chat.razor#L77) | AC5 · G5 |
| `chatStore.set(id)` after a successful reply | [Chat.razor:78](../../../Chatbot.Api/Components/Pages/Chat.razor#L78) | AC1, BR-1, SEC3 · G1 |
| Read + validate saved id | [Chat.razor:145](../../../Chatbot.Api/Components/Pages/Chat.razor#L145) | AC2, AC7, SEC2 · G2 |
| `Restoring` on/off around the fetch | [Chat.razor:146](../../../Chatbot.Api/Components/Pages/Chat.razor#L146) | AC5 · G5 |
| Fill messages, set id, scroll | [Chat.razor:147-148](../../../Chatbot.Api/Components/Pages/Chat.razor#L147-L148) | AC2, AC3 · G2, G3 |
| Not found → clear | [Chat.razor:149](../../../Chatbot.Api/Components/Pages/Chat.razor#L149) | AC4 · G4 |
| Exception → log id only, keep id | [Chat.razor:150](../../../Chatbot.Api/Components/Pages/Chat.razor#L150) | AC6, SEC4 · G6 |
| Call `RestoreAsync` on first render | [Chat.razor:156](../../../Chatbot.Api/Components/Pages/Chat.razor#L156) | AC2 · G2 |
| `chatStore.get/set/clear` bodies | [chat-keys.js:15-19](../../../Chatbot.Api/wwwroot/chat-keys.js#L15-L19) | AC1, AC2, AC4, AC7 |
| Fake service uses the new properties | [ChatPageTests.cs:856](../../../Chatbot.Api.Tests/Components/ChatPageTests.cs#L856) | G2–G6 |

### Suggested first test

`US5_AC1_AfterReply_IdIsSaved` (Group 1 baseline): the smallest change, one `chatStore.set` call after a reply.

## 10. Verification

| # | Check | Result |
|---|---|---|
| V1 | Only planned files changed (plus the plan and this report) | ✅ Chat.razor, chat-keys.js, chat.css, ChatPageTests.cs. Other diffs in `git status` (US-4 docs, `.skill` files) predate this scaffold. |
| V2 | Endpoints match 4.2 | ✅ none added |
| V3 | DTOs match 4.3 | ✅ none changed; storage key `chatbot.conversationId` in `chatStore.key` |
| V4 | Migration | ✅ none, as planned |
| V5 | Security wiring | ✅ GUID validation, id-only storage and id-only logging are TODOs (they're logic) |
| V6 | Planned tests exist | ✅ planned 20 / found 20, names match §7 |
| V7 | No logic leaked | ✅ only properties, comments, CSS and not-implemented throws; `RestoreAsync` is not called yet, so existing behavior is unchanged |
| V8 | Build passes; new tests fail; existing pass | ✅ 0 warnings · 20 failed / 58 passed |

User checklist:

- ☐ File locations and names look right (`Restoring`, `RestoreAsync`, `window.chatStore`)
- ☐ `#restore-indicator` id, text "Loading conversation…", and its spot (in place of the empty-state text) are final
- ☐ Storage key `chatbot.conversationId` is final
- ☐ The test list is complete — any missing case?
- ☐ The TODO map covers all the work

Verified by the user on 2026-11-04.

## 11. Implementation report

### Files changed

| File | Change |
|---|---|
| [Chat.razor](../../../Chatbot.Api/Components/Pages/Chat.razor) | `RestoreAsync` (read id → validate → fetch → fill or clear), called once on first render; `!Restoring` in `CanSend`; `chatStore.set` after each successful reply; `#restore-indicator` in place of the empty-state text |
| [chat-keys.js](../../../Chatbot.Api/wwwroot/chat-keys.js) | `window.chatStore` get/set/clear on `localStorage` key `chatbot.conversationId`; storage errors are swallowed (treated as "nothing saved") |
| [chat.css](../../../Chatbot.Api/wwwroot/chat.css) | `.typing.restoring` (from the scaffold) |
| [ChatPageTests.cs](../../../Chatbot.Api.Tests/Components/ChatPageTests.cs) | 20 US-5 tests + helpers (`SavedId`, `Convo`, `RenderRestored`, `StartRestoring`, `Calls`); `FakeChatService.GetConversationAsync` now uses `Conversations`, `PendingConversation`, `ThrowOnGet` and records `GetRequests` |
| [US-5 story](../user-story/US-5-restore-after-reload.md), [README](../user-story/README.md) | status → implemented; AC-6, AC-7 added; known limitations A-1 (id is the only key, D3) and A-2 (no paging) |

### Test results

- `dotnet build`: 0 warnings, 0 errors.
- `dotnet test`: **78 passed, 0 failed** (20 new US-5 + 58 existing).
- First red run: 16 of 20 failed. The other 4 are "nothing happens" contrasts (`FreshPage_NothingSaved`, `FailedSend_NothingSaved`, `NoSavedId_NoFetch`, `NoSavedId_NoIndicator`) that are true before any logic exists; the mutation check below shows the logic is still pinned by other tests.

### Mutation check

Each change was applied alone, tests run, then reverted.

| Mutation | Result |
|---|---|
| Remove `!Restoring` from `CanSend` | ❌ 2 tests fail (G5) |
| Don't clear an invalid saved id | ❌ 1 test fails (`US5_AC7_…`) |
| Don't keep the restored conversation id | ❌ 1 test fails (`US5_AC3_AfterRestore_…`) |

### Coverage

| AC / risk | Tests | Status |
|---|---|---|
| AC1, BR-1, SEC3 | G1 (5) | ✅ |
| AC2 | G2 (4) | ✅ |
| AC3 | G3 (2) | ✅ |
| AC4 | G4 (2) | ✅ |
| AC5 | G5 (4) | ✅ |
| AC6, SEC4 | G6 (1) | ✅ |
| AC7, SEC2 | G2 `US5_AC7_…` | ✅ |
| SEC1 | S1 (1) | ✅ |
| SEC5 | — | accepted limitation (D3), noted in the story |

### Plan revisions

| # | Change vs plan | Why |
|---|---|---|
| R1 | On a restore error, `_conversationId` is set to the saved id, so the next send continues that conversation | Matches the D2 choice ("Keep it", including "if the user sends meanwhile, the message continues that hidden conversation"). G6 asserts it. |
| R2 | Reading the saved id is wrapped: a JS/interop failure is logged and treated as "nothing saved" | Not in the plan; prevents a broken `localStorage` from crashing the page on load |
| R3 | `chatStore` swallows storage exceptions in the browser | Private-mode / disabled storage should not break chatting |

### Not tested automatically

- Real `localStorage` in a browser (bUnit mocks JS interop). Manual check: send a message, reload, and the chat comes back; in DevTools set `localStorage['chatbot.conversationId']` to a random GUID, reload, and the chat starts empty with the key removed.

### Browser check (2026-11-04)

Run against the real app (`dotnet run`, http://localhost:5008) in headless Edge via Playwright:

| Check | Result |
|---|---|
| Fresh page: nothing saved | ✅ `chatbot.conversationId` = null |
| Send → reply: id saved | ✅ id saved, matches the conversation |
| Reload: history restored, same id | ✅ both messages back, same labels and order |
| Unknown GUID → reload | ✅ empty chat, key removed, no error shown |
| Tampered value `not-a-guid` → reload | ✅ empty chat, key removed |
| Browser console | Only a 404 for `/favicon.ico` (pre-existing, unrelated) |

