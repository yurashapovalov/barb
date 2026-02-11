-- Recreate instrument_full view with notes column
drop view public.instrument_full;

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
  i.notes,
  i.image_url,
  i.active,
  i.config,
  e.timezone as exchange_timezone,
  e.name as exchange_name,
  e.image_url as exchange_image_url
from public.instruments i
join public.exchanges e on i.exchange = e.code;
