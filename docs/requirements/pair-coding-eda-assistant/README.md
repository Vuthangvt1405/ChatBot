# Epic: Pair-Coding AI Assistant with Deep EDA for Dataset Engineering

**Epic Summary:** Build an interactive pair-coding co-pilot that assists AI Engineers with Exploratory Data Analysis (EDA), corpus profiling, semantic diversity auditing, and guided data filtering for LLM training and evaluation datasets.  
**Type:** Epic | **Suggested Total Points:** 28 points | **Status:** Ready for Backlog

---

## Requirement Analysis

| Item | Details |
|---|---|
| **Actors** | • **AI / ML Engineer** (primary user: collaborates with the assistant, asks exploratory questions, reviews EDA distributions, defines data filtering rules)<br>• **Pair-Coding Agent / EDA Worker** (system actor: analyzes corpora, computes token distributions, clusters topics, generates data-cleaning recipes) |
| **Goals** | 1. Provide an interactive pair-coding environment where an AI Engineer can explore both source text (scraped web pages/docs) and generated synthetic datasets.<br>2. Run automated Pre-Synthesis EDA to audit source documents for token distribution, boilerplate noise, and vocabulary spread.<br>3. Run Post-Synthesis EDA to evaluate synthetic dataset diversity, topic coverage, response length balance, and grounding faithfulness.<br>4. Detect data collapse, repetitive prompts, and underrepresented domains via semantic clustering.<br>5. Allow the engineer to collaborate with the assistant to generate reproducible data recipes (filter scripts/rules) using natural language. |
| **Business Value** | • Prevents model training failures and hallucination loops by catching data collapse and poor distribution early.<br>• Saves senior AI engineers days of writing ad-hoc EDA and data-wrangling boilerplate scripts.<br>• Guarantees full reproducibility and auditability of dataset curation decisions. |
| **Rules & Constraints** | • The assistant must execute EDA computations non-destructively in an analytical sandbox without altering ground truth data until the engineer confirms a recipe.<br>• EDA summaries must include concrete numerical metrics (p50, p95 token lengths, cluster counts, vocabulary richness) rather than vague subjective descriptions.<br>• All filtering rules applied through the assistant must be exported as a versioned, reproducible data recipe (`recipe.yaml` or Python script). |
| **Data Involved** | • **EDA Session**: Session ID, active dataset reference, session conversation history, generated charts/metrics.<br>• **Corpus Diagnostics**: Token count distribution (min/p50/p95/max), vocabulary Type-Token Ratio (TTR), language breakdown, boilerplate ratio.<br>• **Synthetic Diversity Profile**: Semantic clusters (KMeans/HDBSCAN), centroid labels, similarity matrix, difficulty/readability scores.<br>• **Data Recipe**: Sequential filter rules (e.g., `min_tokens: 50`, `max_similarity: 0.88`, `drop_clusters: [3]`). |
| **Ambiguities & Assumptions** | • *Stated*: Project serves as a pair-coding tool with the AI Engineer to help with EDA.<br>• *Assumed*: EDA visual outputs are delivered via responsive statistical tables and visual charts directly in the pair-coding workspace *(assumption)*.<br>• *Assumed*: Analysis runs locally or within a lightweight Python backend sandbox (pandas, scikit-learn, tokenizers) without requiring external GPU infrastructure for standard EDA *(assumption)*. |

---

## Estimation Log

| Candidate story | Complexity | Uncertainty | Effort | Points | Action |
|---|---|---|---|---|---|
| Comprehensive pair-coding EDA platform | High | High | High | 21+ | ✂️ Split into 5 INVEST stories |
| ↳ [Story 1: Interactive pair-coding workspace](./01-interactive-pair-coding-workspace.md) | Medium | Low | Medium | 5 | ✅ Keep |
| ↳ [Story 2: Pre-synthesis source corpus EDA](./02-pre-synthesis-corpus-eda.md) | Medium | Low | Medium | 5 | ✅ Keep |
| ↳ [Story 3: Semantic diversity and topic clustering](./03-semantic-diversity-clustering.md) | High | Medium | High | 8 | ⚠️ Keep (at limit) |
| ↳ [Story 4: Post-synthesis quality diagnostics](./04-post-synthesis-quality-diagnostics.md) | Medium | Low | Medium | 5 | ✅ Keep |
| ↳ [Story 5: Interactive data recipe builder](./05-interactive-filtering-data-recipe.md) | Medium | Low | Medium | 5 | ✅ Keep |

---

## Ticket Structure

```text
Epic: Pair-Coding AI Assistant with Deep EDA for Dataset Engineering (Total: 28 points)
├── 01-interactive-pair-coding-workspace.md     (5 pts, Priority: Highest, Depends on: —)
├── 02-pre-synthesis-corpus-eda.md             (5 pts, Priority: High, Depends on: Story 1)
├── 03-semantic-diversity-clustering.md        (8 pts [at limit], Priority: High, Depends on: Story 1)
├── 04-post-synthesis-quality-diagnostics.md   (5 pts, Priority: High, Depends on: Story 1, Story 2)
└── 05-interactive-filtering-data-recipe.md     (5 pts, Priority: Medium, Depends on: Story 2, Story 4)
```

---

## Confirmed Requirements Checklist

- [x] **Pair-Coding Model**: Assistant collaborates in a conversational side-by-side workspace.
- [x] **Dual EDA Phases**: Covers both Pre-Synthesis (source corpus audit) and Post-Synthesis (dataset validation).
- [x] **Reproducibility**: Filtering outputs produce reusable data recipes rather than silent destructive modifications.
