from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
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

spec = importlib.util.spec_from_file_location("measure_impact", MODULE_PATH)
assert spec is not None and spec.loader is not None
measure_impact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(measure_impact)


class ScientificImpactAssessmentTests(unittest.TestCase):
    def test_fixture_report_matches_expected(self) -> None:
        openalex_payload = json.loads((SKILL_ROOT / "fixtures" / "openalex_work.json").read_text(encoding="utf-8"))
        altmetric_payload = json.loads((SKILL_ROOT / "fixtures" / "altmetric_counts.json").read_text(encoding="utf-8"))
        expected = json.loads((SKILL_ROOT / "fixtures" / "expected_report.json").read_text(encoding="utf-8"))

        report = measure_impact.build_report_from_payloads(
            openalex_payload,
            altmetric_payload=altmetric_payload,
        )

        self.assertEqual(report, expected)

    def test_altmetric_is_explicitly_unavailable_without_key(self) -> None:
        summary = measure_impact.summarize_altmetric_payload(None, reason="no_api_key")
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
        )

        with (
            patch.dict(os.environ, {"ALTMETRIC_API_KEY": "test-key"}),
            patch.object(
                measure_impact,
                "fetch_openalex_work",
                return_value=openalex_payload,
            ),
            patch.object(
                measure_impact,
                "fetch_altmetric_summary",
                return_value={"status": "available", "score": 1},
            ) as fetch_altmetric,
        ):
            report = measure_impact.build_live_report(args)

        fetch_altmetric.assert_called_once_with(
            doi="10.1038/s41586-024-00000-0",
            api_key="test-key",
            min_interval=unittest.mock.ANY,
        )
        self.assertEqual(report["openalex"]["doi"], "10.1038/s41586-024-00000-0")

    def test_altmetric_key_and_mailto_are_not_command_line_defaults(self) -> None:
        environ = {"ALTMETRIC_API_KEY": "env-key", "OPENALEX_MAILTO": "env@example.org"}
        with patch.dict(os.environ, environ):
            parser = measure_impact.build_parser()
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
                measure_impact,
                "fetch_openalex_work",
                return_value=self.openalex_payload(),
            ),
            patch("urllib.request.urlopen", side_effect=record),
        ):
            report = measure_impact.build_live_report(self.live_args())

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
                measure_impact,
                "fetch_openalex_work",
                return_value=self.openalex_payload(),
            ),
            patch("urllib.request.urlopen", side_effect=record),
            patch("time.sleep"),
        ):
            report = measure_impact.build_live_report(self.live_args(altmetric=True))

        self.assertEqual(len(requested), 1)
        self.assertTrue(requested[0].startswith("https://api.altmetric.com/v1/doi/"))
        self.assertIn("key=secret-key", requested[0])
        shown = json.dumps(report) + measure_impact.format_text(report)
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
            summary = measure_impact.fetch_altmetric_summary(
                "10.1038/nature12373", "secret-key", min_interval=0
            )

        self.assertEqual(summary["status"], "unavailable")
        self.assertNotIn("secret-key", json.dumps(summary))

    def test_the_altmetric_flag_without_a_key_makes_no_request(self) -> None:
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(
                measure_impact,
                "fetch_openalex_work",
                return_value=self.openalex_payload(),
            ),
            patch("urllib.request.urlopen") as urlopen,
        ):
            report = measure_impact.build_live_report(self.live_args(altmetric=True))

        urlopen.assert_not_called()
        self.assertEqual(report["altmetric"]["reason"], "no_api_key")

    def test_the_command_line_takes_an_altmetric_flag_and_no_key(self) -> None:
        parser = measure_impact.build_parser()
        self.assertFalse(parser.parse_args(["--doi", "10.1038/nature12373"]).altmetric)
        self.assertTrue(
            parser.parse_args(["--doi", "10.1038/nature12373", "--altmetric"]).altmetric
        )
        self.assertIn("ALTMETRIC_API_KEY", parser.format_help())

    def test_the_report_has_no_journal_impact_factor(self) -> None:
        report = measure_impact.build_report_from_payloads(self.openalex_payload())
        self.assertNotIn("journal_metric", report)
        self.assertNotIn("impact factor", measure_impact.format_text(report).lower())
        self.assertNotIn(
            "--journal-metrics", measure_impact.build_parser().format_help()
        )
        self.assertFalse(
            (SKILL_ROOT / "references" / "journal_metrics_2024.tsv").exists()
        )

    def test_the_openalex_key_comes_from_the_environment_as_a_bearer_header(
        self,
    ) -> None:
        seen: list[object] = []

        def record(request: object, timeout: float = 0) -> io.BytesIO:
            seen.append(request)
            return io.BytesIO(b"{}")

        with (
            patch.dict(os.environ, {"OPENALEX_API_KEY": "oa-secret"}),
            patch("urllib.request.urlopen", side_effect=record),
        ):
            measure_impact.fetch_openalex_json("https://api.openalex.org/works/W1")
        request = seen[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer oa-secret")
        self.assertNotIn("oa-secret", request.full_url)

    def test_no_openalex_key_sends_no_authorization_header(self) -> None:
        seen: list[object] = []

        def record(request: object, timeout: float = 0) -> io.BytesIO:
            seen.append(request)
            return io.BytesIO(b"{}")

        with (
            patch.dict(os.environ, {}, clear=True),
            patch("urllib.request.urlopen", side_effect=record),
        ):
            measure_impact.fetch_openalex_json("https://api.openalex.org/works/W1")
        self.assertFalse(seen[0].has_header("Authorization"))

    def test_the_openalex_key_is_not_a_command_line_option_and_is_redacted(
        self,
    ) -> None:
        self.assertNotIn("api-key", measure_impact.build_parser().format_help())
        with (
            patch.dict(os.environ, {"OPENALEX_API_KEY": "oa-secret"}),
            patch.object(
                measure_impact,
                "build_live_report",
                side_effect=RuntimeError("proxy echoed Bearer oa-secret"),
            ),
            patch.object(sys, "argv", ["measure-impact", "--doi", "10.1038/x1"]),
            contextlib.redirect_stderr(io.StringIO()) as stderr,
        ):
            code = measure_impact.main()
        self.assertEqual(code, 1)
        self.assertNotIn("oa-secret", stderr.getvalue())

    def http_429(self, retry_after: str | None) -> urllib.error.HTTPError:
        headers = {"Retry-After": retry_after} if retry_after else {}
        return urllib.error.HTTPError(
            "https://api.openalex.org/works/W1", 429, "Too Many", headers, None
        )

    def test_a_429_is_retried_after_the_retry_after_delay(self) -> None:
        outcomes = [self.http_429("2"), io.BytesIO(b'{"id": "W1"}')]

        def respond(request: object, timeout: float = 0) -> io.BytesIO:
            outcome = outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        with (
            patch("urllib.request.urlopen", side_effect=respond),
            patch("time.sleep") as sleep,
        ):
            payload = measure_impact.fetch_openalex_json(
                "https://api.openalex.org/works/W1"
            )
        self.assertEqual(payload, {"id": "W1"})
        sleep.assert_called_once_with(2.0)

    def test_a_429_without_retry_after_backs_off_and_attempts_are_bounded(
        self,
    ) -> None:
        with (
            patch(
                "urllib.request.urlopen",
                side_effect=lambda request, timeout=0: (_ for _ in ()).throw(
                    self.http_429(None)
                ),
            ) as urlopen,
            patch("time.sleep") as sleep,
            self.assertRaises(urllib.error.HTTPError),
        ):
            measure_impact.fetch_openalex_json("https://api.openalex.org/works/W1")
        self.assertEqual(urlopen.call_count, measure_impact.MAX_ATTEMPTS)
        self.assertEqual(sleep.call_count, measure_impact.MAX_ATTEMPTS - 1)

    def test_a_long_retry_after_is_capped(self) -> None:
        outcomes = [self.http_429("86400"), io.BytesIO(b"{}")]

        def respond(request: object, timeout: float = 0) -> io.BytesIO:
            outcome = outcomes.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        with (
            patch("urllib.request.urlopen", side_effect=respond),
            patch("time.sleep") as sleep,
        ):
            measure_impact.fetch_openalex_json("https://api.openalex.org/works/W1")
        sleep.assert_called_once_with(measure_impact.MAX_RETRY_WAIT_S)

    def test_output_refuses_to_overwrite_unless_forced(self) -> None:
        report = measure_impact.build_report_from_payloads(self.openalex_payload())
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "impact.json"
            target.write_text("old\n", encoding="utf-8")
            argv = ["measure-impact", "--doi", "10.1038/x1", "--output", str(target)]
            with (
                patch.object(measure_impact, "build_live_report", return_value=report),
                contextlib.redirect_stderr(io.StringIO()) as stderr,
            ):
                with patch.object(sys, "argv", argv):
                    refused = measure_impact.main()
                self.assertEqual(refused, 1)
                self.assertIn("refusing to overwrite", stderr.getvalue())
                self.assertEqual(target.read_text(encoding="utf-8"), "old\n")
                with patch.object(sys, "argv", [*argv, "--force"]):
                    forced = measure_impact.main()
            self.assertEqual(forced, 0)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), report)

    def test_output_created_during_the_run_is_not_overwritten(self) -> None:
        report = measure_impact.build_report_from_payloads(self.openalex_payload())
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "impact.json"
            argv = ["measure-impact", "--doi", "10.1038/x1", "--output", str(target)]

            def create_meanwhile(_args: object) -> dict:
                target.write_text("new\n", encoding="utf-8")
                return report

            with (
                patch.object(measure_impact, "build_live_report", create_meanwhile),
                contextlib.redirect_stderr(io.StringIO()) as stderr,
                patch.object(sys, "argv", argv),
            ):
                refused = measure_impact.main()
            self.assertEqual(refused, 1)
            self.assertIn("refusing to overwrite", stderr.getvalue())
            self.assertIn("--force", stderr.getvalue())
            self.assertEqual(target.read_text(encoding="utf-8"), "new\n")

    def test_openalex_cache_reuses_fresh_and_refreshes_expired_response(self) -> None:
        payload = {"id": "https://openalex.org/W1"}
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            with patch.object(
                measure_impact, "fetch_openalex_json", return_value=payload
            ) as fetch:
                first = measure_impact.fetch_openalex_cached(
                    "https://api.openalex.org/works/W1",
                    cache_dir=cache_dir,
                    cache_ttl=60,
                    min_interval=0,
                )
                second = measure_impact.fetch_openalex_cached(
                    "https://api.openalex.org/works/W1",
                    cache_dir=cache_dir,
                    cache_ttl=60,
                    min_interval=0,
                )
                self.assertEqual(first, second)
                self.assertEqual(fetch.call_count, 1)
                cache = next((cache_dir / "responses").glob("*.json"))
                os.utime(cache, (1, 1))
                measure_impact.fetch_openalex_cached(
                    "https://api.openalex.org/works/W1",
                    cache_dir=cache_dir,
                    cache_ttl=60,
                    min_interval=0,
                )
                self.assertEqual(fetch.call_count, 2)


if __name__ == "__main__":
    unittest.main()
