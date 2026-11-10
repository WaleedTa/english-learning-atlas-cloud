# Phase 9B — reproducible study screening (offline prototype)

Date: 2026-11-10. Status: review draft, not integrated with production database.

## Scientific workflow

1. **Register question and inclusion/exclusion criteria before screening.** Include learner population, CEFR level, target skill, intervention, comparator, and measurable outcomes. Changing criteria requires a new protocol version and documented rationale.
2. **Discover studies** from authorized scientific sources with source query, date, search scope, and source IDs.
3. **Deduplicate conservatively**: DOI first; otherwise canonical HTTPS URL; otherwise exact normalized title + valid publication year. Unresolved records remain for human inspection.
4. **Title/abstract screening** by at least two independent reviewers; save include/exclude/uncertain and an explicit reason. Different or uncertain votes go to adjudication.
5. **Full-text screening** with retrieval-status tracking and explicit reason on exclusion. Unavailable full text cannot be silently treated as excluded for methodological reasons.
6. **Extract and appraise** complete evidence using the phase 9A source-locator, reviewer and limitation gates; record study design, biases, outcomes and contradictory results.
7. **Report** flow counts and source identities; use PRISMA 2020 reporting guidance where a formal systematic review is actually undertaken.
8. **Benchmark automation** against adjudicated human labels: report precision, recall, disagreements, false-negative case studies, and coverage of source types and learner subgroups.

## What is implemented here

- `research_screening.py`: deterministic conservative DOI/URL/title-year deduplication, immutable protocol/decision objects, independent reviewer reconciliation, benchmark precision/recall, and flow-count consistency checks.
- `tests/test_research_screening.py`: 11 offline checks covering deduplication, reviewer conflict, missing criteria, metrics and contradictory counts.
- **No** automatic paper inclusion, unverified study exclusion, LLM extraction, source crawling, publication, database writes, or actual review completed.

## Known methodological limits

- Conservative matching cannot detect every duplicate; title-year matching can still falsely merge distinct records with identical titles and years. Such merges must be inspectable/reversible before production use.
- Two reviewers agreeing does not alone establish eligibility, methodological quality, or valid evidence. Real screening requires reviewer independence, documented criteria, training and calibration.
- `screening_metrics` runs on supplied adjudicated labels and cannot infer generalization, statistical confidence, prevalence, or actual performance from a few fixtures.
- PRISMA is a reporting guideline, not proof of review quality. `prisma_counts` validates only basic flow arithmetic, not all PRISMA requirements.
- No fabricated efficacy, learner improvement, classifier accuracy or reliability estimates.

## Next gate before production

Create a small **licensed, human-labeled English teaching research benchmark** across pronunciation, listening, speaking, reading, writing and vocabulary. Define two-reviewer adjudication and independent assessment of any AI-assisted screening. After approval, design the Supabase persistence/RLS and an admin-only bilingual screening interface; keep public-facing decisions dependent on validated evidence.

Primary references:
- PRISMA 2020: https://www.prisma-statement.org/prisma-2020
- ASReview documentation: https://asreview.readthedocs.io/en/stable/
