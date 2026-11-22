# Canonical Label Policy v3

## Purpose

This policy supports a separate canonical-label consistency evaluation. It does not replace raw extraction output or raw exact-string evaluation. Both the original and fresh extraction runs use the same deterministic rules before comparison.

## Scope

The policy covers aspects, customer issues, feature requests, use cases, positive points, and negative points. It maps only explicit, recurring variants. Any phrase without a documented mapping remains normalized but otherwise unchanged.

## Development and freeze rule

The mappings were developed from the complete original 1,632-record schema-valid extraction checkpoint. The fresh-run outputs and their mismatches were not used to tune the rules. The policy is frozen as version `2026-10-28-v3` before it is applied to the fresh-comparison records.

## Normalization applied to every value

- Convert to lowercase.
- Replace hyphens, underscores, and slashes with spaces.
- Collapse repeated spaces.

## Field-specific mappings

### Aspects

Existing aspect aliases remain in use. Examples: `noise-cancelling` and `noise reduction` map to `noise cancellation`; `sound` maps to `sound quality`; and `battery` maps to `battery life`.

### Customer issues

Documented exact aliases and conservative keyword patterns map recurring concepts to `battery or charging problem`, `connectivity problem`, `poor durability`, `discomfort`, `poor fit`, `volume or controls problem`, `audio quality problem`, `cable problem`, and `service or delivery problem`.

### Feature requests

Explicit variants map to requests such as `improve volume control`, `improve bass`, `improve comfort`, `improve cable`, `add or improve microphone`, `improve fit`, `improve connectivity`, and `improve durability`.

### Use cases

Only common activity/context variants are grouped: exercise/gym/running terms map to `exercise`; phone-call terms map to `making calls`; music-listening variants map to `listening to audio`; and recurring work, gaming, travel/commute, yard-work, and sleeping contexts receive separate labels.

### Positive points

Common positive variants are grouped into `good sound quality`, `comfortable fit`, `good fit`, `good value`, `good battery life`, `effective noise cancellation`, `good durability`, `good microphone`, `good cable`, `good connectivity`, `easy to use`, and `works well`.

### Negative points

Common negative variants are grouped into the same field-specific problem concepts as customer issues, plus `poor value` and `functional failure` where the phrase explicitly states that the product does not work.

## Limitations

- Canonical agreement is concept-level consistency, not a replacement for raw exact-string agreement.
- Broad mappings can hide useful distinctions, so uncertain or compound phrases remain unchanged.
- The original phrase and its review evidence remain the traceability source.
- The policy may require revision for new domains or unseen review language; a new version must be created rather than silently changing this one.
