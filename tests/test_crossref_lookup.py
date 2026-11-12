from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
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

    def test_audit_counts_entries_without_doi_not_title_fields(self) -> None:
        bib = (
            "@inproceedings{with_doi,\n  title = {A},\n  booktitle = {Proc B},\n"
            "  doi = {10.1000/abc}\n}\n\n"
            "@article{no_doi,\n  title = {C},\n  journaltitle = {J}\n}\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "refs.bib"
            path.write_text(bib, encoding="utf-8")
            valid = crossref_lookup.LookupResult("valid", "10.1000/abc", {})
            stdout = io.StringIO()
            with (
                mock.patch.object(
                    crossref_lookup.CrossrefClient, "fetch_doi", return_value=valid
                ),
                contextlib.redirect_stdout(stdout),
            ):
                code = crossref_lookup.main(
                    ["--audit-bibliography", str(path), "--strict"]
                )
        self.assertEqual(json.loads(stdout.getvalue())["potentially_missing_dois"], 1)
        self.assertEqual(code, 1)

    def test_an_empty_doi_field_counts_as_a_missing_doi(self) -> None:
        for bib in (
            "@article{k, title={Missing DOI}, doi={}}",
            '@article{k,\n  title = {Missing DOI},\n  doi = ""\n}',
            "@article{k, title={Missing DOI}, doi = { }}",
        ):
            with self.subTest(bib=bib):
                self.assertEqual(crossref_lookup.count_entries_without_doi(bib), 1)
        full = "@article{k, title={T}, doi={10.1000/abc}}"
        self.assertEqual(crossref_lookup.count_entries_without_doi(full), 0)

    def test_parenthesized_entries_are_audited(self) -> None:
        bib = (
            "@article(no_doi, title={C})\n"
            "@article(with_doi, title={D}, doi={10.1000/abc})\n"
        )
        self.assertEqual(crossref_lookup.count_entries_without_doi(bib), 1)

    def test_audit_of_a_complete_bibliography_passes_strict(self) -> None:
        bib = (
            "@inproceedings{k,\n  title = {A},\n  booktitle = {B},\n"
            "  doi = {10.1000/abc}\n}\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "refs.bib"
            path.write_text(bib, encoding="utf-8")
            valid = crossref_lookup.LookupResult("valid", "10.1000/abc", {})
            with (
                mock.patch.object(
                    crossref_lookup.CrossrefClient, "fetch_doi", return_value=valid
                ),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                code = crossref_lookup.main(
                    ["--audit-bibliography", str(path), "--strict"]
                )
        self.assertEqual(code, 0)

    def test_output_created_between_the_check_and_the_write_is_not_overwritten(
        self,
    ) -> None:
        valid = crossref_lookup.LookupResult("valid", "10.1000/abc", {})
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "report.json"
            target.write_text("new\n", encoding="utf-8")
            with (
                mock.patch.object(
                    crossref_lookup.CrossrefClient, "fetch_doi", return_value=valid
                ),
                # The existence check ran before the file appeared.
                mock.patch.object(Path, "exists", return_value=False),
                contextlib.redirect_stderr(io.StringIO()) as stderr,
            ):
                refused = crossref_lookup.main(
                    ["--doi", "10.1000/abc", "--output", str(target)]
                )
            self.assertEqual(refused, 1)
            self.assertIn("refusing to overwrite", stderr.getvalue())
            self.assertEqual(target.read_text(encoding="utf-8"), "new\n")

    def test_output_refuses_to_overwrite_unless_forced(self) -> None:
        valid = crossref_lookup.LookupResult("valid", "10.1000/abc", {})
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "report.json"
            target.write_text("old\n", encoding="utf-8")
            argv = ["--doi", "10.1000/abc", "--output", str(target)]
            with (
                mock.patch.object(
                    crossref_lookup.CrossrefClient, "fetch_doi", return_value=valid
                ),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                refused = crossref_lookup.main(argv)
                self.assertEqual(refused, 1)
                self.assertEqual(target.read_text(encoding="utf-8"), "old\n")
                forced = crossref_lookup.main([*argv, "--force"])
            self.assertEqual(forced, 0)
            self.assertEqual(
                json.loads(target.read_text(encoding="utf-8"))["status"], "valid"
            )

    def test_wrapper_runs_its_own_script_and_no_other_skill(self) -> None:
        wrapper = (MODULE_PATH.parent / "lookup").read_text(encoding="utf-8")
        self.assertNotIn("skills/", wrapper)
        self.assertIn("lookup.py", wrapper)


if __name__ == "__main__":
    unittest.main()
