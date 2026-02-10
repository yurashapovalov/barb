-- Add native timezone to exchanges
alter table public.exchanges
  add column timezone text not null default 'CT';

update public.exchanges set timezone = 'CT' where code in ('CME', 'CBOT');
update public.exchanges set timezone = 'ET' where code in ('NYMEX', 'COMEX');
update public.exchanges set timezone = 'GMT' where code = 'ICEEUR';

-- Drop view first (depends on data_timezone)
drop view public.instrument_full;

-- Remove data_timezone from instruments (always ET, system constant)
alter table public.instruments drop column data_timezone;

-- Recreate view with exchange timezone
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
  e.eth,
  e.maintenance,
  e.timezone as exchange_timezone,
  e.name as exchange_name,
  e.image_url as exchange_image_url
from public.instruments i
join public.exchanges e on i.exchange = e.code;
