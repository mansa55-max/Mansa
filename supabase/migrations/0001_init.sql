-- Ad projects: one row per UGC ad the user is creating.
create table if not exists public.ad_projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  product_name text not null,
  product_description text not null default '',
  product_url text,
  tone text not null default 'excited',
  script text not null default '',
  avatar_id text not null,
  voice_id text not null,
  status text not null default 'draft'
    check (status in ('draft', 'generating', 'ready', 'failed')),
  video_url text,
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists ad_projects_user_id_idx on public.ad_projects (user_id, created_at desc);

alter table public.ad_projects enable row level security;

create policy "Users can view their own ad projects"
  on public.ad_projects for select
  using (auth.uid() = user_id);

create policy "Users can create their own ad projects"
  on public.ad_projects for insert
  with check (auth.uid() = user_id);

create policy "Users can update their own ad projects"
  on public.ad_projects for update
  using (auth.uid() = user_id);

create policy "Users can delete their own ad projects"
  on public.ad_projects for delete
  using (auth.uid() = user_id);

create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger ad_projects_set_updated_at
  before update on public.ad_projects
  for each row execute function public.set_updated_at();
