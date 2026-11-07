# TASK-05: Implement Data Recipe Engine & Code Generator

**Target Story:** [05-interactive-filtering-data-recipe.md](../../requirements/pair-coding-eda-assistant/05-interactive-filtering-data-recipe.md)  
**Priority:** Medium | **Estimate:** 3 pts | **Status:** Queued

---

## Technical Goal
Implement a rule execution engine that parses filtering actions into a structured, versioned `recipe.yaml` and serializes the recipe into a self-contained, reproducible Python pandas script (`clean_dataset.py`).

---

## Files to Touch / Create
- `backend/src/services/recipe_engine.py` *(new)*
- `backend/src/templates/clean_dataset_template.py.jinja2` *(new)*
- `backend/tests/test_recipe_engine.py` *(new)*

---

## Implementation Steps

### 1. Define Recipe Schema
```yaml
recipe_version: "1.0"
dataset_id: "ds_abc123"
steps:
  - step: 1
    operator: "filter_token_length"
    params: { min_tokens: 30, max_tokens: 2000 }
  - step: 2
    operator: "exclude_flag"
    params: { flag: "HIGH_HALLUCINATION_RISK" }
  - step: 3
    operator: "drop_cluster"
    params: { cluster_id: 4 }
```

### 2. Implement Rule Execution & Preview
- [ ] Implement filter operators: `filter_token_length`, `exclude_flag`, `drop_cluster`, `deduplicate_semantic`.
- [ ] Provide preview dry-run: execute rule in memory and return `{"original_count": N, "remaining_count": M, "percentage_retained": P}`.

### 3. Generate Standalone Python Script
- [ ] Use Jinja2 template to generate a complete `clean_dataset.py` that loads input CSV/JSONL, applies the exact filter logic using pandas, and writes `cleaned_output.jsonl`.

---

## Verification & Testing
- Run test: `pytest backend/tests/test_recipe_engine.py`
- Verify generated Python script executes successfully with `python clean_dataset.py --input raw.jsonl --output out.jsonl`.

---

## Definition of Done
- [ ] Recipe can be saved, reverted step-by-step, and exported.
- [ ] Generated Python script runs standalone without backend dependencies.
