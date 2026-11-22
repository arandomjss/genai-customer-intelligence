"""
Gemini LLM provider.

This module contains Gemini-specific API interaction.
The rest of the extraction pipeline should use BaseLLMProvider
rather than directly interacting with the Gemini SDK.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any

from google import genai
from dotenv import load_dotenv

from .base_provider import BaseLLMProvider

# Load the project-local secret file when this module is used from a notebook,
# a CLI command, or another working directory. Existing shell variables win.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


class GeminiProvider(BaseLLMProvider):
    """Gemini implementation of the common LLM provider interface."""

    def __init__(
        self,
        model_name: str = "gemini-3.5-flash-lite",
        api_key: str | None = None
    ):
        self.model_name = model_name

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY was not found."
            )

        self.client = genai.Client(
            api_key=self.api_key
        )

    def extract(
        self,
        review_text: str,
        review_id: str | None = None
    ) -> Dict[str, Any]:
        """
        Extract structured information from a customer review.

        The extraction schema is enforced through JSON output.
        """

        if not review_text or not review_text.strip():
            raise ValueError(
                "review_text must contain non-empty text."
            )

        prompt = f"""
You are performing structured customer intelligence extraction
from an e-commerce customer review.

Extract ONLY information explicitly supported by the review.

Return valid JSON with exactly these fields:

{{
  "aspects": [],
  "aspect_sentiments": [],
  "customer_issues": [],
  "feature_requests": [],
  "use_cases": [],
  "positive_points": [],
  "negative_points": [],
  "review_summary": ""
}}

Rules:

1. Do not invent information.
2. Use empty arrays when no information is present.
3. "aspect_sentiments" must contain objects with:
   - aspect
   - sentiment
   - evidence
4. sentiment must be exactly:
   - positive
   - negative
   - neutral
5. Evidence must be a short phrase supported by the review.
6. "customer_issues" contains actual problems experienced.
7. "feature_requests" contains only explicit requests or desired
   improvements. Do not infer requests.
8. "use_cases" describes how the customer uses the product.
9. "positive_points" contains concrete positive experiences.
10. "negative_points" contains concrete negative experiences.
11. "review_summary" should be short and factual.
12. If the review is too short to extract meaningful information,
    return empty arrays and a concise factual summary.
13. Do not treat a complaint, product limitation, or conditional statement
    as a use case. A use case must be an activity or setting the customer
    explicitly says they used the product for.
14. Preserve uncertainty in the review. Words such as "seems", "looks",
    "might", and "didn't seem" do not prove performance or durability;
    either retain that uncertainty in the label/summary or omit the claim.
15. Do not turn appearance, expectation, or a prediction into a confirmed
    product attribute. For example, "durability looks good" is not proof of
    durability.
16. Prefer concise, reusable aspect names such as "sound quality", "fit",
    "battery display", "charging", and "connectivity". Do not use a vague
    "overall" aspect for a review with no identifiable product feature.

Customer review:

{review_text}
"""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config={
                "response_mime_type": "application/json"
            }
        )

        raw_text = response.text.strip()

        try:
            result = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Gemini returned invalid JSON"
                f"{f' for {review_id}' if review_id else ''}:\n"
                f"{raw_text}"
            ) from exc

        return result
