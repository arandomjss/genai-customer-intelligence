"""Create deterministic, evidence-linked product summaries and recommendations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ACTION_BY_ASPECT = {
    "battery life": "Investigate battery capacity, power management, and charge-cycle testing.",
    "charging": "Investigate charging hardware, cables, and charge-cycle failure modes.",
    "connectivity": "Investigate pairing, connection stability, and compatibility across common devices.",
    "sound quality": "Review acoustic tuning and quality-control testing for the reported sound issue.",
    "fit": "Review fit geometry and provide clearer sizing or fit guidance.",
    "comfort": "Review ergonomics, materials, heat buildup, and extended-wear comfort.",
    "build quality": "Investigate component durability and strengthen reliability testing.",
    "noise cancellation": "Investigate noise-control performance and any reported artifacts.",
    "volume control": "Review control design, responsiveness, and volume-range behavior.",
    "customer service": "Review support-response and replacement processes for affected customers.",
    "delivery": "Review delivery handling and customer communication for delayed or damaged orders.",
}


def _priority(negative_review_count: int, review_count: int) -> tuple[str, str]:
    support = negative_review_count / review_count if review_count else 0
    if negative_review_count >= 10 or support >= 0.25:
        return "high", "Repeated negative mentions provide strong support within the available reviews."
    if negative_review_count >= 3 or support >= 0.10:
        return "medium", "Multiple negative mentions justify targeted investigation, although the sample is limited."
    return "low", "This issue appears in few available reviews and should be monitored before a major intervention."


def _summary(product: dict[str, Any]) -> str:
    positives = []
    negatives = []
    for item in product.get("aspects", []):
        counts = item["sentiment_counts"]
        if counts.get("positive", 0):
            positives.append((counts["positive"], item["aspect"]))
        if counts.get("negative", 0):
            negatives.append((counts["negative"], item["aspect"]))
    top_positive = ", ".join(name for _, name in sorted(positives, reverse=True)[:3]) or "no repeated positive aspect"
    top_negative = ", ".join(name for _, name in sorted(negatives, reverse=True)[:3]) or "no repeated negative aspect"
    return f"Based on {product['review_count']} valid extracted reviews, the most frequently positive aspects are {top_positive}; the most frequently negative aspects are {top_negative}."


def build_decision_support(products: list[dict[str, Any]], max_recommendations: int = 3) -> list[dict[str, Any]]:
    """Produce auditable recommendations from counts already present in aggregation."""
    output = []
    for product in products:
        candidates = []
        for item in product.get("aspects", []):
            negative_count = item["sentiment_counts"].get("negative", 0)
            if not negative_count:
                continue
            negative_review_count = item.get("sentiment_review_counts", {}).get("negative", negative_count)
            priority, confidence = _priority(negative_review_count, product["review_count"])
            negative_evidence = []
            seen_reviews = set()
            for entry in item.get("evidence", []):
                if entry["sentiment"] == "negative" and entry["review_id"] not in seen_reviews:
                    negative_evidence.append(entry)
                    seen_reviews.add(entry["review_id"])
            candidates.append({
                "finding": f"Negative feedback on {item['aspect']}",
                "aspect": item["aspect"],
                "negative_mentions": negative_count,
                "negative_review_count": negative_review_count,
                "review_count": product["review_count"],
                "support_rate": round(negative_review_count / product["review_count"], 3),
                "evidence": negative_evidence[:3],
                "suggested_action": ACTION_BY_ASPECT.get(item["aspect"], f"Investigate the reported {item['aspect']} concern and validate it with targeted product testing."),
                "priority": priority,
                "confidence_rationale": confidence,
                "limitation": "Review counts describe mentions in the available extracted sample; they do not prove root cause or population prevalence.",
            })
        candidates.sort(key=lambda item: (-item["negative_mentions"], item["aspect"]))
        output.append({
            "parent_asin": product["parent_asin"],
            "review_count": product["review_count"],
            "summary": _summary(product),
            "recommendations": candidates[:max_recommendations],
        })
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Create evidence-grounded decision-support outputs.")
    parser.add_argument("--input", type=Path, required=True, help="Canonical aggregation JSON file.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    products = json.loads(args.input.read_text(encoding="utf-8"))
    result = build_decision_support(products)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created decision support for {len(result)} products.")


if __name__ == "__main__":
    main()
