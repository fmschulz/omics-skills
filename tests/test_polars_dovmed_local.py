"""Tests for the polars-dovmed local scan wrapper."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

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


if __name__ == "__main__":
    unittest.main()
