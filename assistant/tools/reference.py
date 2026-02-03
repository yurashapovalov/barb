"""get_query_reference tool — Barb Script format reference."""

from pathlib import Path

_REF_DIR = Path(__file__).parent / "reference"

DECLARATION = {
    "name": "get_query_reference",
    "description": (
        "Get Barb Script query format and examples. "
        "Use pattern to get examples for a specific query type."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "enum": [
                    "simple_stat",
                    "filter_count",
                    "group_analysis",
                    "pattern_detect",
                    "ranking",
                ],
                "description": (
                    "Query pattern for the user's question. "
                    "simple_stat: scalar statistics (average, count). "
                    "filter_count: filter rows + count/stat. "
                    "group_analysis: group by column + aggregate. "
                    "pattern_detect: prev(), rolling patterns. "
                    "ranking: top/bottom N. "
                    "Omit to get all examples."
                ),
            },
        },
    },
}


def run(args: dict) -> str:
    """Return format reference + relevant pattern examples."""
    pattern = args.get("pattern")
    return _build_reference(pattern)


def _build_reference(pattern: str | None) -> str:
    parts = [(_REF_DIR / "format.md").read_text()]

    if pattern:
        path = _REF_DIR / "patterns" / f"{pattern}.md"
        if path.exists():
            parts.append(path.read_text())
    else:
        for path in sorted((_REF_DIR / "patterns").glob("*.md")):
            parts.append(path.read_text())

    return "\n\n".join(parts)
