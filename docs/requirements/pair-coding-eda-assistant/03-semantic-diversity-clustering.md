# Story 3: Semantic diversity and topic clustering for dataset coverage

[← Back to Epic Overview](./README.md)

**Summary:** Semantic diversity and topic clustering for dataset coverage  
**Type:** Story | **Epic:** Pair-Coding AI Assistant with Deep EDA for Dataset Engineering | **Priority:** High | **Labels:** `clustering`, `semantic-eda`, `embeddings` | **Components:** `Embedding-Worker`, `Clustering-Service`  
**Story points (suggested):** 8 *(at the limit)* — Complexity [High], Uncertainty [Medium], Effort [High] — Embeds dataset samples, performs unsupervised clustering, and surfaces topic balance to detect data collapse.

---

### User Story
As an **AI Engineer**, I want **the assistant to cluster dataset samples by semantic meaning and display a topic coverage map**, so that **I can identify over-represented topics, discover coverage gaps, and prevent model mode collapse**.

### Background
Generative models frequently fall into repetitive patterns, generating hundreds of minor variations of the same prompt while ignoring other critical domains. Semantic clustering uncovers the hidden distribution of themes and ensures balanced coverage.

### Acceptance Criteria

**AC1 — Unsupervised topic clustering execution**  
Given a dataset of at least 50 samples  
When the engineer triggers "Analyze Semantic Diversity" (or prompts the assistant in chat)  
Then the system computes text embeddings, groups samples into semantic clusters (e.g., $K$-means or HDBSCAN *(dev decision)*), and assigns each cluster an auto-generated descriptive topic label.

**AC2 — Visual cluster distribution and size balance**  
Given clustering finishes  
When the user views the EDA panel  
Then the system displays an interactive cluster chart showing:
- Cluster Name / Theme
- Sample Count & Percentage of Dataset
- Top 5 representative keywords/phrases per cluster
- Outlier / Unclustered sample count

**AC3 — Data collapse and imbalance warning**  
Given cluster distribution is calculated  
When any single cluster accounts for > 40% of the dataset, or a desired domain has < 5% representation  
Then the assistant flags a `TOPIC_IMBALANCE` warning in chat and suggests: *"Topic 'Authentication / Login' dominates 48% of your data. Consider generating more samples from underrepresented sections (e.g. 'Billing & Webhooks')."*

**AC4 — Inspect samples within a specific cluster**  
Given the cluster summary view  
When the user clicks on a cluster node or row  
Then the sample viewer instantly filters to show all prompts and responses belonging to that cluster, allowing spot-checking of semantic similarity.

**AC5 — Cluster pruning action**  
Given a cluster contains repetitive or irrelevant samples  
When the engineer confirms "Exclude Cluster #X" via chat or button  
Then all samples in that cluster are excluded from the candidate export pool, updating overall diversity metrics.

### Developer Notes
- **Context & Intent**: Mode collapse in fine-tuning data leads directly to narrow, repetitive model outputs. This story provides visual and quantitative proof of dataset diversity.
- **Affected Areas**: `EmbeddingWorker`, `TopicClusteringService`, `ClusterVisualizer`, `LLMTopicLabeler`.
- **Dev Decisions**:
  - Embedding model: Fast local embedding model (e.g., `all-MiniLM-L6-v2`) or API embedding provider.
  - Auto-labeling: Extract top TF-IDF n-grams per cluster, or pass 5 centroid samples to a small LLM to generate a concise 3-word cluster title.
  - Performance: For datasets up to 5,000 samples, clustering must complete within 15 seconds.

### Out of Scope
- Real-time 3D interactive graphics rendering (standard 2D scatter or hierarchical bar chart is sufficient).

### Dependencies
- Story 1 (Pair-coding workspace).

### Open Questions
- None.
