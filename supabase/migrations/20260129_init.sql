-- conversations
create table public.conversations (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users(id) on delete cascade,
  title       text not null default 'New conversation',
  instrument  text not null default 'NQ',
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create index idx_conversations_user_updated
  on public.conversations (user_id, updated_at desc);

-- messages
create table public.messages (
  id               uuid primary key default gen_random_uuid(),
  conversation_id  uuid not null references public.conversations(id) on delete cascade,
  role             text not null check (role in ('user', 'model')),
  content          text not null default '',
  data             jsonb,
  usage            jsonb,
  created_at       timestamptz not null default now()
);

create index idx_messages_conversation_created
  on public.messages (conversation_id, created_at asc);

-- tool_calls
create table public.tool_calls (
  id           uuid primary key default gen_random_uuid(),
  message_id   uuid not null references public.messages(id) on delete cascade,
  tool_name    text not null,
  input        jsonb,
  output       jsonb,
  error        text,
  duration_ms  int,
  created_at   timestamptz not null default now()
);

create index idx_tool_calls_message_created
  on public.tool_calls (message_id, created_at asc);

-- RLS
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.tool_calls enable row level security;

create policy "Users select own conversations"
  on public.conversations for select using (auth.uid() = user_id);
create policy "Users insert own conversations"
  on public.conversations for insert with check (auth.uid() = user_id);
create policy "Users update own conversations"
  on public.conversations for update using (auth.uid() = user_id);
create policy "Users delete own conversations"
  on public.conversations for delete using (auth.uid() = user_id);

create policy "Users select own messages"
  on public.messages for select
  using (conversation_id in (select id from public.conversations where user_id = auth.uid()));
create policy "Users insert own messages"
  on public.messages for insert
  with check (conversation_id in (select id from public.conversations where user_id = auth.uid()));
create policy "Users delete own messages"
  on public.messages for delete
  using (conversation_id in (select id from public.conversations where user_id = auth.uid()));

create policy "Users select own tool_calls"
  on public.tool_calls for select
  using (message_id in (
    select m.id from public.messages m
    join public.conversations c on c.id = m.conversation_id
    where c.user_id = auth.uid()
  ));
create policy "Users insert own tool_calls"
  on public.tool_calls for insert
  with check (message_id in (
    select m.id from public.messages m
    join public.conversations c on c.id = m.conversation_id
    where c.user_id = auth.uid()
  ));

-- auto-update trigger
create or replace function public.update_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger conversations_updated_at
  before update on public.conversations
  for each row execute function public.update_updated_at();
