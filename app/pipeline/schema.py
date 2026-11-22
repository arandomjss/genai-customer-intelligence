"""Validation and normalization for the project's eight-field extraction schema."""

from __future__ import annotations

from typing import Any

FIELDS = (
    "aspects", "aspect_sentiments", "customer_issues", "feature_requests",
    "use_cases", "positive_points", "negative_points", "review_summary",
)
LIST_FIELDS = set(FIELDS) - {"aspect_sentiments", "review_summary"}
SENTIMENTS = {"positive", "negative", "neutral"}


def validate_extraction(value: Any) -> list[str]:
    """Return human-readable structural validation errors (empty means valid)."""
    errors: list[str] = []
    if not isinstance(value, dict):
        return ["result must be a JSON object"]
    missing, extra = set(FIELDS) - set(value), set(value) - set(FIELDS)
    if missing:
        errors.append(f"missing fields: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"unexpected fields: {', '.join(sorted(extra))}")
    for field in LIST_FIELDS:
        items = value.get(field)
        if not isinstance(items, list) or not all(isinstance(item, str) and item.strip() for item in items):
            errors.append(f"{field} must be a list of non-empty strings")
    summary = value.get("review_summary")
    if not isinstance(summary, str):
        errors.append("review_summary must be a string")
    sentiments = value.get("aspect_sentiments")
    if not isinstance(sentiments, list):
        errors.append("aspect_sentiments must be a list")
    else:
        for index, item in enumerate(sentiments):
            if not isinstance(item, dict):
                errors.append(f"aspect_sentiments[{index}] must be an object")
                continue
            required = {"aspect", "sentiment", "evidence"}
            if set(item) != required:
                errors.append(f"aspect_sentiments[{index}] must contain exactly aspect, sentiment, evidence")
                continue
            if not all(isinstance(item[key], str) and item[key].strip() for key in required):
                errors.append(f"aspect_sentiments[{index}] values must be non-empty strings")
            elif item["sentiment"].lower() not in SENTIMENTS:
                errors.append(f"aspect_sentiments[{index}].sentiment is invalid")
    return errors


def normalize_extraction(value: dict[str, Any]) -> dict[str, Any]:
    """Trim strings and standardize sentiment casing without adding information."""
    result: dict[str, Any] = {}
    for field in LIST_FIELDS:
        result[field] = [item.strip() for item in value.get(field, []) if isinstance(item, str) and item.strip()]
    result["aspect_sentiments"] = [
        {"aspect": item["aspect"].strip(), "sentiment": item["sentiment"].strip().lower(), "evidence": item["evidence"].strip()}
        for item in value.get("aspect_sentiments", []) if isinstance(item, dict)
        and all(isinstance(item.get(key), str) and item[key].strip() for key in ("aspect", "sentiment", "evidence"))
    ]
    result["review_summary"] = value.get("review_summary", "").strip() if isinstance(value.get("review_summary", ""), str) else ""
    return result
