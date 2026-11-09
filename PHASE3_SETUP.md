# Phase 3: Supabase-backed public atlas, private moderation

## Setup
1. Create a Supabase project at https://supabase.com/dashboard. Do not paste passwords, access tokens, or service-role keys into GitHub.
2. Open Supabase **SQL Editor** and execute `supabase/schema.sql`.
3. Under **Authentication → Users**, create your administrator account with a strong password. Copy the account's UUID.
4. In SQL Editor run `insert into public.atlas_admins(user_id) values ('YOUR_AUTH_USER_UUID');` replacing the placeholder with your UUID.
5. In your deployed Streamlit app settings, add secrets:
   ```toml
   SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
   SUPABASE_ANON_KEY = "YOUR_PUBLISHABLE_OR_ANON_KEY"
   ```
   Use the project publishable/anon key, **never** the service_role/secret key. Supabase RLS is the authorization boundary.
6. Restart the app. The public page lists only **approved** database records. Log in via the Admin tab to import candidate CSV, assess and approve items.
7. Upload `review_queue/openalex_candidates.csv` in the admin tab to import candidates into the database; the upload alone does not publish them.
8. Check access in a private/incognito window: no pending or rejected rows must be visible. Verify admin sign-in and review flow.

## Security and limitations
- Public visitors cannot change records; only allowlisted Supabase Auth user UUIDs can insert/update.
- Supabase service_role credentials must never be stored in Streamlit or GitHub. Do not turn off RLS.
- Decisions are durable in Supabase, not browser session storage.
- Importing candidates and reviewing are manual; the weekly GitHub Action still creates a PR with CSV and does **not** directly write to Supabase.
- No scientific claims are automatically verified; approved means a human review was recorded.
- Auth is a basic password sign-in, not yet MFA, team roles, or audit log. Configure Supabase Auth rate limits, email verification and MFA as needed.
- Streamlit Community Cloud deployments from a public repo expose source code; secrets belong only in Streamlit Secrets.
