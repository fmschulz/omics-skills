from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
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


def atom_feed(*abs_urls: str) -> str:
    entries = "".join(
        f"""<entry><id>{url}</id><title>Paper</title>
        <link rel="alternate" href="{url}"/></entry>"""
        for url in abs_urls
    )
    return f"""<feed xmlns="http://www.w3.org/2005/Atom">
    <updated>2026-01-01T00:00:00Z</updated>{entries}</feed>"""


class ArxivIdentifierTests(unittest.TestCase):
    def test_old_style_id_keeps_its_archive(self) -> None:
        parsed = arxiv_search.parse_feed(
            atom_feed(
                "http://arxiv.org/abs/hep-th/9901001v1",
                "http://arxiv.org/abs/2501.01234v2",
            )
        )
        self.assertEqual(
            [r["arxiv_id"] for r in parsed["results"]],
            ["hep-th/9901001v1", "2501.01234v2"],
        )

    def test_summarize_matches_requested_ids_ignoring_the_version_suffix(self) -> None:
        feed = arxiv_search.parse_feed(
            atom_feed(
                "http://arxiv.org/abs/2501.01234v2",
                "http://arxiv.org/abs/hep-th/9901001v1",
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            argv = [
                "arxiv_summarize.py",
                "2501.01234,hep-th/9901001,2406.00001",
                "--output-dir",
                tmp,
            ]
            stdout = io.StringIO()
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(
                    arxiv_summarize,
                    "fetch_results_by_ids",
                    return_value=("https://example.test", feed),
                ),
                contextlib.redirect_stdout(stdout),
            ):
                result = arxiv_summarize.main()
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(stdout.getvalue())["missing_ids"], ["2406.00001"])

    def test_summarize_reports_a_requested_version_that_was_not_returned(self) -> None:
        feed = arxiv_search.parse_feed(atom_feed("http://arxiv.org/abs/2501.01234v1"))
        with tempfile.TemporaryDirectory() as tmp:
            argv = [
                "arxiv_summarize.py",
                "2501.01234v1,2501.01234v999",
                "--output-dir",
                tmp,
            ]
            stdout = io.StringIO()
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(
                    arxiv_summarize,
                    "fetch_results_by_ids",
                    return_value=("https://example.test", feed),
                ),
                contextlib.redirect_stdout(stdout),
            ):
                result = arxiv_summarize.main()
        self.assertEqual(result, 0)
        self.assertEqual(
            json.loads(stdout.getvalue())["missing_ids"], ["2501.01234v999"]
        )


class ArxivRequestTests(unittest.TestCase):
    def run_search(self, argv: list[str]) -> dict[str, str]:
        with tempfile.TemporaryDirectory() as tmp:
            full_argv = ["arxiv_search.py", *argv, "--cache-dir", tmp]
            with (
                mock.patch.object(sys, "argv", full_argv),
                mock.patch.object(
                    arxiv_search,
                    "fetch_feed",
                    return_value=("https://example.test", atom_feed()),
                ) as fetch,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(arxiv_search.main(), 0)
        return fetch.call_args.args[0]

    def test_ids_request_as_many_results_as_ids_by_default(self) -> None:
        ids = ",".join(f"2501.{n:05d}" for n in range(1, 13))
        self.assertEqual(self.run_search(["--ids", ids])["max_results"], "12")

    def test_explicit_max_results_wins_over_the_id_count(self) -> None:
        # max_results is positional and follows the (ignored) query.
        argv = ["", "5", "--ids", "2501.00001,2501.00002"]
        self.assertEqual(self.run_search(argv)["max_results"], "5")

    def test_query_without_ids_keeps_the_default_of_ten(self) -> None:
        self.assertEqual(self.run_search(["protein folding"])["max_results"], "10")

    def test_category_binds_to_the_whole_raw_query(self) -> None:
        args = arxiv_search.build_parser().parse_args(
            ["ti:a OR ti:b", "--category", "cs.LG"]
        )
        self.assertEqual(
            arxiv_search.compile_search_query(args), "(ti:a OR ti:b) AND cat:cs.LG"
        )

    def test_raw_query_without_category_passes_through_unchanged(self) -> None:
        args = arxiv_search.build_parser().parse_args(["ti:a OR ti:b"])
        self.assertEqual(arxiv_search.compile_search_query(args), "ti:a OR ti:b")


if __name__ == "__main__":
    unittest.main()
