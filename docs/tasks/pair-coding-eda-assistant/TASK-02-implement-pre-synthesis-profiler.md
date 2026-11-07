# TASK-02: Implement Pre-Synthesis Corpus Profiler

**Target Story:** [02-pre-synthesis-corpus-eda.md](../../requirements/pair-coding-eda-assistant/02-pre-synthesis-corpus-eda.md)  
**Priority:** High | **Estimate:** 3 pts | **Status:** Ready to Start

---

## Technical Goal
Implement the backend EDA profiling module to compute token length percentiles (min, p25, p50, p95, max), vocabulary richness (Type-Token Ratio), language detection, and boilerplate/noise ratio across ingested raw text chunks.

---

## Files to Touch / Create
- `backend/src/services/eda/corpus_profiler.py` *(new)*
- `backend/src/api/routes/eda_routes.py` *(new)*
- `backend/src/schemas/eda_schemas.py` *(new)*
- `backend/tests/test_corpus_profiler.py` *(new)*

---

## Implementation Steps

### 1. Define Schemas (`eda_schemas.py`)
```python
from pydantic import BaseModel
from typing import Dict, List, Optional

class CorpusSummaryStats(BaseModel):
    total_documents: int
    total_tokens: int
    min_tokens: int
    p25_tokens: float
    p50_tokens: float
    p95_tokens: float
    max_tokens: int
    type_token_ratio: float
    language_breakdown: Dict[str, float]
    flagged_noise_count: int

class ChunkAuditResult(BaseModel):
    chunk_id: str
    token_count: int
    noise_ratio: float
    is_boilerplate: bool
    reasons: List[str]
```

### 2. Implement Profiling Engine (`corpus_profiler.py`)
- [ ] **Token Counting**: Use `tiktoken.get_encoding("cl100k_base")` to tokenize text and calculate exact token lengths.
- [ ] **Percentiles**: Use `numpy.percentile` over the token counts list for `[0, 25, 50, 95, 100]`.
- [ ] **Type-Token Ratio (TTR)**: Compute `len(set(tokens)) / len(tokens)` on downsampled chunks to measure vocabulary diversity.
- [ ] **Boilerplate Heuristic**:
  - Calculate ratio of punctuation, HTML remnants, and short repetitive words.
  - If non-content ratio > 0.30 or token count < 30 with uppercase headers, flag as `is_boilerplate = True`.

### 3. Expose API Route (`eda_routes.py`)
```python
@router.post("/api/datasets/{dataset_id}/eda/corpus-profile", response_model=CorpusSummaryStats)
async def profile_corpus(dataset_id: str, db: Session = Depends(get_db)):
    ...
```

---

## Verification & Testing
- Run unit test: `pytest backend/tests/test_corpus_profiler.py`
- Test with sample test cases:
  1. High-noise web snippet with cookie consent text -> must be flagged as boilerplate.
  2. Clean technical documentation paragraph -> must pass with valid token counts and TTR > 0.4.

---

## Definition of Done
- [ ] Endpoint returns calculations in < 2 seconds for corpora up to 2,000 chunks.
- [ ] 100% unit test coverage for `corpus_profiler.py`.
