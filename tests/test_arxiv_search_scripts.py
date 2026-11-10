from __future__ import annotations

import contextlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "skills" / "preprint-search" / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


arxiv_search = load_module("arxiv_search", SCRIPT_DIR / "arxiv_search.py")
arxiv_summarize = load_module("arxiv_summarize", SCRIPT_DIR / "arxiv_summarize.py")


class ArxivQueryDetectionTests(unittest.TestCase):
    def test_plain_scientific_terms_are_not_mistaken_for_raw_syntax(self) -> None:
        for query in (
            "ORF prediction",
            "OR-Tools optimization",
            "AND-gate circuits",
            "protein folding (deep learning)",
            "single cell [atlas]",
        ):
            with self.subTest(query=query):
                self.assertFalse(arxiv_search.is_raw_query(query))

    def test_explicit_fields_and_standalone_boolean_operators_are_raw(self) -> None:
        for query in (
            'ti:"protein structure"',
            "cat:q-bio.GN",
            "submittedDate:[20260101 TO 20260131]",
            "protein structure OR protein folding",
            "virus ANDNOT phage",
        ):
            with self.subTest(query=query):
                self.assertTrue(arxiv_search.is_raw_query(query))


class ArxivCacheAndPacingTests(unittest.TestCase):
    def test_expired_cache_is_refetched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            params = {"search_query": "all:test", "start": "0", "max_results": "1"}
            query = arxiv_search.urllib.parse.urlencode(params, quote_via=arxiv_search.urllib.parse.quote)
            url = f"{arxiv_search.API_URL}?{query}"
            cached = arxiv_search.cache_path(cache_dir, url)
            cached.parent.mkdir(parents=True)
            cached.write_text("stale")
            os.utime(cached, (1, 1))
            with mock.patch.object(arxiv_search, "wait_for_pacing"), mock.patch.object(arxiv_search, "fetch_url_once", return_value="fresh") as fetch:
                _, text = arxiv_search.fetch_feed(params, 20, cache_dir, False, 3.1, 0, 0, cache_ttl=60)
            self.assertEqual(text, "fresh")
            fetch.assert_called_once()

    def test_pacing_state_is_guarded_by_cross_process_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(arxiv_search.fcntl, "flock") as flock:
            arxiv_search.wait_for_pacing(Path(tmp), 0.001)
            self.assertEqual(flock.call_args_list[0].args[1], arxiv_search.fcntl.LOCK_EX)
            self.assertEqual(flock.call_args_list[-1].args[1], arxiv_search.fcntl.LOCK_UN)


class ArxivSummarizeTests(unittest.TestCase):
    def test_main_forwards_cache_and_retry_options_without_network_access(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "summaries"
            cache_dir = Path(tmp) / "cache"
            argv = [
                "arxiv_summarize.py",
                "1706.03762",
                "--output-dir",
                str(output_dir),
                "--cache-dir",
                str(cache_dir),
                "--no-cache",
                "--min-interval",
                "0.5",
                "--retries",
                "1",
                "--retry-backoff",
                "2",
            ]

            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(
                    arxiv_summarize,
                    "fetch_results_by_ids",
                    return_value=("https://example.test/query", {"results": []}),
                ) as fetch,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                result = arxiv_summarize.main()

            self.assertEqual(result, 0)
            fetch.assert_called_once_with(
                ["1706.03762"],
                20,
                cache_dir=cache_dir,
                no_cache=True,
                min_interval=0.5,
                retries=1,
                retry_backoff=2.0,
            )


if __name__ == "__main__":
    unittest.main()
