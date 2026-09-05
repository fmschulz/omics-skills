from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
import unittest.mock
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "scientific-impact-assessment"
MODULE_PATH = SKILL_ROOT / "scripts" / "measure_impact.py"

spec = importlib.util.spec_from_file_location("scientific_impact_assessment", MODULE_PATH)
assert spec is not None and spec.loader is not None
scientific_impact_assessment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scientific_impact_assessment)


class ScientificImpactAssessmentTests(unittest.TestCase):
    def test_fixture_report_matches_expected(self) -> None:
        metrics = scientific_impact_assessment.load_journal_metrics(
            SKILL_ROOT / "references" / "journal_metrics_2024.tsv"
        )
        openalex_payload = json.loads((SKILL_ROOT / "fixtures" / "openalex_work.json").read_text(encoding="utf-8"))
        altmetric_payload = json.loads((SKILL_ROOT / "fixtures" / "altmetric_counts.json").read_text(encoding="utf-8"))
        expected = json.loads((SKILL_ROOT / "fixtures" / "expected_report.json").read_text(encoding="utf-8"))

        report = scientific_impact_assessment.build_report_from_payloads(
            openalex_payload,
            metrics,
            altmetric_payload=altmetric_payload,
        )

        self.assertEqual(report, expected)

    def test_altmetric_is_explicitly_unavailable_without_key(self) -> None:
        summary = scientific_impact_assessment.summarize_altmetric_payload(None, reason="no_api_key")
        self.assertEqual(summary["status"], "unavailable")
        self.assertEqual(summary["reason"], "no_api_key")

    def test_openalex_id_uses_resolved_doi_for_altmetric(self) -> None:
        openalex_payload = json.loads(
            (SKILL_ROOT / "fixtures" / "openalex_work.json").read_text(encoding="utf-8")
        )
        args = SimpleNamespace(
            doi=None,
            openalex_id="W1234567890",
            mailto=None,
            altmetric_api_key="test-key",
            journal_metrics=str(SKILL_ROOT / "references" / "journal_metrics_2024.tsv"),
        )

        with (
            patch.object(
                scientific_impact_assessment,
                "fetch_openalex_work",
                return_value=openalex_payload,
            ),
            patch.object(
                scientific_impact_assessment,
                "fetch_altmetric_summary",
                return_value={"status": "available", "score": 1},
            ) as fetch_altmetric,
        ):
            report = scientific_impact_assessment.build_live_report(args)

        fetch_altmetric.assert_called_once_with(
            doi="10.1038/s41586-024-00000-0",
            api_key="test-key",
            min_interval=unittest.mock.ANY,
        )
        self.assertEqual(report["openalex"]["doi"], "10.1038/s41586-024-00000-0")

    def test_openalex_cache_reuses_fresh_and_refreshes_expired_response(self) -> None:
        payload = {"id": "https://openalex.org/W1"}
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            with patch.object(scientific_impact_assessment, "fetch_json", return_value=payload) as fetch:
                first = scientific_impact_assessment.fetch_openalex_cached("https://api.openalex.org/works/W1", cache_dir=cache_dir, cache_ttl=60, min_interval=0)
                second = scientific_impact_assessment.fetch_openalex_cached("https://api.openalex.org/works/W1", cache_dir=cache_dir, cache_ttl=60, min_interval=0)
                self.assertEqual(first, second)
                self.assertEqual(fetch.call_count, 1)
                cache = next((cache_dir / "responses").glob("*.json"))
                os.utime(cache, (1, 1))
                scientific_impact_assessment.fetch_openalex_cached("https://api.openalex.org/works/W1", cache_dir=cache_dir, cache_ttl=60, min_interval=0)
                self.assertEqual(fetch.call_count, 2)


if __name__ == "__main__":
    unittest.main()
