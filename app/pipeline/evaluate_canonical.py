"""Evaluate concept-level consistency using a fixed canonical-label policy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.pipeline.canonicalization import (
    EVALUATION_CANONICALIZATION_VERSION,
    canonicalize_field_value,
)
from app.pipeline.evaluate import _f1


FIELDS = (
    "aspects",
    "customer_issues",
    "feature_requests",
    "use_cases",
    "positive_points",
    "negative_points",
)


def _valid_records(path: Path) -> dict[str, dict[str, Any]]:
    """Keep the latest schema-valid SUCCESS record per review ID."""
    records: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if (
            record.get("status") == "SUCCESS"
            and record.get("schema_valid")
            and isinstance(record.get("result"), dict)
        ):
            records[record["review_id"]] = record
    return records


def _values(record: dict[str, Any], field: str) -> set[str]:
    return {
        canonicalize_field_value(field, str(value))
        for value in record["result"].get(field, [])
        if str(value).strip()
    }


def evaluate_canonical(
    original_path: Path, fresh_path: Path
) -> dict[str, Any]:
    """Compare original and fresh runs after deterministic canonicalisation."""
    original = _valid_records(original_path)
    fresh = _valid_records(fresh_path)
    shared = sorted(set(original) & set(fresh))
    report: dict[str, Any] = {
        "evaluation_type": "canonical_label_consistency",
        "canonicalization_policy_version": EVALUATION_CANONICALIZATION_VERSION,
        "matched_reviews": len(shared),
        "fields": {},
    }
    for field in FIELDS:
        true_positive = predicted_total = reference_total = 0
        for review_id in shared:
            predicted = _values(original[review_id], field)
            reference = _values(fresh[review_id], field)
            true_positive += len(predicted & reference)
            predicted_total += len(predicted)
            reference_total += len(reference)
        report["fields"][field] = _f1(
            true_positive, predicted_total, reference_total
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate two extraction runs after fixed canonicalisation."
    )
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--fresh", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(evaluate_canonical(args.original, args.fresh), indent=2),
        encoding="utf-8",
    )
    print(args.output)


if __name__ == "__main__":
    main()
