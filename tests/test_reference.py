"""Tests for query reference — file loading and pattern selection."""

import json

from assistant.tools.reference import _REF_DIR, run

PATTERNS = ["simple_stat", "filter_count", "group_analysis", "pattern_detect", "ranking"]


class TestPatternFiles:
    def test_format_file_exists(self):
        assert (_REF_DIR / "format.md").exists()
        assert (_REF_DIR / "format.md").read_text().strip()

    def test_all_pattern_files_exist(self):
        for name in PATTERNS:
            path = _REF_DIR / "patterns" / f"{name}.md"
            assert path.exists(), f"Missing pattern file: {name}.md"
            assert path.read_text().strip(), f"Empty pattern file: {name}.md"

    def test_examples_are_valid_json(self):
        """Every JSON example in pattern files must parse."""
        for path in (_REF_DIR / "patterns").glob("*.md"):
            text = path.read_text()
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("{") and stripped.endswith("}"):
                    try:
                        json.loads(stripped)
                    except json.JSONDecodeError:
                        raise AssertionError(
                            f"Invalid JSON in {path.name}: {stripped}"
                        )


class TestRun:
    def test_no_pattern_returns_all(self):
        result = run({})
        assert "Barb Script Query Reference" in result
        for name in PATTERNS:
            title = (_REF_DIR / "patterns" / f"{name}.md").read_text().splitlines()[0]
            assert title.lstrip("# ") in result

    def test_specific_pattern(self):
        result = run({"pattern": "group_analysis"})
        assert "Barb Script Query Reference" in result
        assert "Group Analysis" in result
        assert "Simple Statistics" not in result
        assert "Ranking" not in result

    def test_each_pattern_loads(self):
        for name in PATTERNS:
            result = run({"pattern": name})
            assert "Barb Script Query Reference" in result
            content = (_REF_DIR / "patterns" / f"{name}.md").read_text()
            assert content.splitlines()[0].lstrip("# ") in result

    def test_unknown_pattern_returns_format_only(self):
        result = run({"pattern": "nonexistent"})
        assert "Barb Script Query Reference" in result
        for name in PATTERNS:
            title = (_REF_DIR / "patterns" / f"{name}.md").read_text().splitlines()[0]
            assert title.lstrip("# ") not in result

    def test_format_always_included(self):
        result = run({"pattern": "simple_stat"})
        assert "Execution Order" in result
        assert "## Functions" in result

    def test_pattern_result_shorter_than_all(self):
        all_result = run({})
        one_result = run({"pattern": "simple_stat"})
        assert len(one_result) < len(all_result)
