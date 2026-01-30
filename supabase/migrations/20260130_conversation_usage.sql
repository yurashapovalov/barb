alter table public.conversations
  add column usage jsonb not null default '{"input_tokens": 0, "output_tokens": 0, "thinking_tokens": 0, "cached_tokens": 0, "input_cost": 0, "output_cost": 0, "thinking_cost": 0, "total_cost": 0, "message_count": 0}'::jsonb;
