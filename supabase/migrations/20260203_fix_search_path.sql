-- Fix mutable search_path on update_updated_at
alter function public.update_updated_at() set search_path = public;
