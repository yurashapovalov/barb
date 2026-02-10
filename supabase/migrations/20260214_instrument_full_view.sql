-- View: instrument with exchange data merged
create view public.instrument_full as
select
  i.symbol,
  i.name,
  i.exchange,
  i.type,
  i.category,
  i.currency,
  i.data_timezone,
  i.default_session,
  i.data_start,
  i.data_end,
  i.events,
  i.image_url,
  i.active,
  i.config,
  e.eth,
  e.maintenance,
  e.name as exchange_name,
  e.image_url as exchange_image_url
from public.instruments i
join public.exchanges e on i.exchange = e.code;

-- Remove ETH and maintenance from instrument configs (now comes from exchange)
update public.instruments
set config = config - 'maintenance' #- '{sessions,ETH}'
where config ? 'maintenance';
