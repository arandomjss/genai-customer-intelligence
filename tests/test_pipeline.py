import json
import tempfile
import unittest
from pathlib import Path

from app.pipeline.aggregate import aggregate_extractions
from app.pipeline.canonicalization import canonicalize_aspect, canonicalize_field_value
from app.pipeline.evaluate_canonical import evaluate_canonical
from app.pipeline.extract import run_extraction
from app.pipeline.evaluate import evaluate
from app.pipeline.recommend import build_decision_support
from app.pipeline.schema import validate_extraction


VALID = {
    "aspects": ["sound quality"],
    "aspect_sentiments": [{"aspect": "sound quality", "sentiment": "positive", "evidence": "sound is good"}],
    "customer_issues": [], "feature_requests": [], "use_cases": [],
    "positive_points": ["good sound"], "negative_points": [], "review_summary": "The sound is good."
}


class FakeProvider:
    def extract(self, review_text, review_id=None):
        return VALID


class PipelineTests(unittest.TestCase):
    def test_schema_rejects_invalid_sentiment(self):
        invalid = json.loads(json.dumps(VALID))
        invalid["aspect_sentiments"][0]["sentiment"] = "mixed"
        self.assertTrue(validate_extraction(invalid))

    def test_canonicalizes_documented_aliases(self):
        self.assertEqual(canonicalize_aspect("noise-cancelling"), "noise cancellation")
        self.assertEqual(canonicalize_aspect("case"), "carrying case")
        self.assertEqual(canonicalize_field_value("use_cases", "working out"), "exercise")
        self.assertEqual(canonicalize_field_value("positive_points", "Great sound"), "good sound quality")
        self.assertEqual(canonicalize_field_value("negative_points", "Headset broke after a month"), "poor durability")
        self.assertEqual(canonicalize_field_value("customer_issues", "Cannot pair with phone"), "connectivity problem")
        self.assertEqual(canonicalize_field_value("customer_issues", "new phrase"), "new phrase")

    def test_checkpoint_and_aggregation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, results, products = root / "reviews.csv", root / "results.jsonl", root / "products.json"
            source.write_text("parent_asin,review_text\nP1,sound is good\n", encoding="utf-8")
            self.assertEqual(run_extraction(source, results, FakeProvider()), {"skipped": 0, "success": 1, "invalid": 0, "failed": 0})
            self.assertEqual(run_extraction(source, results, FakeProvider())["skipped"], 1)
            output = aggregate_extractions(results, products)
            self.assertEqual(output[0]["review_count"], 1)
            self.assertEqual(output[0]["aspects"][0]["aspect"], "sound quality")

    def test_failed_record_is_not_treated_as_complete(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, results = root / "reviews.csv", root / "results.jsonl"
            source.write_text("review_id,parent_asin,review_text\nR1,P1,sound is good\n", encoding="utf-8")
            results.write_text('{"review_id":"R1","status":"FAILED"}\n', encoding="utf-8")
            self.assertEqual(run_extraction(source, results, FakeProvider())["success"], 1)

    def test_evaluation_does_not_match_labels_across_reviews(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            predictions, gold = root / "predictions.jsonl", root / "gold.jsonl"
            predictions.write_text('{"review_id":"R1","result":{"aspects":["fit"]}}\n{"review_id":"R2","result":{"aspects":["sound"]}}\n', encoding="utf-8")
            gold.write_text('{"review_id":"R1","aspects":["sound"]}\n{"review_id":"R2","aspects":["fit"]}\n', encoding="utf-8")
            self.assertEqual(evaluate(predictions, gold)["fields"]["aspects"]["f1"], 0.0)

    def test_evaluation_ignores_failed_retry_after_success(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            predictions, gold = root / "predictions.jsonl", root / "gold.jsonl"
            predictions.write_text(
                '{"review_id":"R1","status":"SUCCESS","schema_valid":true,"result":{"aspects":["fit"]}}\n'
                '{"review_id":"R1","status":"FAILED","schema_valid":false,"result":null}\n',
                encoding="utf-8",
            )
            gold.write_text('{"review_id":"R1","aspects":["fit"]}\n', encoding="utf-8")
            self.assertEqual(evaluate(predictions, gold)["fields"]["aspects"]["f1"], 1.0)

    def test_canonical_evaluation_matches_documented_variants(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original, fresh = root / "original.jsonl", root / "fresh.jsonl"
            original.write_text(
                '{"review_id":"R1","status":"SUCCESS","schema_valid":true,"result":{"aspects":["noise-cancelling"],"customer_issues":[],"feature_requests":[],"use_cases":["working out"],"positive_points":["Great sound"],"negative_points":[]}}\n',
                encoding="utf-8",
            )
            fresh.write_text(
                '{"review_id":"R1","status":"SUCCESS","schema_valid":true,"result":{"aspects":["noise reduction"],"customer_issues":[],"feature_requests":[],"use_cases":["gym"],"positive_points":["good sound quality"],"negative_points":[]}}\n',
                encoding="utf-8",
            )
            report = evaluate_canonical(original, fresh)
            self.assertEqual(report["matched_reviews"], 1)
            self.assertEqual(report["fields"]["aspects"]["f1"], 1.0)
            self.assertEqual(report["fields"]["use_cases"]["f1"], 1.0)

    def test_recommendations_keep_evidence_and_limitations(self):
        product = {"parent_asin": "P1", "review_count": 4, "aspects": [{"aspect": "charging", "sentiment_counts": {"negative": 2}, "evidence": [{"review_id": "R1", "evidence": "would not charge", "sentiment": "negative", "original_aspect": "charging"}]}]}
        result = build_decision_support([product])[0]["recommendations"][0]
        self.assertEqual(result["aspect"], "charging")
        self.assertEqual(result["negative_review_count"], 2)
        self.assertEqual(result["evidence"][0]["review_id"], "R1")
        self.assertIn("do not prove", result["limitation"])


if __name__ == "__main__":
    unittest.main()
