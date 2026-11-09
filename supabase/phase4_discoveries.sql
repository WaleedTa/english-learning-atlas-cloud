-- Phase 4 evidence registry; metadata never auto-publishes.
create table if not exists public.atlas_discoveries (
  id text primary key,
  source text not null,
  title text not null,
  url text not null,
  doi text,
  year integer,
  kind text not null default 'research',
  authors text,
  abstract text,
  citation_count integer,
  search_query text,
  skills text[] not null default '{}',
  methods text[] not null default '{}',
  frameworks text[] not null default '{}',
  evidence_status text not null default 'unassessed',
  review_status text not null default 'pending'
    check (review_status in ('pending','needs_full_text','approved','rejected')),
  limitations text,
  retrieved_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);
create index if not exists atlas_discoveries_status_idx on public.atlas_discoveries(review_status);
create index if not exists atlas_discoveries_skills_idx on public.atlas_discoveries using gin(skills);
create index if not exists atlas_discoveries_frameworks_idx on public.atlas_discoveries using gin(frameworks);
alter table public.atlas_discoveries enable row level security;
revoke all on public.atlas_discoveries from anon, authenticated;
grant select on public.atlas_discoveries to anon, authenticated;
grant insert, update on public.atlas_discoveries to authenticated;
create policy "public reads reviewed discoveries" on public.atlas_discoveries
 for select to anon, authenticated using (review_status = 'approved');
create policy "admins read all discoveries" on public.atlas_discoveries
 for select to authenticated using ((select atlas_private.is_atlas_admin()));
create policy "admins import pending discoveries" on public.atlas_discoveries
 for insert to authenticated with check ((select atlas_private.is_atlas_admin()) and review_status = 'pending');
create policy "admins moderate discoveries" on public.atlas_discoveries
 for update to authenticated using ((select atlas_private.is_atlas_admin()))
 with check ((select atlas_private.is_atlas_admin()));
