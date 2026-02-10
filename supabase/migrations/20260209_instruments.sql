-- instruments — trading instrument metadata
-- Columns: universal queryable fields. JSONB config: structured data that varies by type.
create table public.instruments (
  symbol          text primary key,
  name            text not null,
  exchange        text not null,
  category        text not null,
  currency        text not null default 'USD',
  data_timezone   text not null default 'ET',
  default_session text not null default 'RTH',
  data_start      date,
  data_end        date,
  image_url       text,
  active          boolean not null default true,
  config          jsonb not null default '{}',
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index idx_instruments_exchange on public.instruments (exchange);
create index idx_instruments_category on public.instruments (category);
create index idx_instruments_active on public.instruments (active) where active = true;

-- public read, service-role write
alter table public.instruments enable row level security;

create policy "Anyone can read instruments"
  on public.instruments for select using (true);

create trigger instruments_updated_at
  before update on public.instruments
  for each row execute function public.update_updated_at();
