"""Registry consistency: every function has a signature and description."""

from barb.functions import DESCRIPTIONS, FUNCTIONS, SIGNATURES


class TestRegistryConsistency:
    def test_all_functions_have_signatures(self):
        missing = set(FUNCTIONS) - set(SIGNATURES)
        assert not missing, f"Functions without signatures: {missing}"

    def test_all_functions_have_descriptions(self):
        missing = set(FUNCTIONS) - set(DESCRIPTIONS)
        assert not missing, f"Functions without descriptions: {missing}"

    def test_no_orphan_signatures(self):
        orphans = set(SIGNATURES) - set(FUNCTIONS)
        assert not orphans, f"Signatures without functions: {orphans}"

    def test_no_orphan_descriptions(self):
        orphans = set(DESCRIPTIONS) - set(FUNCTIONS)
        assert not orphans, f"Descriptions without functions: {orphans}"

    def test_no_empty_signatures(self):
        empty = [k for k, v in SIGNATURES.items() if not v.strip()]
        assert not empty, f"Empty signatures: {empty}"

    def test_no_empty_descriptions(self):
        empty = [k for k, v in DESCRIPTIONS.items() if not v.strip()]
        assert not empty, f"Empty descriptions: {empty}"

    def test_signatures_contain_function_name(self):
        """Each signature should start with the function name."""
        for name, sig in SIGNATURES.items():
            assert sig.startswith(name + "("), (
                f"Signature for '{name}' should start with '{name}(', got: {sig}"
            )

    def test_counts_match(self):
        assert len(FUNCTIONS) == len(SIGNATURES)
        assert len(FUNCTIONS) == len(DESCRIPTIONS)
