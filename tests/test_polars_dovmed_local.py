"""Tests for the polars-dovmed local scan wrapper."""

from __future__ import annotations

import importlib.util
import json
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
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class PolarsDovmedLocalTests(unittest.TestCase):
    def test_local_scan_uses_upstream_parquet_pattern_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_name:
            args = _args(Path(tmp_name))
            with patch.object(query_literature.subprocess, "run") as run:
                run.return_value = SimpleNamespace(returncode=0, stdout="", stderr="")
                response = query_literature.execute_local_scan(args)

        command = run.call_args.args[0]
        self.assertIn("--parquet-pattern", command)
        self.assertIn("/data/pmc/*.parquet", command)
        self.assertNotIn("--corpus", command)
        self.assertEqual(response["parquet_pattern"], "/data/pmc/*.parquet")

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
                with patch.object(query_literature.subprocess, "run") as run:
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
                with patch.object(query_literature.subprocess, "run") as run:
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


if __name__ == "__main__":
    unittest.main()
