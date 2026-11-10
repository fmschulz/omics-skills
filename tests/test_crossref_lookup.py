from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "skills" / "crossref-lookup" / "scripts" / "lookup.py"
SPEC = importlib.util.spec_from_file_location("crossref_lookup", MODULE_PATH)
crossref_lookup = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = crossref_lookup
SPEC.loader.exec_module(crossref_lookup)


class CrossrefLookupTests(unittest.TestCase):
    def test_normalize_doi_removes_bibtex_trailing_punctuation(self) -> None:
        self.assertEqual(
            crossref_lookup.normalize_doi("https://doi.org/10.1000/example.},"),
            "10.1000/example",
        )

    def test_fetch_distinguishes_not_found_from_transient_failure(self) -> None:
        client = crossref_lookup.CrossrefClient()
        not_found = Mock(status_code=404)
        transient = Mock(status_code=503)
        client.session.get = Mock(side_effect=[not_found, transient])
        self.assertEqual(client.fetch_doi("10.1000/missing").status, "not_found")
        self.assertEqual(client.fetch_doi("10.1000/retry").status, "transient_error")

    def test_strict_exit_codes_separate_content_and_service_failures(self) -> None:
        missing = crossref_lookup.LookupResult("not_found", "10.1000/missing")
        transient = crossref_lookup.LookupResult("transient_error", "10.1000/retry")
        self.assertEqual(crossref_lookup.exit_code([missing], strict=True), 1)
        self.assertEqual(crossref_lookup.exit_code([transient], strict=True), 2)

    def test_wrapper_runs_its_own_script_and_no_other_skill(self) -> None:
        wrapper = (MODULE_PATH.parent / "lookup").read_text(encoding="utf-8")
        self.assertNotIn("skills/", wrapper)
        self.assertIn("lookup.py", wrapper)


if __name__ == "__main__":
    unittest.main()
