"""Assemble a unified reviewed reference set from test and production artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def _jsonl(path: Path) -> dict[str, dict]:
    return {record["review_id"]: record for line in path.read_text(encoding="utf-8").splitlines() if line.strip() for record in [json.loads(line)]}


def build_reference_set(gold_path: Path, test_reviews_path: Path, test_predictions_path: Path, production_path: Path, reviews_output: Path, predictions_output: Path) -> int:
    gold = _jsonl(gold_path)
    with test_reviews_path.open(encoding="utf-8-sig", newline="") as handle:
        test_reviews = {row["review_id"]: row for row in csv.DictReader(handle)}
    test_predictions = _jsonl(test_predictions_path)
    production = _jsonl(production_path)
    review_rows, prediction_rows, missing = [], [], []
    for review_id in sorted(gold):
        if review_id in test_reviews and review_id in test_predictions:
            review_rows.append({"review_id": review_id, "review_text": test_reviews[review_id].get("review_text") or test_reviews[review_id].get("text") or ""})
            prediction_rows.append(test_predictions[review_id])
        elif review_id in production and production[review_id].get("status") == "SUCCESS":
            review_rows.append({"review_id": review_id, "review_text": production[review_id]["review_text"]})
            prediction_rows.append(production[review_id])
        else:
            missing.append(review_id)
    if missing:
        raise ValueError(f"Missing review text or successful prediction for: {', '.join(missing)}")
    reviews_output.parent.mkdir(parents=True, exist_ok=True)
    with reviews_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["review_id", "review_text"])
        writer.writeheader()
        writer.writerows(review_rows)
    predictions_output.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in prediction_rows), encoding="utf-8")
    return len(review_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build unified inputs for reference-set evaluation.")
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--test-reviews", type=Path, required=True)
    parser.add_argument("--test-predictions", type=Path, required=True)
    parser.add_argument("--production", type=Path, required=True)
    parser.add_argument("--reviews-output", type=Path, required=True)
    parser.add_argument("--predictions-output", type=Path, required=True)
    args = parser.parse_args()
    print(f"Assembled {build_reference_set(args.gold, args.test_reviews, args.test_predictions, args.production, args.reviews_output, args.predictions_output)} reviewed examples.")


if __name__ == "__main__":
    main()
