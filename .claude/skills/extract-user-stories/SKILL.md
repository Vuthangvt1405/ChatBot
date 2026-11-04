---
name: extract-user-stories
description: Turn a new feature request into user stories (US) and acceptance criteria (AC), then split them into a `user-story/` folder with one Markdown file per story plus a README index. Use when the client or user describes a new feature they want ("I want...", "add X", "users should be able to...", a pasted ticket or idea), asks for user stories or AC, or asks to extract/split stories from an existing feature doc.
---

# Feature request → user stories + AC

Two possible starting points:

- **A. Raw feature request** (the client describes what they want in chat) → do Phase 1, then Phase 2.
- **B. Existing feature doc** (e.g. `docs/features/<feature>.md`) → skip to Phase 2.

## Phase 1: From request to feature doc

1. **Understand the request.** Work out the goal, who the users are, and the problem being solved.
2. **Study the context.** Look in the codebase for what already exists: API endpoints (request/response fields, limits, error codes), data models, and the existing docs in `docs/features/`. The AC must match what the system can actually do.
3. **Ask only the questions that block you.** Use AskUserQuestion for the decisions that change the stories (scope, roles, key rules), at most 1–4 questions, each with a recommended option. For everything else, choose a sensible default and record it under Assumptions.
4. **Write the feature doc** at `docs/features/<feature-kebab>.md`:

```markdown
# Feature: <Name>

- **Date:** <today>
- **Status:** Stories drafted; AC drafted

## 1. User Stories

**Goal:** <one sentence>

API available:
- <endpoint and contract, or "to be built">

| ID | Priority | Story |
|----|----------|-------|
| US-1 | Must | As a <role>, I want <goal>, so that <benefit>. |

### Out of scope
- ...

### Open questions
- ...

## 2. Acceptance Criteria
(AC per story, using the rules below)

### Assumptions
- ...
```

   Story rules: each story covers one user goal, is small enough to build on its own, and uses the format "As a / I want / so that". Priority is Must / Should / Could. Usually 4–10 stories per feature. Include the cross-cutting ones too: validation, loading, errors, security.

5. **Show the story table to the client** and ask them to confirm it before you write the files. A short summary is enough; the details go in the doc.

## Phase 2: Split into the user-story folder

1. **Read the feature doc fully**: goal, stories, API contract, out of scope, existing AC, business rules.
2. **Create** `user-story/` next to the feature doc (e.g. `docs/features/user-story/`). If several features share `docs/features/`, use `docs/features/<feature>/user-story/` so their stories don't mix.
3. **Write one file per story**: `US-<n>-<short-kebab-title>.md` (template below).
   - AC already in the doc → copy it **word for word**, status `AC in draft (from feature doc)`.
   - Otherwise → draft new AC, status `AC drafted, not yet confirmed`.
4. **Write `user-story/README.md`**, an index table linking every story.
5. **Don't change the source feature doc** in Phase 2.
6. **Report back**: a short table of each story and what its AC cover, then a list of the design choices the client should confirm (error wording, storage, UI details, and so on).

## Writing good AC

- 3–6 AC per story, each named `**AC-<n> <Short title>**`, then Given / When / Then (And / But) lines.
- Use concrete values: field names, endpoints, status codes, limits. Test the edges (max length and max+1).
- Cover the happy path, validation, edge cases, and each error the API can return.
- Each AC is testable: one observable outcome, no vague words ("fast", "nice").
- Never write AC for items that are out of scope.
- Refer to other stories instead of repeating them ("handled in US-2").
- Put cross-cutting rules under **Business rules** as `BR-<n>`.
- Wrap code, fields, and endpoints in backticks.

## Story file template

```markdown
# US-<n> <Short title>

> Feature: [<Feature name>](../<feature-doc>.md) · Stack assumption: <stack, if known>

- **Priority:** <Must | Should | Could>
- **Status:** <AC in draft (from feature doc) | AC drafted, not yet confirmed>

**Story:** As a <role>, I want <goal>, so that <benefit>.

## Acceptance Criteria

- **AC-1 <Title>**
  Given <context>
  When <action>
  Then <observable outcome>

## Business rules

- BR-1 <rule>
```

Leave out the Business rules section if a story has none.

## README template

```markdown
# User stories – <Feature name>

Source: [<feature-doc>.md](../<feature-doc>.md)

| ID | Priority | Story | AC status |
|----|----------|-------|-----------|
| [US-1](US-1-<slug>.md) | Must | <short title> | <Draft (from feature doc) / Drafted, to confirm> |
```

## Tips

- On Windows, write files with the Write tool, not bash heredocs (backticks and apostrophes break shell quoting).
- Write all the story files in parallel.
- Once the stories are confirmed, the next step is building them (the `implement-feature` skill), one story at a time.
