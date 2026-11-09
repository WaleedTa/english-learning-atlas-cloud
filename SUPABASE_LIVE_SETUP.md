# Live Supabase setup

Project: `jpqhnefmbpvxanbzhjzg` (English Learning Atlas Cloud). Database schema was applied through Supabase migration `atlas_phase3_public_catalog_private_moderation`.

## Completed
- Public resource catalog with RLS: visitors read only `approved` resources.
- Private `atlas_review_details` table for notes and reviewer identities.
- Private `atlas_private.atlas_admins` allowlist.
- Authenticated RPC `atlas_review_resource` to record human decisions.
- Database currently has no users, admins or imported records.

## Required setup
1. Create an administrator in Supabase Dashboard → Authentication → Users (use your own email; do not share passwords).
2. Copy that Auth user's UUID, then add it with Supabase SQL Editor:
   `insert into atlas_private.atlas_admins(user_id) values ('YOUR_USER_UUID') on conflict do nothing;`
3. In Streamlit app settings → Secrets, set `SUPABASE_URL` to the project URL and `SUPABASE_ANON_KEY` to a **publishable** key. Never use service_role/secret key.
4. Change Streamlit main file to `cloud_app_phase3.py` after merging this fix PR.
5. Log in on the Admin tab, import `review_queue/openalex_candidates.csv` (pending only), then review each item.
6. Verify public/incognito visitors see no pending records and cannot read private notes.

The GitHub weekly workflow only updates a review CSV, not the database. Import is still manual. No administrator is automatically assigned. Do not run the older `supabase/schema.sql` against the live project; the live migration uses a safer separated private-notes design.
