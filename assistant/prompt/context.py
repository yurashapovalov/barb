"""Market context builders for system prompt.

Each function takes an instrument config dict and returns a text block
for the system prompt. Config comes from get_instrument() — either
local INSTRUMENTS dict or Supabase.
"""

from config.market.events import EventImpact, get_event_types_for_instrument
from config.market.holidays import HOLIDAY_NAMES


def build_instrument_context(config: dict) -> str:
    """Instrument info: sessions, tick size, data range."""
    sessions = config.get("sessions", {})
    session_lines = "\n".join(
        f"  {name:12s} {start}-{end}" for name, (start, end) in sessions.items()
    )

    tick_size = config.get("tick_size", "?")
    tick_value = config.get("tick_value", "?")
    point_value = config.get("point_value")
    tick_line = f"Tick: {tick_size}"
    if tick_value != "?":
        tick_line += f" (${tick_value} per tick"
        if point_value:
            tick_line += f", ${point_value} per point"
        tick_line += ")"

    maintenance = config.get("maintenance")
    maint_line = (
        f"\nMaintenance: {maintenance[0]}-{maintenance[1]} (no data)" if maintenance else ""
    )

    notes = config.get("notes")
    notes_line = f"\nNote: {notes}" if notes else ""

    return f"""\
<instrument>
Symbol: {config.get("symbol", "?")} ({config.get("name", "?")})
Exchange: {config.get("exchange", "?")}
Data: {config.get("data_start", "?")} to {config.get("data_end", "?")}
{tick_line}
Default session: {config.get("default_session", "RTH")}
All times in ET

Sessions:
{session_lines}{maint_line}{notes_line}
</instrument>"""


def build_holiday_context(config: dict) -> str:
    """Holiday rules: full close and early close days."""
    holidays = config.get("holidays", {})
    if not holidays:
        return ""

    full_close = holidays.get("full_close", [])
    early_close = holidays.get("early_close", {})

    if not full_close and not early_close:
        return ""

    closed_names = [HOLIDAY_NAMES.get(r, r) for r in full_close]
    early_items = [f"{HOLIDAY_NAMES.get(r, r)} ({t})" for r, t in early_close.items()]

    parts = ["<holidays>"]
    if closed_names:
        parts.append(f"Market closed: {', '.join(closed_names)}")
    if early_items:
        parts.append(f"Early close: {', '.join(early_items)}")
    parts.append("Saturday holidays → observed Friday. Sunday → observed Monday.")
    parts.append("If user asks about a closed date → tell them why market was closed.")
    parts.append("If user asks about early close day → note shortened session.")
    parts.append("</holidays>")

    return "\n".join(parts)


def build_event_context(config: dict) -> str:
    """Market events affecting this instrument."""
    symbol = config.get("symbol")
    if not symbol:
        return ""

    events = get_event_types_for_instrument(symbol)
    if not events:
        return ""

    high = [e for e in events if e.impact == EventImpact.HIGH]
    medium = [e for e in events if e.impact == EventImpact.MEDIUM]

    parts = ["<events>"]

    if high:
        high_lines = []
        for e in high:
            line = f"  {e.name} — {e.schedule}"
            if e.typical_time:
                line += f", {e.typical_time} ET"
            high_lines.append(line)
        parts.append("High impact:")
        parts.extend(high_lines)

    if medium:
        medium_names = ", ".join(e.name for e in medium)
        parts.append(f"\nMedium impact: {medium_names}")

    # Calculable date hints
    parts.append("")
    parts.append(
        "NFP = 1st Friday of month. OPEX = 3rd Friday. Quad Witching = 3rd Fri Mar/Jun/Sep/Dec."
    )
    parts.append("When user asks about event days → calculate dates and query those dates.")
    parts.append("</events>")

    return "\n".join(parts)
