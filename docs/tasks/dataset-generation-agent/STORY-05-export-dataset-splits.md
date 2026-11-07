# STORY-05: Export dataset directly in JSONL and CSV with splits

[← Back to Sprint Backlog](./README.md) | [Epic PRD](../../requirements/dataset-generation-agent/README.md)

**Summary:** Export dataset directly in JSONL and CSV with splits  
**Type:** Story | **Epic:** AI-Assisted Dataset Generation & Curation Platform | **Priority:** High | **Labels:** `export`, `download`, `packaging` | **Components:** `Export-Service`, `Frontend`  
**Story points (suggested):** 3 — Complexity [Low], Uncertainty [Low], Effort [Low] — Formats samples into JSONL/CSV, calculates train/val/test partitions, and delivers a downloadable `.zip`.

---

### User Story
As an **AI Engineer**, I want **to immediately export my generated dataset into JSONL or CSV formatted files with train/validation/test splits**, so that **I can download a `.zip` archive and load it directly into training or evaluation pipelines**.

### Background
Once generation finishes, engineers need immediate file downloads partitioned cleanly (e.g., 80% train, 10% validation, 10% test) formatted according to industry conventions (OpenAI/Hugging Face JSONL).

### Acceptance Criteria

**AC1 — Direct export trigger from job dashboard**  
Given a dataset job with at least 1 `READY` sample  
When the AI Engineer clicks "Export Dataset"  
Then an export dialog appears with format selection (`JSONL`, `CSV`) and split sliders (default: Train 80%, Validation 10%, Test 10%).

**AC2 — Split ratio validation**  
Given the split configuration controls  
When the sum of Train + Validation + Test does not equal exactly 100%  
Then the modal disables the download button and displays: `"Splits must sum to exactly 100%."`

**AC3 — Download `.zip` archive containing partitioned files**  
Given valid export settings are confirmed  
When the user clicks "Download Archive"  
Then the system partitions all `READY` samples (omitting `EXCLUDED` samples), generates separate files (e.g., `train.jsonl`, `val.jsonl`, `test.jsonl`), and serves a `.zip` file download named `<dataset_name>_export.zip`.

**AC4 — Appropriate JSONL structure based on mode**  
Given the user selects `JSONL` export  
When the files are packaged:
- If Training mode: rows adhere to standard prompt/completion or chat `{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}` format *(dev decision)*.
- If Evaluation mode: rows adhere to `{"prompt": "...", "reference_answer": "...", "criteria": "..."}`.

**AC5 — Empty dataset guard**  
Given a job has 0 `READY` samples (e.g., all were excluded)  
When the user views the export action  
Then the "Export Dataset" button is disabled with tooltip: `"No ready samples available for export."`

### Developer Notes
- **Context & Intent**: Fast, reliable download bundle creation directly in the browser session.
- **Affected Areas**: `DatasetExportModal`, `PartitionService`, `ZipStreamHelper`.
- **Dev Decisions**:
  - Shuffle: Apply a random shuffle before partitioning splits to avoid ordering bias from seed documents.
  - Performance: Stream zip generation using in-memory / temporary spooling for datasets up to 10,000 samples.

### Out of Scope
- Direct push to external cloud storage (S3 / GCS) or Hugging Face Hub.

### Dependencies
- Story 3 (Samples generated with `READY` status).

### Open Questions
- None.
