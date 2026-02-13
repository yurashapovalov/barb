-- user_instruments — which instruments each user has added to their workspace
create table public.user_instruments (
  id         uuid primary key default gen_random_uuid(),
  user_id    uuid not null references auth.users(id) on delete cascade,
  instrument text not null references public.instruments(symbol),
  added_at   timestamptz not null default now(),

  unique (user_id, instrument)
);

create index idx_user_instruments_user
  on public.user_instruments (user_id, added_at asc);

-- RLS: users manage their own instruments
alter table public.user_instruments enable row level security;

create policy "Users select own instruments"
  on public.user_instruments for select using (auth.uid() = user_id);
create policy "Users insert own instruments"
  on public.user_instruments for insert with check (auth.uid() = user_id);
create policy "Users delete own instruments"
  on public.user_instruments for delete using (auth.uid() = user_id);
