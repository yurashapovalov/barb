-- Remove unnecessary fields from instrument_full view
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
  i.config,
  e.timezone as exchange_timezone,
  e.name as exchange_name
from public.instruments i
join public.exchanges e on i.exchange = e.code;
