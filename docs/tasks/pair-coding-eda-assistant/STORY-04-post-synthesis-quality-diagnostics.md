# STORY-04: Post-synthesis quality diagnostics and grounding verification

[← Back to Sprint Backlog](./README.md) | [Epic PRD](../../requirements/pair-coding-eda-assistant/README.md)

**Summary:** Post-synthesis quality diagnostics and grounding verification  
**Type:** Story | **Epic:** Pair-Coding AI Assistant with Deep EDA for Dataset Engineering | **Priority:** High | **Labels:** `quality-eda`, `grounding`, `faithfulness` | **Components:** `Diagnostics-Worker`, `Quality-Service`  
**Story points (suggested):** 5 — Complexity [Medium], Uncertainty [Low], Effort [Medium] — Diagnostic checks for prompt-to-response length ratios, reading grade difficulty, and source grounding faithfulness.

---

### User Story
As an **AI Engineer**, I want **the assistant to run diagnostic health checks on synthetic samples (prompt vs. response length ratios, difficulty scores, and source grounding)**, so that **I can catch truncated responses, trivial questions, or hallucinations before deploying the dataset**.

### Background
Evaluating synthetic datasets requires looking beyond simple syntax validation. AI Engineers need to know whether generated responses are unnaturally short, whether questions are too simple to evaluate real reasoning, and whether answers are strictly grounded in source documents.

### Acceptance Criteria

**AC1 — Prompt vs. Response length correlation analysis**  
Given a synthetic dataset of instruction/response or evaluation pairs  
When the engineer requests "Run Quality Diagnostics"  
Then the system plots a scatter/density distribution of Prompt Length vs. Response Length and reports the median ratio, flagging samples where the response is unusually short (< 15 tokens) or truncated at maximum generation limits.

**AC2 — Reading grade and linguistic complexity scoring**  
Given the generated text samples  
When the diagnostic worker processes inputs and outputs  
Then it computes standard readability metrics (e.g., Flesch-Kincaid Grade Level / Automated Readability Index) and categorizes dataset difficulty into: `Elementary` (Grade < 6), `Intermediate` (Grade 6–12), and `Advanced / Technical` (Grade > 12).

**AC3 — Grounding / Faithfulness risk audit**  
Given samples generated from web context or seed documents  
When the grounding heuristic evaluates fact alignment  
Then it calculates an extractive grounding overlap score and flags samples with low factual overlap (< 0.40 score *(dev decision)*) as `HIGH_HALLUCINATION_RISK`.

**AC4 — Conversational diagnostic report in chat**  
Given diagnostics are complete  
When the assistant summarizes the findings in the pair-coding chat  
Then it delivers a prioritized health check (e.g., *"Overall Quality Score: 88/100. 14 samples flagged for potential hallucination; 8 samples flagged for truncated answers"*).

**AC5 — Filter by diagnostic tag**  
Given the user clicks on any flagged category in the chat report  
Then the data viewer filters instantly to show those specific flagged samples for human inspection.

### Developer Notes
- **Context & Intent**: Provides standard automated evaluation heuristics that save hours of spot-checking.
- **Affected Areas**: `QualityDiagnosticsWorker`, `ReadabilityScorer`, `GroundingEvaluator`, `HealthReportWidget`.
- **Dev Decisions**:
  - Readability: Use standard Python `textstat` or formulas for Flesch-Kincaid.
  - Grounding heuristic: Token n-gram recall + key entity overlap between reference context and generated answer.

### Out of Scope
- Full GPT-4-as-a-judge re-evaluation on 100% of large datasets (cost prohibitive; use fast statistical heuristics and spot-checking).

### Dependencies
- Story 1 (Pair-coding workspace).

### Open Questions
- None.
