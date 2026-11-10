from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
import unittest.mock
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "crossref-lookup"
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
            altmetric=True,
            journal_metrics=str(SKILL_ROOT / "references" / "journal_metrics_2024.tsv"),
        )

        with (
            patch.dict(os.environ, {"ALTMETRIC_API_KEY": "test-key"}),
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

    def test_altmetric_key_and_mailto_are_not_command_line_defaults(self) -> None:
        environ = {"ALTMETRIC_API_KEY": "env-key", "OPENALEX_MAILTO": "env@example.org"}
        with patch.dict(os.environ, environ):
            parser = scientific_impact_assessment.build_parser()
            args = parser.parse_args(["--doi", "10.1038/nature12373"])
        self.assertIsNone(args.mailto)
        self.assertFalse(hasattr(args, "altmetric_api_key"))
        self.assertNotIn("--altmetric-api-key", parser.format_help())

        flagged = parser.parse_args(
            ["--doi", "10.1038/nature12373", "--mailto", "flag@example.org"]
        )
        self.assertEqual(flagged.mailto, "flag@example.org")

    def live_args(self, **overrides: object) -> SimpleNamespace:
        values = {
            "doi": "10.1038/s41586-024-00000-0",
            "openalex_id": None,
            "mailto": None,
            "altmetric": False,
            "journal_metrics": str(
                SKILL_ROOT / "references" / "journal_metrics_2024.tsv"
            ),
        }
        return SimpleNamespace(**(values | overrides))

    def openalex_payload(self) -> dict:
        return json.loads(
            (SKILL_ROOT / "fixtures" / "openalex_work.json").read_text(encoding="utf-8")
        )

    def test_an_ambient_altmetric_key_does_not_trigger_a_request(self) -> None:
        requested: list[str] = []

        def record(request: object, timeout: float = 0) -> None:
            requested.append(request.full_url)
            raise urllib.error.URLError("offline")

        with (
            patch.dict(os.environ, {"ALTMETRIC_API_KEY": "ambient-key"}),
            patch.object(
                scientific_impact_assessment,
                "fetch_openalex_work",
                return_value=self.openalex_payload(),
            ),
            patch("urllib.request.urlopen", side_effect=record),
        ):
            report = scientific_impact_assessment.build_live_report(self.live_args())

        self.assertEqual(requested, [])
        self.assertEqual(report["altmetric"]["reason"], "not_requested")

    def test_the_altmetric_flag_sends_the_environment_key_and_never_prints_it(
        self,
    ) -> None:
        requested: list[str] = []

        def record(request: object, timeout: float = 0) -> None:
            requested.append(request.full_url)
            raise urllib.error.HTTPError(request.full_url, 500, "boom", {}, None)

        with (
            patch.dict(os.environ, {"ALTMETRIC_API_KEY": "secret-key"}),
            patch.object(
                scientific_impact_assessment,
                "fetch_openalex_work",
                return_value=self.openalex_payload(),
            ),
            patch("urllib.request.urlopen", side_effect=record),
            patch("time.sleep"),
        ):
            report = scientific_impact_assessment.build_live_report(
                self.live_args(altmetric=True)
            )

        self.assertEqual(len(requested), 1)
        self.assertTrue(requested[0].startswith("https://api.altmetric.com/v1/doi/"))
        self.assertIn("key=secret-key", requested[0])
        shown = json.dumps(report) + scientific_impact_assessment.format_text(report)
        self.assertNotIn("secret-key", shown)
        self.assertEqual(report["altmetric"]["reason"], "http_500")

    def test_a_failure_message_never_carries_the_altmetric_key(self) -> None:
        def explode(request: object, timeout: float = 0) -> None:
            raise OSError(f"connection to {request.full_url} reset")

        with (
            patch.dict(os.environ, {"ALTMETRIC_API_KEY": "secret-key"}),
            patch("urllib.request.urlopen", side_effect=explode),
            patch("time.sleep"),
        ):
            summary = scientific_impact_assessment.fetch_altmetric_summary(
                "10.1038/nature12373", "secret-key", min_interval=0
            )

        self.assertEqual(summary["status"], "unavailable")
        self.assertNotIn("secret-key", json.dumps(summary))

    def test_the_altmetric_flag_without_a_key_makes_no_request(self) -> None:
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(
                scientific_impact_assessment,
                "fetch_openalex_work",
                return_value=self.openalex_payload(),
            ),
            patch("urllib.request.urlopen") as urlopen,
        ):
            report = scientific_impact_assessment.build_live_report(
                self.live_args(altmetric=True)
            )

        urlopen.assert_not_called()
        self.assertEqual(report["altmetric"]["reason"], "no_api_key")

    def test_the_command_line_takes_an_altmetric_flag_and_no_key(self) -> None:
        parser = scientific_impact_assessment.build_parser()
        self.assertFalse(parser.parse_args(["--doi", "10.1038/nature12373"]).altmetric)
        self.assertTrue(
            parser.parse_args(["--doi", "10.1038/nature12373", "--altmetric"]).altmetric
        )
        self.assertIn("ALTMETRIC_API_KEY", parser.format_help())

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
