"""Product-level aggregation that keeps every claim traceable to review evidence."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from app.pipeline.canonicalization import CANONICALIZATION_VERSION, canonicalize_aspect


def _result(record: dict[str, Any]) -> dict[str, Any] | None:
    """Read both current JSONL records and the first notebook's saved format."""
    value = record.get("result")
    if isinstance(value, dict):
        return value
    legacy = record.get("result_json")
    if isinstance(legacy, str):
        try:
            return json.loads(legacy)
        except json.JSONDecodeError:
            return None
    return None


def aggregate_extractions(input_path: Path, output_path: Path, evidence_per_aspect: int = 3) -> list[dict[str, Any]]:
    products: dict[str, list[dict[str, Any]]] = defaultdict(list)
    # A retried record may appear more than once in an append-only checkpoint.
    # Keep the latest valid SUCCESS record for each review ID so aggregation
    # never inflates counts when an interrupted run is restarted.
    valid_records: dict[str, dict[str, Any]] = {}
    with input_path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            result = _result(record)
            if record.get("status") == "SUCCESS" and record.get("schema_valid") and result is not None:
                record["result"] = result
                valid_records[record["review_id"]] = record
    for record in valid_records.values():
        products[record.get("parent_asin") or "UNKNOWN"].append(record)
    output: list[dict[str, Any]] = []
    for product_id, records in sorted(products.items()):
        sentiments: dict[str, Counter[str]] = defaultdict(Counter)
        sentiment_review_ids: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
        evidence: dict[str, list[dict[str, str]]] = defaultdict(list)
        issues, requests = Counter(), Counter()
        for record in records:
            result = record["result"]
            issues.update(result["customer_issues"])
            requests.update(result["feature_requests"])
            for item in result["aspect_sentiments"]:
                original_aspect = item["aspect"].strip()
                aspect = canonicalize_aspect(original_aspect)
                sentiments[aspect][item["sentiment"]] += 1
                sentiment_review_ids[aspect][item["sentiment"]].add(record["review_id"])
                if len(evidence[aspect]) < evidence_per_aspect and not any(entry["review_id"] == record["review_id"] for entry in evidence[aspect]):
                    evidence[aspect].append({"review_id": record["review_id"], "original_aspect": original_aspect, "evidence": item["evidence"], "sentiment": item["sentiment"]})
        output.append({"parent_asin": product_id, "review_count": len(records), "canonicalization_version": CANONICALIZATION_VERSION, "aspects": [
            {"aspect": aspect, "sentiment_counts": dict(counts), "sentiment_review_counts": {sentiment: len(review_ids) for sentiment, review_ids in sentiment_review_ids[aspect].items()}, "evidence": evidence[aspect]}
            for aspect, counts in sorted(sentiments.items(), key=lambda pair: (-sum(pair[1].values()), pair[0]))
        ], "top_customer_issues": [{"text": text, "count": count} for text, count in issues.most_common(10)], "top_feature_requests": [{"text": text, "count": count} for text, count in requests.most_common(10)]})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(f"Aggregated {len(aggregate_extractions(args.input, args.output))} products.")


if __name__ == "__main__":
    main()
