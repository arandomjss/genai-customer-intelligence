# GenAI-Powered Customer Intelligence from E-Commerce Reviews

## Project goal

**Project title:** GenAI-Powered Customer Intelligence & Decision Support System Using E-Commerce Reviews

### Business problem

E-commerce businesses receive large volumes of customer reviews. Manual reading is time-consuming and inconsistent, while star ratings alone do not explain which features customers value, what problems recur, or what a product team should improve first. This project turns review text into traceable product-level insights and practical recommendations to support product and customer-experience decisions.

### Objective

Build an end-to-end Generative AI pipeline that converts public reviews into structured, evidence-grounded customer/product intelligence and actionable recommendations. This is a university GAI project, not a generic chatbot or thin API wrapper.

Core deliverables:

- Reproducible data preparation and structured review extraction
- Aspect-level sentiment, issues, feature requests, use cases, strengths, and weaknesses
- Product-level aggregation and cross-product comparison
- Evidence-grounded product summaries linked to source review IDs
- **Actionable recommendations** with evidence, rationale, and transparent priority/confidence
- Human-reviewed extraction evaluation
- **A simple ML baseline** for a clearly defined task, compared on compatible held-out examples
- A decision-support demonstration, report, presentation, and limitations

**RAG is not part of the current scope.** The focus is extraction, aggregation, evaluation, and evidence-backed decision support.

## Project environment

- Project root: `C:\Users\91738\OneDrive\Desktop\coding\SEM 7\GAI\GAI_Project`
- Python 3.11, `.venv`, Jupyter kernel `Python 3.11 (GAI Project)`
- Workflow: VS Code and Jupyter notebooks
- LLM provider: Google Gemini
- Model reported by the latest successful batch run: `gemini-3.5-flash-lite`. Verify the current provider configuration and API availability before changing it; never guess model IDs.
- Keep API keys in `.env`; never commit, print, or copy secrets into source code or documentation.

## Dataset

The project began with the Amazon Reviews 2023 dataset released by the McAuley Lab / UC San Diego. Raw Electronics files previously documented:

- `data/raw/meta_Electronics.jsonl.gz`
- `data/raw/reviews_Electronics.jsonl.gz`

Raw data is immutable.

Reported processed artifacts (verify files/counts before treating these as current):

| Artifact                                                         | Reported contents                                  |
| ---------------------------------------------------------------- | -------------------------------------------------- |
| `data/processed/cleaned_product_reviews.csv`                   | 21,609 reviews, 95 unique products                 |
| `data/processed/sampled_product_reviews_100.csv`               | 4,939 rows, 95 products, up to 100 reviews/product |
| `data/processed/extraction_schema.json`                        | Eight-field extraction schema                      |
| `data/processed/extraction_test/extraction_test_input.csv`     | 20 deterministic test reviews                      |
| `data/processed/extraction_test/extraction_test_results.jsonl` | Checkpointed extraction results                    |
| `data/processed/extraction_test/extraction_test_results.csv`   | Tabular extraction results                         |

The sampled dataset was reported to contain columns `parent_asin`, `asin`, `rating`, `title`, `text`, `timestamp`, `verified_purchase`, `helpful_vote`, and `review_text`. The reported per-product range was 1–100 reviews; do not claim every product has 100 reviews.

## Extraction schema

The authoritative schema is `data/processed/extraction_schema.json`. Its eight fields are:

1. `aspects`
2. `aspect_sentiments` — objects with `aspect`, `sentiment` (`positive`, `negative`, `neutral`), and `evidence`
3. `customer_issues`
4. `feature_requests`
5. `use_cases`
6. `positive_points`
7. `negative_points`
8. `review_summary`

Read the actual schema before changing fields or validators. Coordinate schema changes across prompts, code, tests, and docs.

## Decision-support outputs

The final system should help a product/customer-experience decision-maker answer:

- What do customers consistently praise or complain about for each product?
- Which issues and feature requests recur most often?
- How do products compare on specific aspects?
- What should the team investigate or improve first, and what evidence supports that recommendation?

Product-level findings should include transparent counts/support measures where available, representative review evidence, and source review/product IDs. Generated summaries must not invent statistics or make unsupported causal claims.

### Actionable recommendation format

Each recommendation should, where evidence permits, state:

1. The observed issue or opportunity.
2. Supporting evidence (review IDs/examples and frequency or another transparent support measure).
3. A specific suggested action.
4. Intended customer/business impact and rationale.
5. Priority/confidence rationale based on frequency, severity, evidence strength, and relevant rating context.
6. Important uncertainty or limitation.

Recommendations are a core deliverable. State when evidence is too weak to justify a recommendation rather than filling gaps with speculation.

## ML baseline and evaluation plan

Implement a modest ML baseline for a task supported by the available human-reviewed labels and class distribution. A candidate is TF-IDF plus Logistic Regression or a linear SVM for a well-defined sentiment/aspect classification task. Confirm the task after inspecting labels; do not imply this baseline covers all LLM extraction fields unless the tasks are genuinely comparable.

- Use a documented train/validation/test split or suitable cross-validation, preventing review-level leakage.
- Compare baseline and GenAI on the same compatible held-out examples.
- Report precision, recall, F1, and per-class results where useful.
- Evaluate semantic extraction quality separately from schema validity and evidence grounding.
- Document annotation policy, split strategy, limitations, and uncertainty.
- Treat baseline results as planned until code has run and metrics have been calculated.

### Simple Dashboard (Planned Deliverable)

The project will include a simple, interactive **Streamlit dashboard** that presents the outputs of the customer intelligence pipeline in an accessible, decision-oriented format.

The dashboard will allow a product or business decision-maker to:

- **Explore individual products:** Select a product and view its customer-feedback insights.
- **View key metrics:** Display the number of reviews, sentiment distribution, and common positive and negative aspects.
- **Identify recurring problems:** Explore frequently mentioned customer issues and feature requests, supported by representative customer reviews.
- **Compare products:** Compare customer feedback, sentiment, and aspects across products where sufficient data is available.
- **Review recommendations:** View actionable product or customer-experience recommendations, including supporting evidence, rationale, and priority or confidence.
- **Trace insights to evidence:** Link findings back to the original review text and relevant product/review IDs wherever possible.

**Implementation approach:** Streamlit will be used to build a lightweight Python-based interface. The dashboard will present results from the existing extraction, evaluation, and aggregation pipeline rather than duplicate its logic.

The dashboard will be implemented after the core pipeline and evaluation are sufficiently reliable. It is a planned deliverable and must not be described as completed until it has been implemented and tested.

## Research questions

1. How reliably can an LLM extract aspects, aspect sentiment, issues, feature requests, and use cases from reviews?
2. How does the GenAI approach compare with a simple ML baseline on a clearly defined, compatible task?
3. How can review-level extractions become traceable product-level patterns?
4. Can the evidence support useful, specific, appropriately qualified product/customer-experience recommendations?

## Implementation

Provider files previously created:

- `app/llm/__init__.py`
- `app/llm/base_provider.py`
- `app/llm/gemini_provider.py`

The Gemini implementation uses the Google GenAI client pattern `self.client.models.generate_content(model=self.model_name, contents=prompt, config=...)`. Verify actual source before editing. A previous notebook cell was reported to rewrite `gemini_provider.py` with an older hard-coded model default; inspect any source-writing cell before rerunning it.

The provider architecture should remain modular so the pipeline is not tightly coupled to one vendor.

## Verified extraction test

The single-review smoke test and 20-review batch were reported as successful:

- 20 reviews processed
- 20 schema-valid outputs
- 0 validation failures
- 0 API/processing failures
- one attempt per review
- `BATCH STATUS: PASSED`
- model printed: `gemini-3.5-flash-lite`

This proves the tested calls completed and passed the implemented structural validation. It does **not** prove semantic accuracy. Human evaluation is needed to detect missed aspects, unsupported claims, weak evidence, inconsistent labels, and incomplete issue extraction.

Preliminary review of the outputs raised questions about generic `overall` aspects on very short reviews, inconsistent/awkward aspect labels, broad dissatisfaction not always represented as an issue, nuanced statements, and whether the title should be included with the review body. Treat these as observations to test, not automatically confirmed errors.

## Current status snapshot

### Demonstrated

- Local environment and notebook workflow
- Source dataset download and initial reconnaissance
- Cleaned and sampled review datasets reported above
- Eight-field extraction schema
- Gemini provider integration
- Single-review smoke test passed
- 20-review batch passed structural validation and saved JSONL/CSV results

### Still to verify or complete

- Expand and document the human-reviewed reference set and holdout strategy
- Improve and report semantic extraction quality, evidence grounding, and limitations
- Complete extraction and aggregation of the remaining sampled rows
- Build and evaluate a suitable ML baseline on a compatible held-out task
- Generate evidence-grounded product summaries and cross-product comparisons
- Produce prioritized actionable recommendations with evidence and explicit uncertainty
- Complete the decision-support demonstration, report, and slide deck

### Verified current execution — 2026-10-24

- `pilot.jsonl`: 5 reviews processed successfully; 5 schema-valid results; zero invalid or failed records.
- `pilot_v2.jsonl`: the same five reviews rerun after prompt safeguards for uncertainty, vague aspects, and inferred use cases.
- `full_sample.jsonl`: first 100 sampled reviews processed successfully; 100 schema-valid results; zero invalid or failed records.
- `full_sample_100_canonical.json`: aggregation of those 100 records across 4 products. It preserves review IDs, evidence, original model labels, and canonical aspect labels. It is an interim result, not an evaluation metric or a final product claim.
- `full_sample_485_canonical.json`: interim canonical aggregation of 485 valid records across 12 products. The attempted 500-row expansion reached the Gemini free-tier daily request quota; 114 failed calls and one invalid response were retained in the checkpoint rather than omitted.
- `gold_annotations.jsonl`: a user-confirmed, AI-assisted 100-review reference set combining deterministic test and production examples. It is balanced at 50 issue-present and 50 no-issue reviews.
- `evaluation_report_100.json`: per-review micro exact-string comparison of 100 saved LLM predictions. Aspect extraction: precision 0.877, recall 0.892, F1 0.885. Customer issues: F1 0.798. Exact-string metrics do not measure semantic equivalence or evidence grounding.
- The runner now retries previously failed records after quota recovery while continuing to skip terminal `SUCCESS` and `INVALID` records.

This is a status snapshot, not a claim that no further work has happened. Inspect the repository and outputs before deciding what remains.

## Recommended next steps

1. Inspect the repository, notebook, schema, provider, and saved batch outputs.
2. Compare the 20 model outputs against their source reviews.
3. Define annotation rules for aspects, sentiment, evidence, issues, feature requests, summaries, and title/body handling.
4. Build a small human-reviewed reference set.
5. Improve prompts or normalization based on observed errors, then rerun the test.
6. Scale to the sampled dataset with checkpoints and explicit failure records.
7. Aggregate results by product and compare products where meaningful.
8. Generate product summaries grounded in review evidence.
9. Build and evaluate the ML baseline on a compatible held-out task.
10. Produce actionable recommendations with traceable evidence, rationale, and priority.
11. Prepare the decision-support demo, report, and presentation.

## Design principles

- Keep raw datasets immutable.
- Put derived data in `data/interim/`, `data/processed/`, and `data/validation/`.
- Keep reusable code in modules; notebooks should orchestrate experiments, not duplicate large implementations.
- Record seeds and key parameters.
- Preserve review/product IDs and supporting evidence.
- Keep raw outputs and validation outcomes where useful.
- Never silently drop failed records.
- Do not claim metrics unless actually calculated against a suitable reference set.
- Build the interface after the data pipeline and evaluation are credible.
- Make the business problem and decision-support use case visible in the final demo.
- Treat recommendations as evidence-backed outputs, not free-form speculation.
- Keep RAG out of scope unless the user explicitly approves a scope change.

## Current implementation

The repository now includes a reusable, command-line pipeline under `app/pipeline/`:

- `schema.py` performs strict structural validation and conservative normalization of all eight extraction fields.
- `extract.py` runs Gemini extraction with append-only JSONL checkpoints. It records successes, invalid model outputs, and exceptions separately; re-running skips already recorded `review_id` values.
- `aggregate.py` turns valid extraction records into product-level aspect counts, issue/request rankings, and review-ID-linked evidence. It can read both the original notebook result format and new runner output.
- `canonicalization.py` applies versioned, deterministic mappings. Product aggregation retains the original aspect label next to its evidence; the separate evaluation policy also defines cautious mappings for issues, requests, use cases, and positive/negative points.
- `evaluate.py` calculates strict raw exact-string consistency. It keeps the latest schema-valid `SUCCESS` record per review ID, so a later failed retry cannot replace valid output.
- `evaluate_canonical.py` calculates a separate canonical-label consistency score using the frozen policy in `data/validation/canonical_label_policy_v3.md`. It does not overwrite raw outputs or replace exact-string metrics.
- `recommend.py` creates deterministic product summaries and recommendations from canonical aggregation counts. Each recommendation retains evidence, support counts, priority rationale, and an explicit limitation.
- `app/dashboard.py` is the Streamlit decision-support interface for the saved 485-review artifacts. It includes product exploration, aspect sentiment, evidence, recommendation, review-trace, and comparison views.

`data/validation/ANNOTATION_GUIDELINES.md` defines the human-review policy. `gold_annotations_template.jsonl` is deliberately only a template, not claimed annotation data.

## Run the pipeline

First repair or recreate the project virtual environment if necessary, then install the small dependency set:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run a deliberately bounded pilot before any larger paid API run. The runner refuses to run without `--limit`:

```powershell
python -m app.pipeline.extract --input data\processed\extraction_test\extraction_test_input.csv --output data\processed\extraction_runs\pilot.jsonl --limit 5 --delay 1
python -m app.pipeline.aggregate --input data\processed\extraction_runs\pilot.jsonl --output data\processed\product_intelligence\pilot.json
```

Run the strict raw exact-string comparison and the separate canonical-label comparison with:

```powershell
python -m app.pipeline.evaluate --predictions data\processed\extraction_runs\full_sample.jsonl --gold data\validation\fresh_annotation_raw_250.jsonl --output data\validation\raw_exact_string_evaluation_250.json
python -m app.pipeline.evaluate_canonical --original data\processed\extraction_runs\full_sample.jsonl --fresh data\validation\fresh_annotation_raw_250.jsonl --output data\validation\canonical_label_evaluation_250.json
```

The first 100-record production batch completed with no recorded extraction failures. Continue in bounded batches and inspect each canonical aggregation. A full run remains resumable because each result is appended and flushed immediately.

## Decision-support dashboard

Generate or refresh decision support after canonical aggregation:

```powershell
python -m app.pipeline.recommend --input data\processed\product_intelligence\full_sample_485_canonical.json --output data\processed\product_intelligence\decision_support_485.json
```

Launch the local dashboard:

```powershell
python -m pip install -r requirements.txt
streamlit run app\dashboard.py
```

The dashboard consumes saved pipeline artifacts and never calls Gemini. Its recommendations identify review-supported issues to investigate; they do not prove root cause.

## Verification

The repository includes offline unit tests in `tests/test_pipeline.py`; they use a fake provider and do not send API calls:

```powershell
python -m unittest discover -v
```

## End-to-end workflow

```text
Public E-commerce Reviews
  -> Reproducible Cleaning and Sampling
  -> Structured LLM Extraction
  -> Human-Reviewed Evaluation
  -> ML Baseline on a Compatible Task
  -> Product-Level Aggregation and Comparison
  -> Evidence-Grounded Product Summaries
  -> Actionable Recommendations and Priorities
  -> Decision-Support Demonstration
  -> Report and Presentation
```

The project should demonstrate not just valid JSON, but useful, traceable insights, honest evaluation, an interpretable baseline comparison, and recommendations a product/customer-experience team could investigate or act on. RAG is explicitly excluded from the current scope.
