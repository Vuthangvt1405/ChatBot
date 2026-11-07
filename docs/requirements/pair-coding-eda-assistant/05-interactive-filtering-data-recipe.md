# Story 5: Interactive data recipe builder and natural language filtering

[← Back to Epic Overview](./README.md)

**Summary:** Interactive data recipe builder and natural language filtering  
**Type:** Story | **Epic:** Pair-Coding AI Assistant with Deep EDA for Dataset Engineering | **Priority:** Medium | **Labels:** `data-recipes`, `reproducibility`, `filtering` | **Components:** `Recipe-Service`, `Rule-Engine`  
**Story points (suggested):** 5 — Complexity [Medium], Uncertainty [Low], Effort [Medium] — Translates natural language filtering requests into an executable, versioned data recipe (`recipe.yaml` / Python).

---

### User Story
As an **AI Engineer**, I want **to ask the assistant in natural language to filter or prune the dataset based on EDA findings, and have it produce a versioned data recipe**, so that **my data-cleaning operations are 100% reproducible and audit-trailed**.

### Background
Manual ad-hoc deletions leave datasets in an unrepeatable state. When an engineer tells the pair-coding assistant *"Drop all samples with < 20 tokens and remove duplicate cluster #4"*, translating that into a structured data recipe (similar to Data-Juicer or Lilac recipes) ensures the exact same filtering can be re-run on future data batches.

### Acceptance Criteria

**AC1 — Natural language rule interpretation**  
Given an active dataset with EDA metrics  
When the engineer types a filtering instruction in chat (e.g., *"Filter out prompts shorter than 30 characters and drop anything with hallucination risk"*)  
Then the assistant parses the intent into explicit rule parameters and presents a preview: *"Proposed Filter: prompt_length >= 30 AND hallucination_risk == False. This will retain 412 / 450 samples (91.5%)."*

**AC2 — Preview impact before applying**  
Given a proposed filtering rule  
When the user views the preview  
Then the EDA metrics panel simulates the new token distributions and cluster balances in a "Draft" mode without mutating the underlying dataset.

**AC3 — Apply rule and generate versioned recipe**  
Given the user clicks "Confirm & Apply Recipe"  
When the operation executes  
Then the system creates a new dataset version slice, updates the active view, and appends the rule to a version-controlled `recipe.yaml` file.

**AC4 — Exportable Python and YAML recipe formats**  
Given a finalized data recipe  
When the engineer clicks "Export Recipe"  
Then the system allows downloading the recipe as either:
- A declarative `recipe.yaml` configuration.
- A standalone, self-contained Python script (`clean_dataset.py`) using `pandas` that any engineer can run via CLI.

**AC5 — Rollback / Revert recipe step**  
Given a sequence of applied filtering steps (e.g., Step 1: Dedup, Step 2: Length Filter)  
When the user clicks "Revert Step 2"  
Then the dataset rolls back to the state after Step 1, updating sample counts and metrics accordingly.

### Developer Notes
- **Context & Intent**: Bridges conversational pair-coding with strict software engineering reproducibility.
- **Affected Areas**: `DataRecipeEngine`, `FilterInterpreter`, `RecipeSerializer`, `VersionHistoryController`.
- **Data & Fields**:
  - `recipe_id`: UUIDv4
  - `steps`: array of `{step_index: int, operator: string, params: object, removed_count: int, timestamp: string}`
  - `output_slice_hash`: SHA256 string.

### Out of Scope
- Distributed streaming execution across Spark or Ray clusters (designed for in-memory / workstation scale).

### Dependencies
- Story 2 & Story 4 (Metrics and diagnostic tags).

### Open Questions
- None.
