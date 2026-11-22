"""Offline ML baseline for review-level customer-issue detection.

The baseline is deliberately narrow: TF-IDF + Logistic Regression predicts
whether a review contains at least one customer issue. It is comparable to the
LLM output by reducing `customer_issues` to the same binary label.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline


def _records(path: Path) -> dict[str, dict[str, Any]]:
    return {record["review_id"]: record for line in path.read_text(encoding="utf-8").splitlines() if line.strip() for record in [json.loads(line)]}


def _prediction_payload(record: dict[str, Any]) -> dict[str, Any]:
    if isinstance(record.get("result"), dict):
        return record["result"]
    if isinstance(record.get("result_json"), str):
        return json.loads(record["result_json"])
    return record


def _metrics(y_true: list[int], y_pred: list[int]) -> dict[str, Any]:
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", zero_division=0)
    matrix = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": sum(actual == predicted for actual, predicted in zip(y_true, y_pred)) / len(y_true),
        "confusion_matrix_labels": ["no_issue", "issue_present"],
        "confusion_matrix": matrix,
    }


def run_baseline(reviews_path: Path, gold_path: Path, llm_predictions_path: Path) -> dict[str, Any]:
    """Evaluate baseline and saved LLM outputs on the same confirmed reference IDs."""
    with reviews_path.open(encoding="utf-8-sig", newline="") as handle:
        reviews = {row["review_id"]: row for row in csv.DictReader(handle)}
    gold = _records(gold_path)
    predictions = _records(llm_predictions_path)
    matched_ids = sorted(set(reviews) & set(gold) & set(predictions))
    texts = [reviews[review_id].get("review_text") or reviews[review_id].get("text") or "" for review_id in matched_ids]
    y_true = [int(bool(gold[review_id].get("customer_issues", []))) for review_id in matched_ids]
    y_llm = [int(bool(_prediction_payload(predictions[review_id]).get("customer_issues", []))) for review_id in matched_ids]
    class_counts = Counter(y_true)
    min_class_count = min(class_counts.values()) if class_counts else 0
    if len(matched_ids) < 4 or min_class_count < 2:
        raise ValueError("Need at least four matched examples and two examples in each class for stratified evaluation.")
    folds = min(5, min_class_count)
    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=5_000, sublinear_tf=True)),
        ("classifier", LogisticRegression(class_weight="balanced", max_iter=1_000, random_state=42, solver="liblinear")),
    ])
    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=42)
    y_baseline = cross_val_predict(model, texts, y_true, cv=splitter, method="predict").tolist()
    return {
        "task": "review-level customer issue detection",
        "positive_label": "issue_present: one or more user-confirmed customer issues",
        "matched_reviews": len(matched_ids),
        "class_distribution": {"no_issue": class_counts[0], "issue_present": class_counts[1]},
        "split_strategy": f"{folds}-fold stratified cross-validation, shuffled with random_state=42",
        "baseline": {"method": "TF-IDF (word unigrams and bigrams) + class-balanced Logistic Regression", "metrics": _metrics(y_true, y_baseline)},
        "llm": {"method": "Saved Gemini extraction; positive when customer_issues is non-empty", "metrics": _metrics(y_true, y_llm)},
        "limitations": [
            f"The reference set contains only {len(matched_ids)} reviews, so results are exploratory and have high uncertainty.",
            "The baseline is comparable only for binary customer-issue detection, not the full structured extraction task.",
            "The LLM outputs are pre-existing predictions on the same reviewed inputs; they are not trained on these labels.",
            "Most expansion labels began as AI-assisted drafts before user confirmation, so the saved-LLM comparison may be optimistic and is not an independent generalization estimate.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate an ML baseline against saved LLM issue detection.")
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--llm-predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run_baseline(args.reviews, args.gold, args.llm_predictions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
