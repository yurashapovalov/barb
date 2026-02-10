-- Add events column to instruments
alter table public.instruments
  add column events text[] not null default '{}';
