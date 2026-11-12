"""Tests for the polars-dovmed local scan wrapper."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import call, patch

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "skills" / "polars-dovmed" / "scripts" / "query_literature.py"
SPEC = importlib.util.spec_from_file_location("query_literature", MODULE_PATH)
query_literature = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = query_literature
SPEC.loader.exec_module(query_literature)


def _args(tmp: Path, **overrides):
    query_file = tmp / "query.json"
    query_file.write_text(json.dumps({"anchor": [["mirusvirus"]]}) + "\n", encoding="utf-8")
    repo_dir = tmp / "polars-dovmed"
    repo_dir.mkdir()
    values = {
        "query": None,
        "details": None,
        "group": [],
        "queries_file": str(query_file),
        "local_repo_dir": str(repo_dir),
        "local_output_dir": str(tmp / "results"),
        "local_parquet_pattern": "/data/pmc/*.parquet",
        "year_band": "all",
        "search_columns": "title,abstract_text,full_text",
        "extract_matches": "primary",
        "add_group_counts": "primary",
        "verbose": False,
        "save_payload": None,
        "save_response": None,
        "max_results": 25,
        "corpus": "pmc",
        "local_corpus": "pmc",
        "mode": "discovery",
        "sync": False,
        "year_bands": None,
        "skip_details_rerank": False,
        "force_details_rerank": False,
        "timeout": None,
        "corpus_revision": "pmc-fixture-2026-07",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class PolarsDovmedLocalTests(unittest.TestCase):
    def test_authenticated_api_rejects_insecure_remote_url(self) -> None:
        with self.assertRaisesRegex(ValueError, "require HTTPS"):
            query_literature.make_request(
                "http://api.example.org",
                "/api/search_literature",
                "secret",
            )
        request = query_literature.make_request(
            "http://127.0.0.1:8000",
            "/api/search_literature",
            "secret",
        )
        self.assertEqual(request.full_url, "http://127.0.0.1:8000/api/search_literature")

    def test_api_key_is_environment_only(self) -> None:
        help_result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--help"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertNotIn("--api-key", help_result.stdout)

    def test_a_request_without_a_key_sends_no_key_header(self) -> None:
        """The hosted API answers anonymously, so the header is sent only with a key."""
        anonymous = query_literature.make_request(
            "https://api.example.org", "/api/usage", None
        )
        self.assertNotIn("x-api-key", {name.lower() for name in anonymous.headers})
        keyed = query_literature.make_request(
            "https://api.example.org", "/api/usage", "secret"
        )
        self.assertEqual(keyed.get_header("X-api-key"), "secret")

    def test_the_api_key_is_optional(self) -> None:
        with patch.dict(query_literature.os.environ, {}, clear=True):
            self.assertIsNone(query_literature.load_api_key())
        with patch.dict(
            query_literature.os.environ, {"POLARS_DOVMED_API_KEY": "secret"}, clear=True
        ):
            self.assertEqual(query_literature.load_api_key(), "secret")

    def test_auto_mode_without_a_key_or_parquet_uses_the_hosted_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            args = _args(
                Path(tmp_name), execution_mode="auto", local_parquet_pattern=None
            )
        with patch.dict(query_literature.os.environ, {}, clear=True):
            self.assertEqual(query_literature.determine_execution_mode(args), "api")
        with patch.dict(
            query_literature.os.environ,
            {"DOVMED_PMC_PARQUET": "/data/*.parquet"},
            clear=True,
        ):
            self.assertEqual(query_literature.determine_execution_mode(args), "local")

    def test_local_scan_reports_a_missing_repo_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            args = _args(Path(tmp_name), local_repo_dir="/nonexistent/repo")
            with self.assertRaisesRegex(SystemExit, "/nonexistent/repo"):
                query_literature.execute_local_scan(args)

    def test_local_scan_uses_upstream_parquet_pattern_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            args = _args(Path(tmp_name))
            with patch.object(
                query_literature,
                "resolve_pixi_executable",
                return_value="/usr/bin/pixi",
            ), patch.object(query_literature.subprocess, "run") as run:
                run.return_value = SimpleNamespace(returncode=0, stdout="", stderr="")
                response = query_literature.execute_local_scan(args)

        command = run.call_args.args[0]
        self.assertIn("--parquet-pattern", command)
        self.assertIn("/data/pmc/*.parquet", command)
        self.assertNotIn("--corpus", command)
        self.assertEqual(response["parquet_pattern"], "/data/pmc/*.parquet")
        self.assertEqual(run.call_args.kwargs["timeout"], 900)

    def test_local_scan_resolves_pixi_from_path(self) -> None:
        with patch.object(query_literature.shutil, "which", return_value="/opt/pixi/bin/pixi"):
            executable = query_literature.resolve_pixi_executable()

        self.assertEqual(executable, "/opt/pixi/bin/pixi")

    def test_local_scan_reads_flattened_csv_without_polars(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            args = _args(tmp)
            output_dir = Path(args.local_output_dir)
            output_dir.mkdir(parents=True)
            (output_dir / "flattened.csv").write_text(
                "pmc_id,doi,title,journal,publication_date,source,total_matches\n"
                "PMC1,10.1/example,Example paper,Example Journal,2025-01-02,pmc,3\n",
                encoding="utf-8",
            )
            with patch.object(
                query_literature,
                "resolve_pixi_executable",
                return_value="/usr/bin/pixi",
            ), patch.object(query_literature.subprocess, "run") as run:
                run.return_value = SimpleNamespace(returncode=0, stdout="", stderr="")
                response = query_literature.execute_local_scan(args)

        self.assertEqual(response["papers"][0]["pmc_id"], "PMC1")
        self.assertEqual(response["papers"][0]["year"], 2025)
        self.assertEqual(response["paper_source_artifact"], "flattened_csv")
        self.assertEqual(response["corpus_revision"], "pmc-fixture-2026-07")

    def test_local_scan_falls_back_to_processed_parquet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            tmp = Path(tmp_name)
            args = _args(tmp)
            output_dir = Path(args.local_output_dir)
            output_dir.mkdir(parents=True)
            (output_dir / "processed.parquet").write_bytes(b"fixture parquet sentinel")

            class Frame:
                def head(self, _limit): return self
                def to_dicts(self):
                    return [{"pmc_id": "PMC2", "doi": "10.1/processed", "title": "Processed paper", "journal": "Fixture", "publication_date": "2024-03-04", "source": "pmc", "total_matches": 2}]

            fake_polars = SimpleNamespace(read_parquet=lambda _path: Frame())
            with patch.dict(sys.modules, {"polars": fake_polars}), patch.object(query_literature, "resolve_pixi_executable", return_value="/usr/bin/pixi"), patch.object(query_literature.subprocess, "run") as run:
                run.return_value = SimpleNamespace(returncode=0, stdout="", stderr="")
                response = query_literature.execute_local_scan(args)

        self.assertEqual(response["papers"][0]["pmc_id"], "PMC2")
        self.assertEqual(response["paper_source_artifact"], "processed_parquet")
        self.assertEqual(response["corpus_revision"], "pmc-fixture-2026-07")

    def test_local_scan_enforces_subprocess_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            args = _args(Path(tmp_name), timeout=7)
            with patch.object(
                query_literature,
                "resolve_pixi_executable",
                return_value="/usr/bin/pixi",
            ), patch.object(
                query_literature.subprocess,
                "run",
                side_effect=subprocess.TimeoutExpired(["pixi"], 7),
            ):
                with self.assertRaisesRegex(SystemExit, "timed out after 7 seconds"):
                    query_literature.execute_local_scan(args)

    def test_local_scan_resolves_paths_before_changing_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            args = _args(
                Path(tmp_name),
                queries_file="tasks/example-query.json",
                local_output_dir="tasks/local-output",
            )
            with patch.object(
                query_literature,
                "load_queries_file",
                return_value={"anchor": [["mirusvirus"]]},
            ):
                with patch.object(
                    query_literature,
                    "resolve_pixi_executable",
                    return_value="/usr/bin/pixi",
                ), patch.object(query_literature.subprocess, "run") as run:
                    run.return_value = SimpleNamespace(returncode=0, stdout="", stderr="")
                    query_literature.execute_local_scan(args)

        command = run.call_args.args[0]
        self.assertIn(str((REPO_ROOT / "tasks/example-query.json").resolve()), command)
        self.assertIn(str((REPO_ROOT / "tasks/local-output").resolve()), command)
        self.assertEqual(run.call_args.kwargs["cwd"], Path(args.local_repo_dir).resolve())

    def test_local_scan_can_use_corpus_env_var(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            args = _args(
                Path(tmp_name),
                corpus="biorxiv",
                local_parquet_pattern=None,
            )
            with patch.dict(
                query_literature.os.environ,
                {"DOVMED_BIORXIV_PARQUET": "/data/biorxiv/*.parquet"},
                clear=True,
            ):
                with patch.object(
                    query_literature,
                    "resolve_pixi_executable",
                    return_value="/usr/bin/pixi",
                ), patch.object(query_literature.subprocess, "run") as run:
                    run.return_value = SimpleNamespace(returncode=0, stdout="", stderr="")
                    response = query_literature.execute_local_scan(args)

        self.assertEqual(response["parquet_pattern"], "/data/biorxiv/*.parquet")

    def test_local_scan_reports_missing_parquet_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            args = _args(Path(tmp_name), local_parquet_pattern=None)
            with patch.dict(query_literature.os.environ, {}, clear=True):
                with self.assertRaisesRegex(SystemExit, "DOVMED_PMC_PARQUET"):
                    query_literature.execute_local_scan(args)

    def test_pmc_year_band_discovery_uses_sync_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            args = _args(Path(tmp_name), year_bands=["2024_plus"])
            payload = {"corpus": "pmc", "mode": "discovery"}

        self.assertFalse(
            query_literature.should_use_async_jobs(
                args,
                "/api/scan_literature_advanced",
                payload,
            )
        )

    def test_non_pmc_discovery_keeps_async_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            args = _args(Path(tmp_name), corpus="biorxiv", year_bands=None)
            payload = {"corpus": "biorxiv", "mode": "discovery"}

        self.assertTrue(
            query_literature.should_use_async_jobs(
                args,
                "/api/scan_literature_advanced",
                payload,
            )
        )

    def test_pmc_year_band_discovery_skips_details_unless_forced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            args = _args(Path(tmp_name), year_bands=["2024_plus"])
            payload = {
                "corpus": "pmc",
                "mode": "discovery",
                "primary_queries": {"anchor": [["mirusvirus"]]},
            }
            result = {"papers": [{"pmc_id": "PMC10827195"}]}

        self.assertFalse(
            query_literature.should_run_details_rerank(
                args,
                "/api/scan_literature_advanced",
                payload,
                result,
            )
        )
        args.force_details_rerank = True
        self.assertTrue(
            query_literature.should_run_details_rerank(
                args,
                "/api/scan_literature_advanced",
                payload,
                result,
            )
        )

    def test_crossref_email_comes_only_from_the_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_dir = Path(tmp) / ".config" / "polars-dovmed"
            env_dir.mkdir(parents=True)
            (env_dir / ".env").write_text("CROSSREF_EMAIL=from-file@example.org\n", encoding="utf-8")
            environ = {"HOME": tmp, "CROSSREF_EMAIL": "from-env@example.org"}
            with patch.dict("os.environ", environ), patch.object(
                sys, "argv", ["query_literature.py", "--queries-file", "q.json"]
            ):
                self.assertEqual(query_literature.parse_args().crossref_email, "")
            with patch.dict("os.environ", environ), patch.object(
                sys,
                "argv",
                ["query_literature.py", "--queries-file", "q.json", "--crossref-email", "flag@example.org"],
            ):
                self.assertEqual(query_literature.parse_args().crossref_email, "flag@example.org")

    def test_crossref_metadata_enrichment_fills_missing_fields(self) -> None:
        papers = [
            {
                "title": "Example environmental genomics paper",
                "doi": None,
                "year": None,
                "journal": None,
            }
        ]
        item = {
            "DOI": "10.1234/example",
            "title": ["Example environmental genomics paper"],
            "container-title": ["Journal of Examples"],
            "issued": {"date-parts": [[2025, 1, 2]]},
        }

        with patch.object(
            query_literature,
            "best_crossref_match",
            return_value=(item, 0.99),
        ) as lookup:
            enriched, metadata = query_literature.enrich_compact_with_crossref(
                papers,
                limit=1,
                email="test@example.org",
            )

        self.assertEqual(enriched[0]["doi"], "10.1234/example")
        self.assertEqual(enriched[0]["doi_source"], "crossref")
        self.assertEqual(enriched[0]["year"], 2025)
        self.assertEqual(enriched[0]["journal"], "Journal of Examples")
        self.assertEqual(metadata["lookups"], 1)
        self.assertEqual(metadata["matches"], 1)
        lookup.assert_called_once_with(
            "Example environmental genomics paper",
            email="test@example.org",
        )

    def test_crossref_metadata_enrichment_respects_limit(self) -> None:
        papers = [
            {"title": "Paper one", "doi": None, "year": None, "journal": None},
            {"title": "Paper two", "doi": None, "year": None, "journal": None},
        ]

        with patch.object(
            query_literature,
            "best_crossref_match",
            return_value=(None, 0.0),
        ) as lookup:
            _enriched, metadata = query_literature.enrich_compact_with_crossref(
                papers,
                limit=1,
            )

        self.assertEqual(metadata["lookups"], 1)
        lookup.assert_called_once()

    def test_analyze_paper_keeps_its_scores_when_it_reuses_the_context_analysis(
        self,
    ) -> None:
        paper = {
            "title": "Mirusvirus host range",
            "abstract_text": "Mirusvirus infection of protists.",
            "full_text": "The host range of mirusvirus was tested in detail.",
        }
        queries = {
            "anchor_entity": [["mirusvirus"]],
            "host_relation": [["host range"], ["infection"]],
            "disqualifying_terms": [["plant"]],
        }
        analysis = query_literature.analyze_paper_against_queries(paper, queries)
        self.assertEqual(
            analysis,
            {
                "matched_group_counts": {"anchor_entity": 1, "host_relation": 2},
                "matched_group_scores": {"anchor_entity": 1.8, "host_relation": 4.2},
                "matched_concepts": ["anchor_entity", "host_relation"],
                "concept_coverage": 2,
                "support_concept_coverage": 1,
                "support_specificity_score": 4.2,
                "specific_support_group_hits": 1,
                "title_support_hits": 1,
                "abstract_support_hits": 1,
                "full_text_support_hits": 1,
                "total_group_matches": 3,
            },
        )

    def anonymous_clock(self, tmp: Path):
        """Patch time so a sleep advances the clock; return the list of sleeps."""
        now = [1_000.0]
        sleeps: list[float] = []

        def fake_sleep(seconds: float) -> None:
            sleeps.append(seconds)
            now[0] += seconds

        stack = contextlib.ExitStack()
        stack.enter_context(patch.object(query_literature.time, "time", lambda: now[0]))
        stack.enter_context(patch.object(query_literature.time, "sleep", fake_sleep))
        self.addCleanup(stack.close)
        return sleeps

    def test_anonymous_requests_are_limited_to_20_per_minute_across_calls(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            state_dir = Path(tmp_name)
            sleeps = self.anonymous_clock(state_dir)
            for _ in range(20):
                query_literature.wait_for_anonymous_slot(state_dir)
            self.assertEqual(sleeps, [])
            query_literature.wait_for_anonymous_slot(state_dir)
            self.assertEqual(len(sleeps), 1)
            self.assertAlmostEqual(sleeps[0], 60.0, delta=0.5)
            # The window slides: 20 more calls fit once the minute has passed.
            for _ in range(19):
                query_literature.wait_for_anonymous_slot(state_dir)
            self.assertEqual(len(sleeps), 1)

    def test_a_corrupt_pacer_state_file_is_reported_not_reset(self) -> None:
        for content in ("not json", '{"a": 1}', '[1, "x"]', "[NaN]"):
            with (
                self.subTest(content=content),
                tempfile.TemporaryDirectory() as tmp_name,
            ):
                state_dir = Path(tmp_name)
                sleeps = self.anonymous_clock(state_dir)
                state_path = state_dir / "anonymous-requests.json"
                state_path.write_text(content, encoding="utf-8")
                with self.assertRaises(query_literature.RateLimitStateError) as ctx:
                    query_literature.wait_for_anonymous_slot(state_dir)
                message = str(ctx.exception)
                self.assertIn(str(state_path), message)
                self.assertIn("Delete", message)
                self.assertEqual(sleeps, [])
                self.assertEqual(state_path.read_text(encoding="utf-8"), content)

    def test_an_unlockable_pacer_state_refuses_the_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            state_dir = Path(tmp_name)
            sleeps = self.anonymous_clock(state_dir)
            with (
                patch.object(
                    query_literature.fcntl, "flock", side_effect=OSError("no locks")
                ),
                self.assertRaises(query_literature.RateLimitStateError) as ctx,
            ):
                query_literature.wait_for_anonymous_slot(state_dir)
            self.assertIn(str(state_dir), str(ctx.exception))
            self.assertIn("API key", str(ctx.exception))
            self.assertEqual(sleeps, [])

    def test_an_unwritable_pacer_state_refuses_the_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            state_dir = Path(tmp_name)
            sleeps = self.anonymous_clock(state_dir)
            with (
                patch.object(
                    query_literature.os, "replace", side_effect=OSError("read-only")
                ),
                self.assertRaises(query_literature.RateLimitStateError) as ctx,
            ):
                query_literature.wait_for_anonymous_slot(state_dir)
            self.assertIn(str(state_dir), str(ctx.exception))
            self.assertIn("API key", str(ctx.exception))
            self.assertEqual(sleeps, [])
            self.assertEqual(
                sorted(p.name for p in state_dir.iterdir()), ["anonymous-requests.lock"]
            )

    def test_an_unusable_pacer_state_directory_refuses_the_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            blocker = Path(tmp_name) / "file"
            blocker.write_text("x", encoding="utf-8")
            sleeps = self.anonymous_clock(blocker)
            with self.assertRaises(query_literature.RateLimitStateError) as ctx:
                query_literature.wait_for_anonymous_slot(blocker / "state")
            self.assertIn(str(blocker / "state"), str(ctx.exception))
            self.assertEqual(sleeps, [])

    def test_the_pacer_state_is_written_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            state_dir = Path(tmp_name)
            self.anonymous_clock(state_dir)
            with patch.object(
                query_literature.os, "replace", wraps=query_literature.os.replace
            ) as replace:
                query_literature.wait_for_anonymous_slot(state_dir)
            replace.assert_called_once()
            source, target = (Path(arg) for arg in replace.call_args.args)
            self.assertEqual(source.parent, state_dir)
            self.assertEqual(target, state_dir / "anonymous-requests.json")
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), [1_000.0])
            self.assertEqual(
                sorted(p.name for p in state_dir.iterdir()),
                ["anonymous-requests.json", "anonymous-requests.lock"],
            )

    def test_pacer_timestamps_far_in_the_future_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            state_dir = Path(tmp_name)
            sleeps = self.anonymous_clock(state_dir)
            (state_dir / "anonymous-requests.json").write_text(
                json.dumps([1_000.0 + 61.0] * 25), encoding="utf-8"
            )
            query_literature.wait_for_anonymous_slot(state_dir)
            self.assertEqual(sleeps, [])

    def test_only_anonymous_requests_are_paced(self) -> None:
        with (
            patch.object(query_literature, "wait_for_anonymous_slot") as pace,
            patch.object(
                query_literature.urllib.request,
                "urlopen",
                side_effect=lambda *args, **kwargs: io.BytesIO(b"{}"),
            ),
        ):
            query_literature.request_json(
                "https://api.example.org", "/api/usage", "secret", timeout=5
            )
            pace.assert_not_called()
            query_literature.request_json(
                "https://api.example.org", "/api/usage", None, timeout=5
            )
            pace.assert_called_once()

    def test_request_json_retries_503_then_returns_payload(self) -> None:
        error = query_literature.urllib.error.HTTPError(
            "https://api.example.org/api/jobs", 503, "Async job queue is full", {}, None
        )
        stderr = io.StringIO()
        with (
            patch.object(
                query_literature.urllib.request,
                "urlopen",
                side_effect=[error, io.BytesIO(b'{"job_id": "example"}')],
            ) as urlopen,
            patch.object(query_literature.time, "sleep") as sleep,
            contextlib.redirect_stderr(stderr),
        ):
            payload = query_literature.request_json(
                "https://api.example.org",
                "/api/jobs",
                "secret",
                timeout=5,
                method="POST",
                payload={"query": "mirusvirus"},
            )
        self.assertEqual(payload, {"job_id": "example"})
        sleep.assert_called_once_with(2)
        self.assertEqual(urlopen.call_count, 2)
        self.assertEqual(urlopen.call_args_list[0], urlopen.call_args_list[1])
        request = urlopen.call_args.args[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(json.loads(request.data), {"query": "mirusvirus"})
        self.assertEqual(len(stderr.getvalue().splitlines()), 1)
        self.assertIn("503", stderr.getvalue())
        self.assertIn("2s", stderr.getvalue())
        self.assertIn("1/5", stderr.getvalue())

    def test_request_json_honors_numeric_retry_after_with_a_cap(self) -> None:
        for retry_after, expected_wait in (("7", 7), ("120", 60)):
            with self.subTest(retry_after=retry_after):
                error = query_literature.urllib.error.HTTPError(
                    "https://api.example.org/api/usage",
                    503,
                    "busy",
                    {"Retry-After": retry_after},
                    None,
                )
                with (
                    patch.object(
                        query_literature.urllib.request,
                        "urlopen",
                        side_effect=[error, io.BytesIO(b"{}")],
                    ),
                    patch.object(query_literature.time, "sleep") as sleep,
                ):
                    query_literature.request_json(
                        "https://api.example.org", "/api/usage", "secret", timeout=5
                    )
                sleep.assert_called_once_with(expected_wait)

    def test_request_json_stops_after_five_503_retries(self) -> None:
        errors = [
            query_literature.urllib.error.HTTPError(
                "https://api.example.org/api/usage", 503, f"busy {attempt}", {}, None
            )
            for attempt in range(6)
        ]
        stderr = io.StringIO()
        with (
            patch.object(
                query_literature.urllib.request, "urlopen", side_effect=errors
            ) as urlopen,
            patch.object(query_literature.time, "sleep") as sleep,
            contextlib.redirect_stderr(stderr),
            self.assertRaises(query_literature.urllib.error.HTTPError) as raised,
        ):
            query_literature.request_json(
                "https://api.example.org", "/api/usage", "secret", timeout=5
            )
        self.assertIs(raised.exception, errors[-1])
        self.assertEqual(urlopen.call_count, 6)
        self.assertEqual(
            sleep.call_args_list, [call(2), call(4), call(8), call(16), call(30)]
        )
        self.assertEqual(len(stderr.getvalue().splitlines()), 5)
        self.assertIn("5/5", stderr.getvalue())

    def test_request_json_does_not_retry_500(self) -> None:
        error = query_literature.urllib.error.HTTPError(
            "https://api.example.org/api/usage", 500, "server error", {}, None
        )
        with (
            patch.object(
                query_literature.urllib.request, "urlopen", side_effect=error
            ) as urlopen,
            patch.object(query_literature.time, "sleep") as sleep,
            self.assertRaises(query_literature.urllib.error.HTTPError) as raised,
        ):
            query_literature.request_json(
                "https://api.example.org", "/api/usage", "secret", timeout=5
            )
        self.assertIs(raised.exception, error)
        urlopen.assert_called_once()
        sleep.assert_not_called()

    def test_request_json_paces_every_anonymous_attempt(self) -> None:
        error = query_literature.urllib.error.HTTPError(
            "https://api.example.org/api/usage", 503, "busy", {}, None
        )
        with (
            patch.object(query_literature, "wait_for_anonymous_slot") as pace,
            patch.object(
                query_literature.urllib.request,
                "urlopen",
                side_effect=[error, io.BytesIO(b"{}")],
            ) as urlopen,
            patch.object(query_literature.time, "sleep"),
        ):
            query_literature.request_json(
                "https://api.example.org", "/api/usage", None, timeout=5
            )
        self.assertEqual(urlopen.call_count, 2)
        self.assertEqual(pace.call_count, 2)

    def test_corpus_both_is_rejected_with_a_clear_message(self) -> None:
        stderr = io.StringIO()
        with (
            patch.object(
                sys,
                "argv",
                ["query_literature.py", "--queries-file", "q.json", "--corpus", "both"],
            ),
            contextlib.redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            query_literature.parse_args()
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("separate calls", stderr.getvalue())

    def test_no_code_path_names_a_missing_endpoint(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("discover_literature", source)

    def test_the_smoke_query_uses_bare_words_as_the_skill_requires(self) -> None:
        fixture = MODULE_PATH.parents[1] / "fixtures" / "smoke_query.json"
        concepts = json.loads(fixture.read_text(encoding="utf-8"))
        terms = [t for groups in concepts.values() for group in groups for t in group]
        self.assertTrue(terms)
        for term in terms:
            self.assertRegex(term, r"^[A-Za-z0-9][A-Za-z0-9 -]*$")

    def test_the_recipes_do_not_pass_the_legacy_sync_flag(self) -> None:
        skill_dir = MODULE_PATH.parents[1]
        for name in ("SKILL.md", "references/commands.md"):
            text = (skill_dir / name).read_text(encoding="utf-8")
            self.assertNotIn("--sync", text, name)


if __name__ == "__main__":
    unittest.main()
