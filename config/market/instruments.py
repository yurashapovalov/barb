"""
Instrument registry.

Instruments are loaded from Supabase at API startup via register_instrument().
The registry provides a normalized dict for each instrument, with holidays
merged from EXCHANGE_HOLIDAYS by exchange code.

All session times in ET.
"""

import json

from config.market.holidays import get_holidays_for_exchange

# Cache: symbol -> normalized dict
_CACHE: dict[str, dict] = {}


def register_instrument(row: dict) -> None:
    """Normalize a Supabase instrument_full row and store in cache.

    Expected row keys (from instrument_full view):
        symbol, name, exchange, type, category, currency,
        default_session, data_start, data_end, events, notes,
        config (JSON string or dict), exchange_timezone, exchange_name
    """
    config = row.get("config", {})
    if isinstance(config, str):
        config = json.loads(config)

    sessions = {name: tuple(times) for name, times in config.get("sessions", {}).items()}

    holidays = get_holidays_for_exchange(row.get("exchange", ""))

    normalized = {
        "symbol": row["symbol"],
        "name": row["name"],
        "exchange": row.get("exchange", ""),
        "type": row.get("type", "futures"),
        "category": row.get("category", ""),
        "currency": row.get("currency", "USD"),
        "default_session": row.get("default_session", "RTH"),
        "data_start": row.get("data_start", ""),
        "data_end": row.get("data_end", ""),
        "events": row.get("events") or ["macro"],
        "notes": row.get("notes"),
        "exchange_timezone": row.get("exchange_timezone", ""),
        "exchange_name": row.get("exchange_name", ""),
        "tick_size": config.get("tick_size"),
        "tick_value": config.get("tick_value"),
        "point_value": config.get("point_value"),
        "sessions": sessions,
        "holidays": holidays,
    }

    _CACHE[row["symbol"].upper()] = normalized


def get_instrument(symbol: str) -> dict | None:
    """Get instrument configuration from cache."""
    return _CACHE.get(symbol.upper())


def get_session_times(symbol: str, session: str) -> tuple[str, str] | None:
    """Get session (start, end) times in ET."""
    instrument = get_instrument(symbol)
    if not instrument:
        return None
    return instrument.get("sessions", {}).get(session.upper())


def get_trading_day_boundaries(symbol: str) -> tuple[str, str] | None:
    """Get trading day (start, end) times. Trading day = ETH session."""
    return get_session_times(symbol, "ETH")


def get_default_session(symbol: str) -> str:
    """Get default session for instrument."""
    instrument = get_instrument(symbol)
    if not instrument:
        return "RTH"
    return instrument.get("default_session", "RTH")


def list_sessions(symbol: str) -> list[str]:
    """List available sessions for instrument."""
    instrument = get_instrument(symbol)
    if not instrument:
        return []
    return list(instrument.get("sessions", {}).keys())


def clear_cache() -> None:
    """Clear the instrument cache. For testing."""
    _CACHE.clear()
