from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
