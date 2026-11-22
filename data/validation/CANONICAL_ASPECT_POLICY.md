# Canonical aspect policy

Product-level aggregation normalizes only documented synonyms. For example, `noise-cancelling`, `noise cancelling`, and `noise cancellation` become `noise cancellation`; `case` becomes `carrying case`; and `sound` becomes `sound quality`.

The aggregation output preserves each model label as `original_aspect` beside the review ID and evidence. This makes every mapping auditable and allows future refinement without re-running the LLM.

The versioned mapping is implemented in `app/pipeline/canonicalization.py`. Do not use fuzzy matching or silently merge new labels: add a reviewed exact mapping, explain it here, and regenerate the aggregation from the same JSONL extraction output.
