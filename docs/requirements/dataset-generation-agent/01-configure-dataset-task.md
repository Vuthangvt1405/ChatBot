# Story 1: Configure dataset generation task for training and evaluation

[← Back to Epic Overview](./README.md)

**Summary:** Configure dataset generation task for training and evaluation  
**Type:** Story | **Epic:** AI-Assisted Dataset Generation & Curation Platform | **Priority:** High | **Labels:** `spec-builder`, `presets`, `mvp` | **Components:** `Frontend`, `Job-Service`  
**Story points (suggested):** 5 — Complexity [Medium], Uncertainty [Low], Effort [Medium] — Configures dataset goal with built-in presets for Training vs. Evaluation benchmarks.

---

### User Story
As an **AI Engineer**, I want **to configure a dataset job with dedicated presets for Model Training or Evaluation Benchmarks**, so that **the generation agent automatically structures outputs suitable for fine-tuning or evaluation grading**.

### Background
Training datasets require input-output pairs or conversation histories, whereas evaluation datasets require test prompts, expected reference ground truths, and optional scoring rubrics. Providing first-class presets eliminates manual schema drafting for standard ML workflows.

### Acceptance Criteria

**AC1 — Select dataset mode and task preset**  
Given an AI Engineer starts creating a dataset job  
When they choose between "Model Training" and "Model Evaluation"  
Then the system displays tailored presets:
- If "Model Training": offers "Instruction & Response" and "Multi-Turn Chat".
- If "Model Evaluation": offers "Prompt & Golden Answer" and "Rubric-Based Evaluation Question".

**AC2 — Configure job parameters and constraints**  
Given a dataset mode is selected  
When the user provides a job title (3–60 chars), generation instructions, domain background, and target sample count (between 5 and 1,000)  
Then the system validates the fields and saves the specification in `DRAFT` status.

**AC3 — Evaluation benchmark schema fields**  
Given the user selects "Model Evaluation"  
When the job specification is generated  
Then the output schema automatically provisions fields for `test_prompt`, `reference_answer`, `evaluation_criteria`, and `difficulty_level` (easy/medium/hard).

**AC4 — Target sample count validation**  
Given the user enters a target sample count  
When the count is less than 5 or greater than 1,000  
Then the system highlights the input with error: `"Target sample count must be between 5 and 1,000 samples."`

**AC5 — Project isolation**  
Given a user is authenticated in Project A  
When they query or modify dataset specifications  
Then they can only view and edit specifications belonging to Project A.

### Developer Notes
- **Context & Intent**: The preset defines the schema contract and system prompt framing used by the generation worker in Story 3.
- **Affected Areas**: `DatasetConfigModal`, `JobSpecController`, `PresetRegistry`.
- **Data & Fields**:
  - `job_id`: UUIDv4
  - `mode`: enum (`TRAINING`, `EVALUATION`)
  - `preset_type`: enum (`INSTRUCTION_RESPONSE`, `CHAT_CONVERSATION`, `GOLDEN_QA`, `RUBRIC_EVAL`)
  - `target_count`: integer (5–1000)
  - `instructions`: text (max 2000 chars)
  - `status`: enum (`DRAFT`, `READY_FOR_GENERATION`, `RUNNING`, `COMPLETED`)
- **Security**: Strict tenant/project isolation based on the user session token.

### Out of Scope
- Custom JavaScript/Python scoring functions.
- Multi-modal dataset presets (audio/image).

### Dependencies
- User authentication and workspace context service.

### Open Questions
- None.
