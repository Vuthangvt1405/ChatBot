# Story 2: Pre-synthesis source corpus EDA and noise profiling

[← Back to Epic Overview](./README.md)

**Summary:** Pre-synthesis source corpus EDA and noise profiling  
**Type:** Story | **Epic:** Pair-Coding AI Assistant with Deep EDA for Dataset Engineering | **Priority:** High | **Labels:** `eda`, `corpus-profiling`, `noise-detection` | **Components:** `EDA-Worker`, `Analysis-Service`  
**Story points (suggested):** 5 — Complexity [Medium], Uncertainty [Low], Effort [Medium] — Statistical profiling of raw ingested text, token distributions, vocabulary richness, and boilerplate noise ratios.

---

### User Story
As an **AI Engineer**, I want **the assistant to run an automated EDA audit on raw scraped web pages or uploaded documents**, so that **I can identify noisy, sparse, or off-topic source chunks before generating synthetic training data**.

### Background
Garbage in results in garbage out. If source web documents contain high percentages of cookie notices, empty navigation strings, or extreme token lengths, synthetic generation will produce poor samples. An early EDA audit ensures high input quality.

### Acceptance Criteria

**AC1 — Comprehensive corpus summary statistics**  
Given raw source documents or web chunks are ingested into the workspace  
When the engineer requests an audit (or clicks "Run Corpus EDA")  
Then the assistant calculates and displays a summary table containing:
- Total Document/Chunk Count
- Total Token Count
- Token Length Percentiles (Min, p25, p50/Median, p95, Max)
- Vocabulary Richness: Type-Token Ratio (TTR)
- Detected Language Distribution (percentage per language)

**AC2 — Visual token distribution histogram**  
Given the corpus summary is calculated  
When viewing the EDA panel  
Then the system renders a token length distribution chart highlighting the target generation sweet spot (e.g., 500–2,500 tokens) and flags outliers (< 100 tokens or > 4,000 tokens).

**AC3 — Boilerplate and noise ratio detection**  
Given text chunks extracted from web pages  
When the analysis worker evaluates text composition  
Then it flags chunks having high boilerplate markers (repeated headers, HTML residue, copyright footers > 30% of total text) with tag `HIGH_BOILERPLATE`.

**AC4 — Assistant generates actionable diagnostic insights**  
Given the EDA metrics are computed  
When the assistant presents findings in the pair-coding chat  
Then it delivers structured advice (e.g., *"Found 12 chunks with < 50 tokens that contain navigation links. Suggest dropping them before generation to save budget."*).

**AC5 — One-click outlier exclusion**  
Given flagged noise chunks in the EDA overview  
When the user clicks "Exclude Flagged Outliers"  
Then those chunks are marked inactive for synthesis, and the summary statistics recalculate dynamically.

### Developer Notes
- **Context & Intent**: Provides standard NLP data hygiene diagnostics before expensive LLM synthesis calls.
- **Affected Areas**: `CorpusProfiler`, `TokenizerService`, `TextStatisticsHelper`, `EDADashboard`.
- **Dev Decisions**:
  - Token counting: Use standard BPE tokenizer (e.g., `tiktoken` `cl100k_base` for OpenAI/Llama compatibility).
  - TTR formula: Unique tokens divided by total tokens in corpus sample.
  - Boilerplate heuristic: Ratio of non-alphanumeric punctuation and structural HTML leftovers vs. running prose.

### Out of Scope
- Full OCR analysis on raw scanned images.

### Dependencies
- Story 1 (Workspace interface).

### Open Questions
- None.
