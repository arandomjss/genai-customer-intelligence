"""Checkpointed extraction runner. It records every outcome and can resume safely."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from app.llm.gemini_provider import GeminiProvider
from app.pipeline.schema import normalize_extraction, validate_extraction


def _completed_ids(path: Path) -> set[str]:
    """Return terminal records only; failed API calls must be retried later."""
    if not path.exists():
        return set()
    terminal_statuses = {"SUCCESS", "INVALID"}
    return {
        record["review_id"]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
        for record in [json.loads(line)]
        if record.get("status") in terminal_statuses
    }


def _review_id(row: dict[str, str], source_row: int) -> str:
    """Use a source ID when available, otherwise create a stable traceable ID."""
    existing = row.get("review_id") or row.get("id")
    if existing:
        return existing
    fingerprint = "\x1f".join(row.get(field, "") for field in ("parent_asin", "asin", "timestamp", "title", "text", "review_text"))
    digest = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:12]
    return f"ROW_{source_row:06d}_{digest}"


def run_extraction(input_path: Path, output_path: Path, provider: Any, limit: int | None = None, delay_seconds: float = 0.0) -> dict[str, int]:
    """Extract reviews into JSONL. Existing review IDs are never called again."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed = _completed_ids(output_path)
    counts = {"skipped": 0, "success": 0, "invalid": 0, "failed": 0}
    with input_path.open(encoding="utf-8-sig", newline="") as source, output_path.open("a", encoding="utf-8") as sink:
        for source_row, row in enumerate(csv.DictReader(source), start=2):
            review_id = _review_id(row, source_row)
            if review_id in completed:
                counts["skipped"] += 1
                continue
            if limit is not None and sum(counts[key] for key in ("success", "invalid", "failed")) >= limit:
                break
            text = row.get("review_text") or row.get("text") or ""
            record: dict[str, Any] = {"review_id": review_id, "source_row": source_row, "parent_asin": row.get("parent_asin", ""), "rating": row.get("rating", ""), "review_text": text}
            try:
                raw_result = provider.extract(text, review_id)
                # Validate the model response before normalization so malformed
                # fields are reported rather than silently discarded.
                errors = validate_extraction(raw_result)
                result = normalize_extraction(raw_result) if not errors else raw_result
                record.update(status="SUCCESS" if not errors else "INVALID", schema_valid=not errors, validation_errors=errors, result=result, error="")
                counts["success" if not errors else "invalid"] += 1
            except Exception as exc:  # Retain failures so they are visible and auditable.
                record.update(status="FAILED", schema_valid=False, validation_errors=[], result=None, error=f"{type(exc).__name__}: {exc}")
                counts["failed"] += 1
            sink.write(json.dumps(record, ensure_ascii=False) + "\n")
            sink.flush()
            if delay_seconds:
                time.sleep(delay_seconds)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Run resumable Gemini review extraction.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, help="Maximum new API calls; use a small value first.")
    parser.add_argument(
        "--delay",
        type=float,
        default=5.0,
        help="Seconds to wait between calls (default: 5.0, safely below the 15 RPM limit).",
    )
    parser.add_argument("--model", default=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"))
    args = parser.parse_args()
    if args.limit is None:
        raise SystemExit("Safety check: pass --limit explicitly before starting a paid API run.")
    print(run_extraction(args.input, args.output, GeminiProvider(model_name=args.model), args.limit, args.delay))


if __name__ == "__main__":
    main()
