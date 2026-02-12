"""Tests for auto-generated function reference."""

from assistant.tools.reference import DISPLAY_GROUPS, build_function_reference
from barb.functions import FUNCTIONS, SIGNATURES


class TestDisplayGroups:
    def test_all_functions_in_groups(self):
        """Every registered function must appear in exactly one display group."""
        grouped = set()
        for _, names, _ in DISPLAY_GROUPS:
            for name in names:
                assert name not in grouped, f"Duplicate in display groups: {name}"
                grouped.add(name)
        missing = set(FUNCTIONS) - grouped
        assert not missing, f"Functions not in any display group: {missing}"

    def test_no_unknown_functions_in_groups(self):
        grouped = set()
        for _, names, _ in DISPLAY_GROUPS:
            grouped.update(names)
        unknown = grouped - set(FUNCTIONS)
        assert not unknown, f"Unknown functions in display groups: {unknown}"


class TestBuildFunctionReference:
    def setup_method(self):
        self.ref = build_function_reference()

    def test_returns_string(self):
        assert isinstance(self.ref, str)
        assert len(self.ref) > 500

    def test_has_base_columns(self):
        assert "## Base columns" in self.ref
        assert "open, high, low, close, volume" in self.ref

    def test_has_operators(self):
        assert "## Operators" in self.ref
        assert "Arithmetic" in self.ref
        assert "Comparison" in self.ref
        assert "Boolean" in self.ref

    def test_has_functions_section(self):
        assert "## Functions" in self.ref

    def test_has_notes(self):
        assert "## Notes" in self.ref
        assert "NaN" in self.ref

    def test_all_signatures_present(self):
        """Every function signature should appear in the reference."""
        for name, sig in SIGNATURES.items():
            assert sig in self.ref, f"Missing signature: {sig}"

    def test_all_group_labels_present(self):
        for label, _, _ in DISPLAY_GROUPS:
            assert label in self.ref, f"Missing group label: {label}"

    def test_expanded_groups_have_descriptions(self):
        """Expanded groups should have ' — ' separator (sig — desc)."""
        for label, names, expanded in DISPLAY_GROUPS:
            if expanded:
                for name in names:
                    sig = SIGNATURES[name]
                    assert f"{sig} —" in self.ref, (
                        f"Expanded function {name} should have description"
                    )

    def test_compact_groups_are_one_line(self):
        """Compact groups should have all sigs on one line after label."""
        for label, names, expanded in DISPLAY_GROUPS:
            if not expanded:
                sigs = ", ".join(SIGNATURES[n] for n in names)
                assert f"{label}: {sigs}" in self.ref
