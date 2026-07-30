from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
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
        self.assertEqual(len(errors), 2)
        self.assertIn("title does not match", errors[0])
        self.assertIn("not in the validated cache", errors[1])

    def test_normalize_doi_removes_bibtex_punctuation(self) -> None:
        self.assertEqual(
            validate_citations.normalize_doi("https://doi.org/10.1000/example.},"),
            "10.1000/example",
        )


if __name__ == "__main__":
    unittest.main()
