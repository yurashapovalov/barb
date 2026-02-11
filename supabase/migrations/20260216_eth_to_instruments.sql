-- Move ETH from exchanges to instruments.
-- ETH varies per instrument (e.g. ICEEUR: BRN trades ~24h, Cocoa only London hours).
-- Maintenance stays at exchange level (platform downtime, same for all products).

-- 1. Add ETH to each instrument's config.sessions
-- CME/CBOT/NYMEX/COMEX instruments: 18:00-17:00 ET
update public.instruments
set config = jsonb_set(config, '{sessions,ETH}', '["18:00", "17:00"]')
where exchange in ('CME', 'CBOT', 'NYMEX', 'COMEX');

-- ICEEUR: BRN has 20:00-18:00 ET
update public.instruments
set config = jsonb_set(config, '{sessions,ETH}', '["20:00", "18:00"]')
where symbol = 'BRN';

-- 2. Drop view (depends on eth column)
drop view public.instrument_full;

-- 3. Remove eth from exchanges
alter table public.exchanges drop column eth;

-- 4. Recreate view without eth (ETH now lives in config.sessions)
create view public.instrument_full as
select
  i.symbol,
  i.name,
  i.exchange,
  i.type,
  i.category,
  i.currency,
  i.default_session,
  i.data_start,
  i.data_end,
  i.events,
  i.image_url,
  i.active,
  i.config,
  e.maintenance,
  e.timezone as exchange_timezone,
  e.name as exchange_name,
  e.image_url as exchange_image_url
from public.instruments i
join public.exchanges e on i.exchange = e.code;
