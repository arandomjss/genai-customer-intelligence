# Human annotation guidelines

Use the title and review body together, with the title first. Only label information explicitly stated by the customer. Do not turn a general opinion into a precise defect or feature request.

- **Aspects:** short, reusable noun phrases (for example, `sound quality`, `battery life`, `fit`, `durability`). Do not use `overall` unless the review contains no identifiable feature.
- **Aspect sentiment:** create one entry per stated aspect; use `positive`, `negative`, or `neutral`; copy the shortest supporting phrase as evidence.
- **Customer issues:** observed problems or failures. A prospective worry is not an issue.
- **Feature requests:** only explicit desired changes (for example, “I wish it had…”). Do not infer requests from complaints.
- **Use cases:** an activity or setting stated in the review (for example, `running`).
- **Positive/negative points:** concrete strengths or weaknesses, preferably concise paraphrases.
- **Summary:** one factual sentence. It must not introduce information beyond the review.

For each annotation, preserve `review_id`. A second annotator should independently label at least 20 reviews before disagreements are reconciled. Record unresolved ambiguities in a `notes` field; do not silently force agreement.
