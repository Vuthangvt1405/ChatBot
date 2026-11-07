# TASK-01: Scaffold Pair-Coding Workspace UI

**Target Story:** [01-interactive-pair-coding-workspace.md](../../requirements/pair-coding-eda-assistant/01-interactive-pair-coding-workspace.md)  
**Priority:** Highest | **Estimate:** 3 pts | **Status:** Ready to Start

---

## Technical Goal
Implement a split-view workspace layout consisting of an interactive pair-coding chat pane (left) and a dynamic EDA data viewer/visualizer pane (right), synchronized via shared React state / WebSocket events.

---

## Files to Touch / Create
- `frontend/src/features/workspace/PairCodingWorkspace.tsx` *(new)*
- `frontend/src/features/workspace/components/ChatPane.tsx` *(new)*
- `frontend/src/features/workspace/components/EDAInspectorPane.tsx` *(new)*
- `frontend/src/features/workspace/hooks/useWorkspaceSession.ts` *(new)*
- `frontend/src/features/workspace/types.ts` *(new)*

---

## Implementation Steps

### 1. Define Workspace Types & State (`types.ts`)
```typescript
export interface WorkspaceSession {
  sessionId: string;
  datasetId: string;
  activeTab: 'overview' | 'samples' | 'clusters' | 'diagnostics';
  selectedClusterId: number | null;
  activeFilterExpression: string | null;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  edaAction?: {
    actionType: 'FILTER' | 'CLUSTER_SELECT' | 'RUN_CODE';
    payload: Record<string, unknown>;
  };
}
```

### 2. Build Split-View Container (`PairCodingWorkspace.tsx`)
- [ ] Implement a 2-column flex container with draggable resizer handle (default width 40% chat / 60% EDA panel, min 300px each).
- [ ] Manage synchronized selection: When user clicks a cluster tag or metric pill in `ChatPane`, dispatch `setSelectedClusterId(clusterId)` to update `EDAInspectorPane`.

### 3. Build Chat Pane (`ChatPane.tsx`)
- [ ] Implement virtualized or auto-scrolling message stream.
- [ ] Render code blocks with a "Run Analysis" interactive button.
- [ ] Add quick-prompt chips at the bottom: `[Run Corpus Audit]`, `[Show Diversity Clusters]`, `[Check Hallucination Risk]`.

### 4. Build EDA Inspector Skeleton (`EDAInspectorPane.tsx`)
- [ ] Tabs: `Corpus Overview`, `Sample Table`, `Clusters`, `Diagnostics`.
- [ ] Display an empty state with upload/fetch triggers if no dataset is loaded.

---

## Verification & Testing
- Run test: `npm run test -- workspace`
- Verify resizer works smoothly without layout breaking.
- Verify clicking a sample reference inside chat focuses that row in the sample table.

---

## Definition of Done
- [ ] Split-view container renders properly on standard desktop viewports (≥ 1280px).
- [ ] State updates in chat immediately propagate to inspector tabs.
- [ ] TypeScript compiles cleanly with zero type errors.
