"""Supabase client — service role, bypasses RLS."""

from functools import lru_cache

from api.config import get_settings
from supabase import Client, create_client


@lru_cache
def get_db() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_key)
