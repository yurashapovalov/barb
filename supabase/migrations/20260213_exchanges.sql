-- Exchanges table: ETH and maintenance per exchange
create table public.exchanges (
  code        text primary key,
  name        text not null,
  eth         jsonb not null,
  maintenance jsonb not null,
  image_url   text
);

-- Public read, service-role write
alter table public.exchanges enable row level security;

create policy "Public read exchanges"
  on public.exchanges for select using (true);

create policy "Service role manages exchanges"
  on public.exchanges for all using ((select auth.role()) = 'service_role');

-- Seed exchanges first (before FK)
insert into public.exchanges (code, name, eth, maintenance) values
  ('CME',    'Chicago Mercantile Exchange', '["18:00", "17:00"]', '["17:00", "18:00"]'),
  ('CBOT',   'Chicago Board of Trade',     '["18:00", "17:00"]', '["17:00", "18:00"]'),
  ('NYMEX',  'New York Mercantile Exchange','["18:00", "17:00"]', '["17:00", "18:00"]'),
  ('COMEX',  'Commodity Exchange',          '["18:00", "17:00"]', '["17:00", "18:00"]'),
  ('ICEEUR', 'ICE Futures Europe',          '["20:00", "18:00"]', '["18:00", "20:00"]');

-- FK from instruments (after seed so existing rows pass validation)
alter table public.instruments
  add constraint fk_instruments_exchange
  foreign key (exchange) references public.exchanges (code);
