# Sprint Backlog: AI-Assisted Dataset Generation Platform

**Epic PRD:** [`docs/requirements/dataset-generation-agent/README.md`](../../requirements/dataset-generation-agent/README.md)  
**Product Owner:** Antigravity (PO Persona)  
**Total Story Points:** 26 pts | **Sprint Status:** Ready for Development

This folder contains the **User Stories that developers need to do right now** to build the dataset generation platform.

---

## Ready-to-Do User Stories (Priority Order)

| Ticket | Points | Priority | Summary | File Link |
|---|---|---|---|---|
| **STORY-01** | 5 pts | High | Configure dataset generation task for training and evaluation | [📄 `STORY-01-configure-dataset-task.md`](./STORY-01-configure-dataset-task.md) |
| **STORY-02** | 5 pts | High | Upload and extract seed documents for dataset generation | [📄 `STORY-02-upload-seed-documents.md`](./STORY-02-upload-seed-documents.md) |
| **STORY-03** | 8 pts ⚠️ | Highest | Generate synthetic sample batches from prompt and seed files | [📄 `STORY-03-generate-synthetic-batches.md`](./STORY-03-generate-synthetic-batches.md) |
| **STORY-04** | 5 pts | Medium | Inspect, edit, and curate generated dataset samples | [📄 `STORY-04-inspect-curate-samples.md`](./STORY-04-inspect-curate-samples.md) |
| **STORY-05** | 3 pts | High | Export dataset directly in JSONL and CSV with splits | [📄 `STORY-05-export-dataset-splits.md`](./STORY-05-export-dataset-splits.md) |

---

## Dependency & Execution Flow

```text
STORY-01: Task Configuration (5 pts)
    │
    ├──► STORY-02: Seed Document Upload & Parsing (5 pts)
    │        │
    │        └──► STORY-03: Batch Synthesis & Auto-Readiness (8 pts ⚠️)
    │                 │
    │                 ├──► STORY-04: Optional Sample Curation (5 pts)
    │                 │
    │                 └──► STORY-05: Direct Export with Splits (3 pts)
```
