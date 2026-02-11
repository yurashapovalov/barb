-- Drop maintenance from exchanges.
-- Maintenance is redundant: the gap between ETH close and ETH open
-- already defines the non-trading window per instrument.

-- 1. Drop view (depends on maintenance column)
drop view public.instrument_full;

-- 2. Remove maintenance column
alter table public.exchanges drop column maintenance;

-- 3. Recreate view without maintenance
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
  e.timezone as exchange_timezone,
  e.name as exchange_name,
  e.image_url as exchange_image_url
from public.instruments i
join public.exchanges e on i.exchange = e.code;
