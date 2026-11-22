"""Transparent exact-set evaluation against a user-confirmed reference JSONL file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _payload(record: dict[str, Any]) -> dict[str, Any]:
    value = record.get("result")
    if isinstance(value, dict):
        return value
    if isinstance(record.get("result_json"), str):
        return json.loads(record["result_json"])
    return record


def _records(path: Path) -> dict[str, dict[str, Any]]:
    """Read records without allowing failed retries to replace valid output.

    Checkpoint JSONL files may contain several attempts for one review. Only a
    schema-valid SUCCESS record is eligible when a status field is present.
    Plain reference files without processing-status metadata remain supported.
    """
    records: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        review_id = record["review_id"]
        if "status" in record:
            if (
                record.get("status") != "SUCCESS"
                or not record.get("schema_valid")
                or not isinstance(record.get("result"), dict)
            ):
                continue
        records[review_id] = record
    return records


def _f1(tp: int, predicted: int, expected: int) -> dict[str, float | int]:
    """Compute micro metrics after matching labels within each review."""
    precision = tp / predicted if predicted else (1.0 if not expected else 0.0)
    recall = tp / expected if expected else (1.0 if not predicted else 0.0)
    return {"tp": tp, "predicted": predicted, "gold": expected, "precision": precision, "recall": recall, "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0}


def evaluate(predictions_path: Path, gold_path: Path) -> dict[str, Any]:
    predictions = _records(predictions_path)
    gold = _records(gold_path)
    shared = sorted(set(predictions) & set(gold))
    fields = ("aspects", "customer_issues", "feature_requests", "use_cases", "positive_points", "negative_points")
    report: dict[str, Any] = {"matched_reviews": len(shared), "prediction_only": len(set(predictions) - set(gold)), "gold_only": len(set(gold) - set(predictions)), "fields": {}}
    for field in fields:
        true_positive = predicted_total = gold_total = 0
        for review_id in shared:
            pred = {str(value).strip().lower() for value in _payload(predictions[review_id]).get(field, [])}
            expected = {str(value).strip().lower() for value in _payload(gold[review_id]).get(field, [])}
            true_positive += len(pred & expected)
            predicted_total += len(pred)
            gold_total += len(expected)
        report["fields"][field] = _f1(true_positive, predicted_total, gold_total)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evaluate(args.predictions, args.gold), indent=2), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
