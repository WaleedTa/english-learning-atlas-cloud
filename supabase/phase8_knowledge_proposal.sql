-- REVIEW-ONLY PROPOSAL. Do not run in production without approval and backup.
-- Candidate projects and individual claims are private until a human verifies them.
-- Existing atlas_is_admin() is already deployed and restricted to authenticated.

create table if not exists public.atlas_projects (
  slug text primary key check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  name text not null check (length(trim(name)) between 2 and 200),
  repository_url text not null unique check (repository_url ~ '^https://github[.]com/[^/]+/[^/]+$'),
  focus text[] not null default '{}',
  license_label text not null default 'unverified',
  license_checked_at timestamptz,
  review_status text not null default 'pending'
    check (review_status in ('pending','approved','rejected')),
  reviewer_id uuid references auth.users(id),
  reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint projects_approval_requires_reviewer check
    (review_status <> 'approved' or (reviewer_id is not null and reviewed_at is not null))
);

create table if not exists public.atlas_project_claims (
  id bigint generated always as identity primary key,
  project_slug text not null references public.atlas_projects(slug) on delete cascade,
  claim_type text not null check (claim_type in ('feature','method','license','outcome','limitation','community_feedback')),
  claim_text text not null check (length(trim(claim_text)) between 10 and 4000),
  evidence_url text not null check (evidence_url like 'https://%'),
  evidence_kind text not null check
    (evidence_kind in ('project_documentation','source_code','academic_study','community_review','other')),
  discovery_id text references public.atlas_discoveries(id),
  reviewed_status text not null default 'pending'
    check (reviewed_status in ('pending','verified','disputed','rejected')),
  reviewer_id uuid references auth.users(id),
  reviewed_at timestamptz,
  caveats text not null default '',
  created_at timestamptz not null default now(),
  constraint claim_verification_requires_review check
    (reviewed_status <> 'verified' or (reviewer_id is not null and reviewed_at is not null))
);

create index if not exists atlas_project_claims_project_idx on public.atlas_project_claims(project_slug);
create index if not exists atlas_project_claims_discovery_idx on public.atlas_project_claims(discovery_id);
alter table public.atlas_projects enable row level security;
alter table public.atlas_project_claims enable row level security;

-- Unlike user-facing learning content, the research catalog remains admin-only.
revoke all on public.atlas_projects, public.atlas_project_claims from anon;
grant select, insert, update on public.atlas_projects, public.atlas_project_claims to authenticated;
grant usage, select on sequence public.atlas_project_claims_id_seq to authenticated;

create policy "admin read projects" on public.atlas_projects for select
  to authenticated using ((select public.atlas_is_admin()));
create policy "admin insert projects" on public.atlas_projects for insert
  to authenticated with check ((select public.atlas_is_admin()));
create policy "admin update projects" on public.atlas_projects for update
  to authenticated using ((select public.atlas_is_admin()))
  with check ((select public.atlas_is_admin()));

create policy "admin read claims" on public.atlas_project_claims for select
  to authenticated using ((select public.atlas_is_admin()));
create policy "admin insert claims" on public.atlas_project_claims for insert
  to authenticated with check ((select public.atlas_is_admin()));
create policy "admin update claims" on public.atlas_project_claims for update
  to authenticated using ((select public.atlas_is_admin()))
  with check ((select public.atlas_is_admin()));

-- No automatic publication, deletion rights, or public read policies are granted.
