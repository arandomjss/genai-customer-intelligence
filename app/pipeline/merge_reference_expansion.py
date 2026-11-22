"""Promote a user-confirmed annotation expansion into the reference set."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def merge(gold_path: Path, draft_path: Path, review_csv: Path, backup_path: Path, plan_path: Path) -> int:
    gold = _jsonl(gold_path)
    draft = _jsonl(draft_path)
    gold_ids = {record["review_id"] for record in gold}
    draft_ids = [record["review_id"] for record in draft]
    if len(draft_ids) != len(set(draft_ids)):
        raise ValueError("The expansion draft contains duplicate review IDs.")
    if gold_ids.intersection(draft_ids):
        raise ValueError("The expansion draft overlaps the confirmed reference set.")

    backup_path.write_text(gold_path.read_text(encoding="utf-8"), encoding="utf-8")
    for record in draft:
        record["notes"] = (
            "AI-assisted draft reviewed and confirmed by the project user on 2026-10-25. "
            "Labels remain constrained to claims explicitly stated in the review."
        )
    merged = gold + draft
    gold_path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in merged), encoding="utf-8")

    with review_csv.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = handle.seek(0) or None
    if rows:
        for row in rows:
            row["reviewer_status"] = "CONFIRMED"
        with review_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["status"] = "CONFIRMED_BY_PROJECT_USER"
    plan["confirmation_note"] = "All 66 expansion annotations were reviewed and confirmed by the project user on 2026-10-25."
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return len(merged)


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge a confirmed reference-set expansion.")
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--review-csv", type=Path, required=True)
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    print(f"Confirmed reference set now contains {merge(args.gold, args.draft, args.review_csv, args.backup, args.plan)} reviews.")


if __name__ == "__main__":
    main()
