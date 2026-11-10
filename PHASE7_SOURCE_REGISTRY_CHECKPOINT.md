# Phase 7 checkpoint — Community and institutional source registry

Date: 2026-11-10

## Implemented
- Supabase table `public.atlas_source_registry` for proposed review sources.
- Categorization: academic, community, app reviews, institution, platform, project, user data, report, other.
- Fields: URL, source language, access-permission status, planned collection method, evidence class, notes, creation metadata, automation authorization flag.
- Check constraint prohibits `approved_for_automation=true` except for a permitted source.
- New sources created through UI always have `approved_for_automation=false`.
- Admin-only RLS and SELECT / INSERT / UPDATE policies. INSERT policy forbids automation permission; UPDATE policy currently also forbids enabling it (approval workflow remains future work).
- Bilingual private management section inside `cloud_app.py`; UI lists and manually registers candidate sources.
- `AtlasClient.list_source_registry` and `AtlasClient.create_registry_source` methods.

## Verified
- RLS enabled, 3 RLS policies.
- 0 registered sources at creation, 310 prior discoveries and 1 prior evidence review retained.
- Security advisors: existing informational private admin table warning; leaked-password protection disabled warning (Auth project setting, follow up via Supabase dashboard).
- Code committed to main; live Streamlit UI save flow **not yet tested**.

## Not implemented
- Automated scraping, crawling, ingestion, analysis of review texts, official platform connectors, automated approvals, scheduled monitoring, user-data collection or self-changing software.
- These future parts require provider-specific permissions, licensing checks, privacy/legal protections and explicit user approvals.
