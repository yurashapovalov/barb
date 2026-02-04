-- Add status column for soft delete
alter table public.conversations
  add column status text not null default 'active'
  check (status in ('active', 'removed'));
