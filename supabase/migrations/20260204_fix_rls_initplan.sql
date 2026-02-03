-- Wrap auth.uid() in (select ...) so it evaluates once per query, not per row.

-- conversations
drop policy "Users select own conversations" on public.conversations;
create policy "Users select own conversations"
  on public.conversations for select using ((select auth.uid()) = user_id);

drop policy "Users insert own conversations" on public.conversations;
create policy "Users insert own conversations"
  on public.conversations for insert with check ((select auth.uid()) = user_id);

drop policy "Users update own conversations" on public.conversations;
create policy "Users update own conversations"
  on public.conversations for update using ((select auth.uid()) = user_id);

drop policy "Users delete own conversations" on public.conversations;
create policy "Users delete own conversations"
  on public.conversations for delete using ((select auth.uid()) = user_id);

-- messages
drop policy "Users select own messages" on public.messages;
create policy "Users select own messages"
  on public.messages for select
  using (conversation_id in (select id from public.conversations where user_id = (select auth.uid())));

drop policy "Users insert own messages" on public.messages;
create policy "Users insert own messages"
  on public.messages for insert
  with check (conversation_id in (select id from public.conversations where user_id = (select auth.uid())));

drop policy "Users delete own messages" on public.messages;
create policy "Users delete own messages"
  on public.messages for delete
  using (conversation_id in (select id from public.conversations where user_id = (select auth.uid())));

-- tool_calls
drop policy "Users select own tool_calls" on public.tool_calls;
create policy "Users select own tool_calls"
  on public.tool_calls for select
  using (message_id in (
    select m.id from public.messages m
    join public.conversations c on c.id = m.conversation_id
    where c.user_id = (select auth.uid())
  ));

drop policy "Users insert own tool_calls" on public.tool_calls;
create policy "Users insert own tool_calls"
  on public.tool_calls for insert
  with check (message_id in (
    select m.id from public.messages m
    join public.conversations c on c.id = m.conversation_id
    where c.user_id = (select auth.uid())
  ));
