# TASK-04: Implement Quality Diagnostics Worker

**Target Story:** [04-post-synthesis-quality-diagnostics.md](../../requirements/pair-coding-eda-assistant/04-post-synthesis-quality-diagnostics.md)  
**Priority:** High | **Estimate:** 3 pts | **Status:** Queued

---

## Technical Goal
Implement diagnostic algorithms to calculate prompt vs. response length correlations, linguistic readability grades (Flesch-Kincaid), and extractive context-grounding overlap scores to flag hallucinations.

---

## Files to Touch / Create
- `backend/src/services/eda/quality_diagnostics.py` *(new)*
- `backend/tests/test_quality_diagnostics.py` *(new)*

---

## Implementation Steps

### 1. Implement Length Correlation
- [ ] Calculate token counts for both prompt and response.
- [ ] Compute Prompt-to-Response ratio (`response_tokens / prompt_tokens`).
- [ ] Flag samples where `response_tokens < 15` as `TRUNCATED_OR_TOO_SHORT`.

### 2. Implement Readability Scorer
- [ ] Compute Flesch-Kincaid Grade Level formula:
  $$\text{Grade} = 0.39 \times \left(\frac{\text{total words}}{\text{total sentences}}\right) + 11.8 \times \left(\frac{\text{total syllables}}{\text{total words}}\right) - 15.59$$
- [ ] Categorize into `Elementary` (< 6), `Intermediate` (6–12), `Advanced` (> 12).

### 3. Implement Grounding / Faithfulness Overlap Heuristic
- [ ] Extract content n-grams (unigrams + bigrams minus stopwords) from reference source chunk.
- [ ] Measure percentage of response claims/entities found in reference source.
- [ ] If overlap < 0.40, flag sample with `HIGH_HALLUCINATION_RISK`.

---

## Verification & Testing
- Run test: `pytest backend/tests/test_quality_diagnostics.py`
- Verify hallucinated response test case correctly triggers `HIGH_HALLUCINATION_RISK`.

---

## Definition of Done
- [ ] Quality diagnostics process 500 samples in < 3 seconds.
- [ ] All diagnostic tags correctly attach to sample metadata.
