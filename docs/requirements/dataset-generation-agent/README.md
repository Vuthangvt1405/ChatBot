# Epic: AI-Assisted Dataset Generation & Curation Platform

**Epic Summary:** Build an agentic service to assist AI Engineers in creating, grounding, and packaging synthetic datasets for model fine-tuning and evaluation benchmarks.  
**Type:** Epic | **Suggested Total Points:** 26 points | **Status:** Ready for Backlog

---

## Requirement Analysis

| Item | Details |
|---|---|
| **Actors** | • **AI / ML Engineer** (primary user: uploads seed files, configures specifications, triggers generation, optionally inspects data, exports splits)<br>• **Dataset Agent / Ingestion Worker** (system actor: extracts text from seed documents, synthesizes training/eval samples, formats output) |
| **Goals** | 1. Create datasets for both **Model Training** (fine-tuning, instruction/response, chat) and **Model Evaluation** (benchmark Q&A, ground truth evaluation sets with rubrics).<br>2. Upload seed documents (PDF, Markdown, TXT, CSV) to ground the synthetic generation in proprietary domain knowledge.<br>3. Automatically mark generated samples as ready for use/export immediately upon generation, eliminating mandatory manual review gates.<br>4. Provide an optional inspection and inline editing interface to tweak samples if desired.<br>5. Export datasets directly as `.zip` packages containing partitioned JSONL and CSV files with train/validation/test splits. |
| **Business Value** | • Enables AI Engineers to produce hundreds of domain-specific training pairs or evaluation benchmarks in minutes from existing documentation.<br>• Unblocks rapid iterative fine-tuning and benchmark regression testing without manual annotation overhead.<br>• Eliminates brittle custom scraping and ad-hoc generation scripts across engineering teams. |
| **Rules & Constraints** | • Generation must support dual output schemas: Instruction Tuning format and Evaluation Benchmark format.<br>• Uploaded seed files must be validated for allowed types (`.pdf`, `.txt`, `.md`, `.csv`) and size limits (max 25 MB per file *(assumption)*).<br>• Generated samples default to `READY` status immediately upon generation (no mandatory verification step required to export).<br>• Export bundles must partition data cleanly according to user-selected split percentages without sample overlap. |
| **Data Involved** | • **Dataset Specification**: Job ID, name, target task mode (`TRAINING_INSTRUCTION`, `EVALUATION_BENCHMARK`, `CUSTOM_SCHEMA`), prompt guidelines, target sample count.<br>• **Seed Document**: Document ID, original filename, file type, file size, parsed text chunks.<br>• **Dataset Sample**: Sample ID, prompt/input, target completion/reference answer, evaluation rubric/grading criteria (if eval mode), status (`READY`, `EDITED`, `EXCLUDED`).<br>• **Export Package**: Format (JSONL, CSV), split ratios (Train / Val / Test), downloaded `.zip` artifact. |
| **Ambiguities & Assumptions** | • *Stated*: Both training and eval datasets supported; no mandatory quality verification step required before export; seed file upload enabled; direct `.zip` export (JSONL/CSV) is sufficient.<br>• *Assumed*: Seed document file size capped at 25 MB per file, up to 5 files per generation job *(assumption)*.<br>• *Assumed*: Evaluation datasets include prompt, reference answer, and optional grading criteria/rubric *(assumption)*. |

---

## Estimation Log

| Candidate story | Complexity | Uncertainty | Effort | Points | Action |
|---|---|---|---|---|---|
| Generate synthetic dataset with uploaded file grounding | High | High | High | 13 | ✂️ Split into Ingestion + Generation |
| ↳ [Story 1: Configure dataset task](./01-configure-dataset-task.md) | Medium | Low | Medium | 5 | ✅ Keep |
| ↳ [Story 2: Upload seed documents](./02-upload-seed-documents.md) | Medium | Low | Medium | 5 | ✅ Keep (new INVEST story from split) |
| ↳ [Story 3: Generate synthetic batches](./03-generate-synthetic-batches.md) | High | Medium | High | 8 | ⚠️ Keep (at limit; prompt synthesis + file grounding) |
| ↳ [Story 4: Inspect and curate samples](./04-inspect-curate-samples.md) | Medium | Low | Medium | 5 | ✅ Keep (optional curation) |
| ↳ [Story 5: Export dataset splits](./05-export-dataset-splits.md) | Low | Low | Low | 3 | ✅ Keep |

---

## Ticket Structure

```text
Epic: AI-Assisted Dataset Generation & Curation Platform (Total: 26 points)
├── 01-configure-dataset-task.md     (5 pts, Priority: High, Depends on: —)
├── 02-upload-seed-documents.md      (5 pts, Priority: High, Depends on: Story 1)
├── 03-generate-synthetic-batches.md (8 pts [at limit], Priority: Highest, Depends on: Story 1, Story 2)
├── 04-inspect-curate-samples.md     (5 pts, Priority: Medium, Depends on: Story 3)
└── 05-export-dataset-splits.md      (3 pts, Priority: High, Depends on: Story 3)
```

---

## Confirmed Requirements Checklist

- [x] **Task Modes**: Both Instruction Training and Evaluation Benchmarks are supported.
- [x] **Verification Workflow**: Samples default to `READY` upon generation; no mandatory verification gate required.
- [x] **Seed File Ingestion**: File upload (PDF, TXT, Markdown, CSV) with text extraction added as a dedicated story.
- [x] **Export**: Direct `.zip` download with JSONL/CSV splits confirmed as sufficient for MVP.
