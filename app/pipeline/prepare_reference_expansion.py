"""Prepare a deterministic, balanced AI-assisted annotation draft.

This module deliberately does *not* merge predictions into the confirmed gold
set.  A reviewer must inspect and approve the generated draft first.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


FIELDS = (
    "aspects",
    "aspect_sentiments",
    "customer_issues",
    "feature_requests",
    "use_cases",
    "positive_points",
    "negative_points",
    "review_summary",
)


def _records(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _payload(record: dict[str, Any]) -> dict[str, Any]:
    if isinstance(record.get("result"), dict):
        return record["result"]
    if isinstance(record.get("result_json"), str):
        return json.loads(record["result_json"])
    return record


def _stable_rank(review_id: str, seed: int) -> str:
    return hashlib.sha256(f"{seed}:{review_id}".encode()).hexdigest()


def _select_diverse(candidates: list[dict[str, Any]], count: int, seed: int) -> list[dict[str, Any]]:
    """Prefer underrepresented product/rating combinations without randomness."""
    selected: list[dict[str, Any]] = []
    product_counts: Counter[str] = Counter()
    rating_counts: Counter[str] = Counter()
    remaining = sorted(candidates, key=lambda item: _stable_rank(item["review_id"], seed))
    while remaining and len(selected) < count:
        choice = min(
            remaining,
            key=lambda item: (
                product_counts[str(item.get("parent_asin", "unknown"))],
                rating_counts[str(item.get("rating", "unknown"))],
                _stable_rank(item["review_id"], seed),
            ),
        )
        remaining.remove(choice)
        selected.append(choice)
        product_counts[str(choice.get("parent_asin", "unknown"))] += 1
        rating_counts[str(choice.get("rating", "unknown"))] += 1
    if len(selected) != count:
        raise ValueError(f"Needed {count} candidates, but only found {len(selected)}.")
    return selected


def prepare_expansion(
    gold_path: Path,
    production_path: Path,
    draft_output: Path,
    review_output: Path,
    plan_output: Path,
    target_per_class: int = 50,
    seed: int = 42,
) -> dict[str, Any]:
    """Create annotation candidates needed to make a balanced reference set."""
    gold = {record["review_id"]: record for record in _records(gold_path)}
    existing_classes = Counter(bool(record.get("customer_issues")) for record in gold.values())
    required = {
        False: max(0, target_per_class - existing_classes[False]),
        True: max(0, target_per_class - existing_classes[True]),
    }

    latest: dict[str, dict[str, Any]] = {}
    for record in _records(production_path):
        latest[record["review_id"]] = record
    pools: dict[bool, list[dict[str, Any]]] = {False: [], True: []}
    for record in latest.values():
        if record.get("status") != "SUCCESS" or record["review_id"] in gold:
            continue
        pools[bool(_payload(record).get("customer_issues", []))].append(record)

    selected = _select_diverse(pools[False], required[False], seed) + _select_diverse(pools[True], required[True], seed)
    selected.sort(key=lambda item: (bool(_payload(item).get("customer_issues", [])), str(item.get("parent_asin", "")), _stable_rank(item["review_id"], seed)))

    draft_rows = []
    review_rows = []
    for record in selected:
        payload = _payload(record)
        draft = {"review_id": record["review_id"], **{field: payload.get(field, [] if field != "review_summary" else "") for field in FIELDS}}
        draft["notes"] = (
            "AI-assisted expansion draft; reviewer must verify each field against the review text. "
            "Delete unsupported claims, add missed explicit claims, and keep labels concise."
        )
        draft_rows.append(draft)
        review_rows.append({
            "review_id": record["review_id"],
            "parent_asin": record.get("parent_asin", ""),
            "rating": record.get("rating", ""),
            "draft_issue_class": "issue_present" if payload.get("customer_issues") else "no_issue",
            "review_text": record.get("review_text", ""),
            "draft_customer_issues": " | ".join(payload.get("customer_issues", [])),
            "reviewer_status": "PENDING",
        })

    draft_output.parent.mkdir(parents=True, exist_ok=True)
    draft_output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in draft_rows), encoding="utf-8")
    with review_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(review_rows[0]) if review_rows else ["review_id"])
        writer.writeheader()
        writer.writerows(review_rows)

    plan = {
        "status": "PENDING_HUMAN_REVIEW",
        "selection_method": "Deterministic greedy diversity selection across parent product and rating; seed=42.",
        "target_reference_set": target_per_class * 2,
        "existing_confirmed": {"no_issue": existing_classes[False], "issue_present": existing_classes[True], "total": len(gold)},
        "draft_additions": {"no_issue": required[False], "issue_present": required[True], "total": len(selected)},
        "after_confirmation": {"no_issue": target_per_class, "issue_present": target_per_class, "total": target_per_class * 2},
        "available_successful_extractions": sum(record.get("status") == "SUCCESS" for record in latest.values()),
        "draft_product_count": len({row["parent_asin"] for row in review_rows}),
        "draft_rating_distribution": dict(sorted(Counter(str(row["rating"]) for row in review_rows).items())),
    }
    plan_output.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare an unconfirmed balanced reference-set expansion draft.")
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--production", type=Path, required=True)
    parser.add_argument("--draft-output", type=Path, required=True)
    parser.add_argument("--review-output", type=Path, required=True)
    parser.add_argument("--plan-output", type=Path, required=True)
    parser.add_argument("--target-per-class", type=int, default=50)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    plan = prepare_expansion(
        gold_path=args.gold,
        production_path=args.production,
        draft_output=args.draft_output,
        review_output=args.review_output,
        plan_output=args.plan_output,
        target_per_class=args.target_per_class,
        seed=args.seed,
    )
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
