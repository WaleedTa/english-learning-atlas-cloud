# Phase 4 — Evidence discovery engine (initial implementation)

## What works
- Metadata discovery adapters: OpenAlex, Crossref, Europe PMC.
- A separate curated directory of 19 frameworks, indexes, applications, communities and open-source entry points. Directory items are **not crawled** or verified automatically.
- Thirteen topic queries, skills/methods/framework tags, DOI-based deduplication, source provenance, retrieval timestamps.
- Weekly GitHub Actions job and manual trigger; uploads JSONL candidate artifact and coverage CSV.
- A protected Supabase `atlas_discoveries` table. New entries are pending and invisible to the public until human review.
- The existing 159 OpenAlex records in `atlas_resources` are preserved.

## How to run
`python -m pip install requests`
`python research_engine.py --output research_output --per-query 8`

Use Actions → **Phase 4 multi-source discovery (review required)** → Run workflow. Download artifact `phase4-research-candidates`. The artifact is **not automatically imported** into Supabase; do not confuse discovery with publication. The current Streamlit dashboard has not yet been extended to import/review these JSONL records.

## What is NOT implemented
- Full-web crawling or scraping of arbitrary sites, forums and apps; source-specific adapters require API/robots/ToS review.
- Automated scientific conclusions, full-text review, causal claims, meta-analysis, model-based extraction, scoring calibration, or cross-framework score equivalence.
- Semantic/vector search, public machine-readable API, systematic coverage evaluation, scheduled direct Supabase ingestion, or testing learning effectiveness with participants.
- The three source adapters are implemented but require a live workflow run to verify availability and coverage.

## Evidence policy
A citation count is not a quality score. A title/abstract keyword is only a candidate tag, not a validated classification. Product marketing claims and forum anecdotes are separate from controlled studies. Any future comparative effectiveness score needs study design, population, baseline, outcomes, effect size, uncertainty, bias, replication, conflicts of interest and a documented human decision.

## Frameworks and evaluation
CEFR, ACTFL, ILR, GSE, CLB, Cambridge English Scale, IELTS, TOEFL, and PTE are distinct frameworks/tests. Their scores cannot be directly treated as interchangeable; mapping requires official linking studies and uncertainty. Also track comprehension, production, interaction, mediation, lexical range, pronunciation, fluency, writing, retention, transfer, accessibility, and learner context.

## Planned next increments
1. Authenticated importer and review UI for `atlas_discoveries` with audit log and per-source details.
2. Extend adapters to ERIC, Semantic Scholar, Open Library, GitHub and provider catalogs as permitted.
3. Build evidence extraction workflow, reviewer rubric, contradictory-results tracker, and comparison explorer.
4. Read-only JSON API for human and AI consumers, with provenance and licensing controls.
