-- Optional, NOT run yet. Today the worker writes to OpenMath's existing `papers`
-- table (title text, spec jsonb) and tells rows apart by spec->>'kind'.
-- To move to a dedicated table: run this once in the Supabase SQL editor and
-- change TABLE in agent/worker.py and web/index.html to 'start_rows'.
create table start_rows (
  id bigint primary key generated always as identity,
  created_at timestamptz default now(),
  title text,
  spec jsonb not null
);
alter table start_rows enable row level security;
grant select, insert on public.start_rows to anon;
create policy "anon read" on public.start_rows for select to anon using (true);
create policy "anon insert" on public.start_rows for insert to anon with check (true);
