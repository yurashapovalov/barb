-- Add type column to instruments (futures, stock, etf, option, etc.)
alter table public.instruments
  add column type text not null default 'futures';

create index idx_instruments_type on public.instruments (type);
