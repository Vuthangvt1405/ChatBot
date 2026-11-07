# STORY-03: Generate synthetic sample batches from prompt and seed files

[← Back to Sprint Backlog](./README.md) | [Epic PRD](../../requirements/dataset-generation-agent/README.md)

**Summary:** Generate synthetic sample batches from prompt and seed files  
**Type:** Story | **Epic:** AI-Assisted Dataset Generation & Curation Platform | **Priority:** Highest | **Labels:** `generation-agent`, `synthesis`, `ai-worker` | **Components:** `Agent-Worker`, `LLM-Service`, `Queue-Service`  
**Story points (suggested):** 8 *(at the limit)* — Complexity [High], Uncertainty [Medium], Effort [High] — Batch generation loop combining instructions and chunked seed files with automatic sample readiness.

---

### User Story
As an **AI Engineer**, I want **the agent to synthesize training or evaluation samples grounded in my uploaded files and instructions**, so that **the entire target dataset is generated and marked ready for use without requiring manual review**.

### Background
Manual scripting of dataset generation frequently hits rate limits or token limits when passing large seed files. The agent manages file chunking, prompt synthesis, diversity variation, and automatically tags generated items as `READY` so engineers can immediately proceed to export.

### Acceptance Criteria

**AC1 — Start generation with seed file grounding**  
Given a dataset job with instructions and at least one parsed seed file (or few-shot examples)  
When the user clicks "Start Generation"  
Then the agent initiates micro-batch generation, transitions job status to `RUNNING`, and displays a live progress indicator (`X / Y samples generated`).

**AC2 — Support both Training and Evaluation schemas**  
Given generation is running  
When samples are synthesized:
- For "Model Training": each sample produces realistic instruction/prompt and response pairs.
- For "Model Evaluation": each sample produces an evaluation prompt, reference ground truth answer, and grading criteria.

**AC3 — Default status set to READY**  
Given synthetic samples are successfully produced and parsed by the worker  
When they are persisted to the dataset repository  
Then each sample is assigned status `READY` by default, making them immediately eligible for export.

**AC4 — Rate limit backoff and error recovery**  
Given upstream LLM rate limiting or network interruptions occur during batch synthesis  
When an error is detected  
Then the worker retries up to 3 times with exponential backoff; if still blocked, it pauses gracefully, saves all generated samples, and alerts the user with: `"Generation paused due to provider rate limits. You can resume or proceed with current samples."`

**AC5 — User cancellation preserves generated samples**  
Given generation is in progress  
When the user clicks "Stop Generation"  
Then the worker completes in-flight calls, stops queued batches, updates the job to `COMPLETED_PARTIAL`, and retains all generated samples with status `READY`.

### Developer Notes
- **Context & Intent**: Because the user does not require mandatory quality verification, samples must be immediately actionable and exportable upon generation.
- **Affected Areas**: `GenerationAgentWorker`, `ContextChunkingService`, `LLMClientGateway`, `SampleRepository`.
- **Dev Decisions**:
  - Micro-batching: 5 samples generated per agent cycle.
  - Chunk retrieval: Slide a rolling window or semantic sample over uploaded seed document text to guarantee diversity across the entire file.
  - Schema parsing: If a single sample is malformed/unparseable JSON, discard it and regenerate to ensure only structured samples enter `READY` state.

### Out of Scope
- Automatic fine-tuning execution on external clusters.

### Dependencies
- Story 1 (Specification) and Story 2 (Seed file extraction).

### Open Questions
- None.
