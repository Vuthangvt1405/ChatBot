# STORY-01: Interactive pair-coding workspace for dataset engineering

[← Back to Sprint Backlog](./README.md) | [Epic PRD](../../requirements/pair-coding-eda-assistant/README.md)

**Summary:** Interactive pair-coding workspace for dataset engineering  
**Type:** Story | **Epic:** Pair-Coding AI Assistant with Deep EDA for Dataset Engineering | **Priority:** Highest | **Labels:** `pair-coding`, `eda-workspace`, `ui` | **Components:** `Frontend`, `Agent-Service`  
**Story points (suggested):** 5 — Complexity [Medium], Uncertainty [Low], Effort [Medium] — Collaborative split-view UI combining chat prompt interaction with live dataset inspection and EDA metrics.

---

### User Story
As an **AI Engineer**, I want **a split-view pair-coding interface where I can chat with the dataset agent while simultaneously inspecting live data and EDA metrics**, so that **I can iteratively explore and curate my datasets collaboratively**.

### Background
Switching between chat interfaces, Jupyter notebooks, and raw CSV files fractures the dataset creation workflow. A unified pair-coding workspace gives the engineer direct visibility into data samples and diagnostic charts while guiding the assistant via chat.

### Acceptance Criteria

**AC1 — Split-view workspace layout**  
Given an AI Engineer opens an active dataset project  
When the workspace loads  
Then the interface displays a split-pane layout: conversational pair-coding assistant on the left (40% width) and an interactive EDA data viewer on the right (60% width), with a draggable divider.

**AC2 — Context-aware chat prompts**  
Given the user asks a question about the active dataset in chat (e.g., *"Show me summary statistics for token lengths"*)  
When the message is submitted  
Then the assistant receives the active dataset metadata (sample count, columns, current filter state) and returns an analytical explanation paired with metric cards in the chat stream.

**AC3 — Synchronized selection between chat and data viewer**  
Given the assistant references a specific cluster or subset in chat  
When the engineer clicks the referenced subset link (e.g., `"View Cluster #3"`)  
Then the right-hand data viewer automatically filters to show only the samples in that cluster within 250 ms.

**AC4 — Code snippet and recipe execution prompt**  
Given the assistant proposes an exploratory Python script or filter expression  
When the engineer clicks "Run Analysis" on the code block  
Then the backend executes the analysis non-destructively and renders the resulting chart/table in the EDA panel.

**AC5 — Session persistence**  
Given an active pair-coding session with chat messages and EDA outputs  
When the user refreshes the page or returns later  
Then the conversation history, executed metrics, and active filter views are fully restored.

### Developer Notes
- **Context & Intent**: Emulates the developer experience of pairing with a senior data scientist.
- **Affected Areas**: `PairCodingWorkspace`, `ChatInterface`, `EDAInspectorPane`, `SessionStateService`.
- **Data & Fields**:
  - `session_id`: UUIDv4
  - `dataset_id`: UUIDv4
  - `history`: array of `{role: string, content: string, attachments?: array, timestamp: string}`
  - `active_view_state`: object (filters, selected cluster, active tab).
- **Non-Functional**: UI state sync must happen with p95 latency < 300 ms.

### Out of Scope
- Multi-user collaborative pair-coding (two engineers typing in the same chat at once).

### Dependencies
- None.

### Open Questions
- None.
