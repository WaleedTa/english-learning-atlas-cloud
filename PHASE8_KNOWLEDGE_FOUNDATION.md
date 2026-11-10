# Phase 8 — Unified knowledge and evidence foundation (draft)

Date: 2026-11-10. Status: **proposed for review**, not deployed.

## What this adds

1. `data/reference_projects.json`: 15 previously examined GitHub projects, each with a stable slug, canonical source URL, descriptive research focus, and license label or `unverified`.
2. `scripts/validate_reference_projects.py`: repeatable offline checks for duplicate references, malformed URLs, missing metadata and unreviewed outcome claims.
3. `supabase/phase8_knowledge_proposal.sql`: **not executed**. Admin-only project index plus separately traceable claims and cited evidence; claims can refer to existing `atlas_discoveries` studies.
4. Offline unit tests; no writes to the existing 159 studies, 310 discoveries, review records or production auth settings.

## Critical interpretation rules

- `focus` tags are **investigation categories**, not independently validated functionality or learning gains.
- Repository links and project names identify research targets; license labels reflect earlier research and need a date-stamped source check before any code/content reuse.
- Do not infer student outcomes, community ratings, official endorsements or legal reuse rights from GitHub metadata.
- Individual findings must be added as `atlas_project_claims`, each with a source, caveats, reviewer, review status and (when applicable) academic discovery reference.
- Project and claim tables are intentionally private to admins, including approved rows. A future public API must separately define an evidence-backed publication policy.

## Remaining work before production

- Check current licenses, repository activity and product claims from primary sources; log the exact revision and retrieval date.
- Have Waleed review the SQL, auth permission model, and a backup/rollback plan before running any production migration.
- Test anon/non-admin/admin reads and writes, approval integrity and end-to-end import with a real admin login.
- Build comparisons on **verified claims only**, with separate measures for evidence strength, usage feedback, accessibility, pedagogy, privacy, cost and licensing.
- Register permitted review/academic/community sources; do not enable scraping without rights and source-specific approval.
- Only then derive a prioritized, measurable curriculum/product specification and build the learner-facing application.

## Direction

Atlas remains the **evidence and decision engine**, not the teaching product itself. Its purpose is to guide the eventual English learning platform from absolute beginner through advanced fluency using tested pedagogy, credible evidence and monitored outcomes; no claim of global leadership can be made before independent comparative evaluation.
