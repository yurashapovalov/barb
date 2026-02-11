-- Add notes column to instruments (nullable text for AI context)
alter table public.instruments add column notes text;
