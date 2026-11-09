-- Run in Supabase SQL Editor. Public reads only approved records.
create table if not exists public.atlas_resources (
  id text primary key,
  title text not null,
  year integer,
  doi text,
  source_query text,
  cited_by_count integer not null default 0,
  review_status text not null default 'pending'
    check (review_status in ('pending','needs_full_text','approved','rejected')),
  evidence_quality text not null default 'not_assessed'
    check (evidence_quality in ('not_assessed','low','moderate','high')),
  relevance text not null default 'not_assessed'
    check (relevance in ('not_assessed','low','medium','high')),
  review_notes text not null default '',
  reviewed_by uuid references auth.users(id),
  reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint approved_requires_review check (
    review_status <> 'approved' or
    (reviewed_by is not null and reviewed_at is not null and
     evidence_quality <> 'not_assessed' and relevance <> 'not_assessed' and length(trim(review_notes)) > 0)
  )
);
create table if not exists public.atlas_admins (
  user_id uuid primary key references auth.users(id) on delete cascade,
  created_at timestamptz not null default now()
);
alter table public.atlas_resources enable row level security;
alter table public.atlas_admins enable row level security;
revoke all on public.atlas_admins from anon, authenticated;
grant select, insert, update on public.atlas_resources to authenticated;
grant select on public.atlas_resources to anon;
-- Admin membership is checked through a SECURITY DEFINER function to avoid
-- recursive policies or exposing the admin membership table.
create or replace function public.atlas_is_admin()
returns boolean language sql stable security definer
set search_path = ''
as $$
  select exists (select 1 from public.atlas_admins where user_id = (select auth.uid()));
$$;
revoke all on function public.atlas_is_admin() from public;
grant execute on function public.atlas_is_admin() to authenticated;
drop policy if exists "public read approved" on public.atlas_resources;
create policy "public read approved" on public.atlas_resources for select
to anon, authenticated using (review_status = 'approved' or (select public.atlas_is_admin()));
drop policy if exists "admins insert" on public.atlas_resources;
create policy "admins insert" on public.atlas_resources for insert
to authenticated with check ((select public.atlas_is_admin()));
drop policy if exists "admins update" on public.atlas_resources;
create policy "admins update" on public.atlas_resources for update
to authenticated using ((select public.atlas_is_admin()))
with check ((select public.atlas_is_admin()));
-- Never add a public insert/update policy. Only admins can moderate.
create index if not exists atlas_resources_status_idx on public.atlas_resources(review_status);
create index if not exists atlas_resources_year_idx on public.atlas_resources(year);
-- After creating your Supabase Auth account, run manually in SQL Editor:
-- insert into public.atlas_admins(user_id) values ('YOUR_AUTH_USER_UUID');
