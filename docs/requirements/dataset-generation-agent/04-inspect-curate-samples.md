# Story 4: Inspect, edit, and curate generated dataset samples

[← Back to Epic Overview](./README.md)

**Summary:** Inspect, edit, and curate generated dataset samples  
**Type:** Story | **Epic:** AI-Assisted Dataset Generation & Curation Platform | **Priority:** Medium | **Labels:** `sample-viewer`, `curation`, `ui` | **Components:** `Frontend`, `Sample-Service`  
**Story points (suggested):** 5 — Complexity [Medium], Uncertainty [Low], Effort [Medium] — Optional viewer allowing AI Engineers to search, inspect, edit, or exclude samples.

---

### User Story
As an **AI Engineer**, I want **an optional viewer to inspect, edit, or exclude generated samples**, so that **I can spot-check and fine-tune specific items if I want to improve dataset quality**.

### Background
Even when datasets do not require mandatory verification, engineers often want to spot-check a few samples, correct slight phrasing issues, or remove an outlier before training.

### Acceptance Criteria

**AC1 — Display generated samples in responsive table**  
Given a dataset job with generated samples  
When the AI Engineer opens the "Samples" tab  
Then all samples are displayed in a paginated list with Input, Output, Mode badge (Training vs. Eval), and status `READY`.

**AC2 — Inspect sample details in drawer**  
Given the samples list  
When the user clicks any row  
Then a detail drawer opens displaying full text, evaluation criteria (if in Eval mode), and source seed reference.

**AC3 — Inline edit and auto-save**  
Given a sample in the detail drawer  
When the user modifies the input, output, or evaluation criteria and clicks "Save"  
Then the sample updates, receives an `EDITED` badge, and remains in `READY` status for export.

**AC4 — Exclude sample from export**  
Given a sample that the user deems unwanted  
When the user clicks "Exclude" (or uses keyboard key `X` *(dev decision)*)  
Then the sample transitions to `EXCLUDED` status and will be omitted from export packages.

**AC5 — Keyword search and filtering**  
Given the samples table  
When the user types a keyword into the search bar  
Then the table filters within 200 ms to show only samples containing that text in either input or output.

### Developer Notes
- **Context & Intent**: This is an optional convenience tool; users can bypass this step entirely and export directly from Story 3.
- **Affected Areas**: `SampleTable`, `SampleDetailDrawer`, `SamplePatchController`.
- **Data & Fields**:
  - `status`: enum (`READY`, `EXCLUDED`)
  - `is_edited`: boolean
  - `updated_at`: UTC timestamp

### Out of Scope
- Multi-annotator grading or blind review consensus.

### Dependencies
- Story 3 (Generated samples available in repository).

### Open Questions
- None.
