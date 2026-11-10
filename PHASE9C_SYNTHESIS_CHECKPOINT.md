# Phase 9C — transparent synthesis and decision ledger (offline prototype)

Date: 2026-11-10. Status: draft for review; no production migration.

## Scope

`evidence_synthesis.py` turns manually reviewed, individually sourced study findings into an inspectable **descriptive evidence map** for a precisely defined research question. It counts direction labels, displays limitations, source pages, populations, review status and applicability judgments; it highlights contradictory or unclear findings without converting votes into proof. Proposed educational decisions are recorded as drafts with rationale and counterevidence.

## Explicit constraints

- Only human-verified evidence with a URL, locator, reviewer and caveats is eligible for display in the included evidence map.
- Study finding must match the question's CEFR level, skill and outcome; currently no synonym matching or validated cross-level generalization.
- Duplicate study IDs are not counted twice; repeated papers with different IDs require upstream 9B deduplication and human check.
- Unknown applicability remains visible, not silently promoted to direct applicability.
- Numerical effect estimation, certainty rating, bias assessment, meta-analysis, causality and educational efficacy decisions are **not implemented**. The output explicitly sets `certainty=not_assessed`, `effect_estimate=null` and `decision=not_authorized`.
- A favorable direction count is never an automatic recommendation. The decision record requires independent review, documented contrary evidence and reasoned approval.
- Populations should be assessed for differences in first language, age, starting proficiency, context, access and instructional intensity before extrapolating to Arabic-speaking learners.
- This is a research instrument, not a CEFR test or validated scientific synthesis.

## Follow-up to reach evidence-based decisions

1. Collect a human-adjudicated benchmark of actual study records covering speaking, listening, writing, reading and pronunciation with DOI/pages and permissions.
2. Record outcome measurements, effect metrics, uncertainty and risk of bias using study-design-appropriate methods; obtain methodology specialist review.
3. Implement explicit overlap, independence and publication-bias checks; do not treat correlated reports as independent experiments.
4. Version the synthesis and write a reviewer-facing audit log and revocation trail, including rationale when recommendations change.
5. Test claims against counterevidence and external experts, then integrate admin-only UI and data storage after access-control review.

Methodological inspiration: Cochrane Handbook, chapter 14 (https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-14). It differentiates synthesis and certainty of the **body of evidence** from a count of individual study findings. Our prototype does not implement GRADE.
