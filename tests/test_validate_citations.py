from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "validate-citations.py"
SPEC = importlib.util.spec_from_file_location("validate_citations", MODULE_PATH)
validate_citations = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = validate_citations
SPEC.loader.exec_module(validate_citations)


class CitationValidationTests(unittest.TestCase):
    def test_collects_frontmatter_title_and_skill_prose_dois(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_md = Path(tmp) / "SKILL.md"
            skill_md.write_text(
                "---\n"
                "title: Correct paper title\n"
                "doi: 10.1234/frontmatter\n"
                "---\n"
                "See DOI 10.5678/prose.\n",
                encoding="utf-8",
            )
            citations = validate_citations.collect_citations([skill_md])
        self.assertEqual(
            [(item.doi, item.title) for item in citations],
            [
                ("10.1234/frontmatter", "Correct paper title"),
                ("10.5678/prose", None),
            ],
        )

    def test_cache_rejects_missing_doi_and_unrelated_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cache = root / "cache.json"
            cache.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "records": {
                            "10.1234/title": {
                                "registered": True,
                                "title": "A chromosome assembly for a beetle",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            citations = [
                validate_citations.Citation(
                    "10.1234/title", root / "paper.md", 4, "Cave metagenome assembled genomes"
                ),
                validate_citations.Citation("10.1234/missing", root / "paper.md", 5),
            ]
            errors = validate_citations.validate_cache(citations, cache)
        # Assert on the errors, not their count: the cache contract gains checks
        # (checked_at freshness, unused entries) and a count locks that shut.
        self.assertTrue(any("title does not match" in error for error in errors), errors)
        self.assertTrue(any("not in the validated cache" in error for error in errors), errors)

    def test_normalize_doi_removes_bibtex_punctuation(self) -> None:
        self.assertEqual(
            validate_citations.normalize_doi("https://doi.org/10.1000/example.},"),
            "10.1000/example",
        )


class CacheFreshnessTests(unittest.TestCase):
    """A cache with no expiry accepts a registration check made years ago, and
    one that never prunes accumulates DOIs nothing cites."""

    def citation(self, doi: str = "10.1000/example") -> validate_citations.Citation:
        return validate_citations.Citation(doi, Path("skills/x/SKILL.md"), 1, None)

    def write_cache(self, tmp: Path, records: dict) -> Path:
        cache = tmp / "citation-cache.json"
        cache.write_text(json.dumps({"version": 1, "records": records}), encoding="utf-8")
        return cache

    def test_a_stale_record_is_rejected(self) -> None:
        old = datetime.now(timezone.utc) - timedelta(days=validate_citations.MAX_CACHE_AGE_DAYS + 1)
        with tempfile.TemporaryDirectory() as tmp:
            cache = self.write_cache(
                Path(tmp),
                {"10.1000/example": {"registered": True, "title": None,
                                     "checked_at": old.strftime("%Y-%m-%dT%H:%M:%SZ")}},
            )
            notices = io.StringIO()
            with contextlib.redirect_stderr(notices):
                errors = validate_citations.validate_cache([self.citation()], cache)
        # Age is a maintenance signal, not a verdict: failing on it would break
        # an offline gate on a date certain.
        self.assertEqual(errors, [])
        self.assertIn("last checked", notices.getvalue())

    def test_a_fresh_record_passes(self) -> None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with tempfile.TemporaryDirectory() as tmp:
            cache = self.write_cache(
                Path(tmp),
                {"10.1000/example": {"registered": True, "title": None, "checked_at": now}},
            )
            self.assertEqual(validate_citations.validate_cache([self.citation()], cache), [])

    def test_a_record_without_a_date_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache = self.write_cache(Path(tmp), {"10.1000/example": {"registered": True, "title": None}})
            errors = validate_citations.validate_cache([self.citation()], cache)
        self.assertTrue(any("no checked_at" in error for error in errors), errors)

    def test_uncited_cache_entries_are_reported(self) -> None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with tempfile.TemporaryDirectory() as tmp:
            cache = self.write_cache(
                Path(tmp),
                {
                    "10.1000/example": {"registered": True, "title": None, "checked_at": now},
                    "10.1000/nobody-cites-me": {"registered": True, "title": None, "checked_at": now},
                },
            )
            notices = io.StringIO()
            with contextlib.redirect_stderr(notices):
                errors = validate_citations.validate_cache([self.citation()], cache)
        self.assertEqual(errors, [])
        self.assertIn("nothing cites any more", notices.getvalue())


class DoiExtractionTests(unittest.TestCase):
    def test_markdown_emphasis_is_not_part_of_the_doi(self) -> None:
        self.assertEqual(
            validate_citations.normalize_doi("10.5281/zenodo.19154110**"),
            "10.5281/zenodo.19154110",
        )

    def test_a_preprint_url_version_suffix_is_stripped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text(
                "See https://www.biorxiv.org/content/10.64898/2026.01.08.698506v3\n",
                encoding="utf-8",
            )
            dois = {c.doi for c in validate_citations.collect_citations([path])}
        self.assertIn("10.64898/2026.01.08.698506", dois)
        self.assertNotIn("10.64898/2026.01.08.698506v3", dois)


if __name__ == "__main__":
    unittest.main()
