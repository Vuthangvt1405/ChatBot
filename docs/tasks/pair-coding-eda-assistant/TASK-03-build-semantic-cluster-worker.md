# TASK-03: Build Semantic Cluster & Diversity Worker

**Target Story:** [03-semantic-diversity-clustering.md](../../requirements/pair-coding-eda-assistant/03-semantic-diversity-clustering.md)  
**Priority:** High | **Estimate:** 5 pts | **Status:** Queued

---

## Technical Goal
Implement embedding computation and unsupervised clustering on dataset samples to surface topic distributions, detect dataset collapse, and generate descriptive cluster labels.

---

## Files to Touch / Create
- `backend/src/services/eda/cluster_service.py` *(new)*
- `backend/src/services/embedding_client.py` *(modify / extend)*
- `backend/src/schemas/cluster_schemas.py` *(new)*
- `backend/tests/test_clustering.py` *(new)*

---

## Implementation Steps

### 1. Define Cluster Schemas (`cluster_schemas.py`)
```python
from pydantic import BaseModel
from typing import List

class ClusterSummary(BaseModel):
    cluster_id: int
    label: str
    sample_count: int
    percentage: float
    top_keywords: List[str]
    centroid_sample_ids: List[str]

class ClusterAnalysisResponse(BaseModel):
    clusters: List[ClusterSummary]
    topic_imbalance_detected: bool
    imbalance_warning: str | None
    unclustered_count: int
```

### 2. Implement Unsupervised Clustering (`cluster_service.py`)
- [ ] Ingest prompt/input embeddings (using local lightweight model or API client).
- [ ] Apply `sklearn.cluster.MiniBatchKMeans` with dynamic $K = \min(10, \max(3, N // 50))$.
- [ ] For each cluster:
  - Extract top 5 keywords using TF-IDF n-grams on member texts.
  - Compute percentage of dataset in cluster.
  - If any cluster > 40%, set `topic_imbalance_detected = True`.

### 3. Generate Cluster Title via LLM / Heuristics
- [ ] Provide top 3 centroid sample snippets to a lightweight prompt to generate a 2–3 word topic title (e.g. *"Auth & Permissions"*, *"Payment Processing"*).

---

## Verification & Testing
- Run test: `pytest backend/tests/test_clustering.py`
- Verify clustering handles edge cases (e.g., $N < 10$ samples returns a single cluster or informative warning).

---

## Definition of Done
- [ ] Successfully clusters 1,000 samples in < 10 seconds.
- [ ] Imbalance heuristic correctly alerts when samples are skewed to a single topic.
