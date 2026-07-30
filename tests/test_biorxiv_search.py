import contextlib
import importlib.util
import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "biorxiv-search" / "scripts" / "search.py"


def load_search_module():
    spec = importlib.util.spec_from_file_location("biorxiv_search_script", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BioRxivPaginationTests(unittest.TestCase):
    def test_follows_api_totals_across_thirty_record_pages(self):
        module = load_search_module()
        records = [
            {
                "doi": f"10.1101/{index:06d}",
                "title": f"Preprint {index}",
                "abstract": "",
                "authors": "A. Author",
                "date": "2026-07-01",
                "version": "1",
            }
            for index in range(65)
        ]
        requested_cursors = []

        def fake_fetch(url, _timeout, *_retry):
            cursor = int(url.rsplit("/", 2)[-2])
            requested_cursors.append(cursor)
            page = records[cursor : cursor + 30]
            return {
                "messages": [
                    {
                        "status": "ok",
                        "cursor": cursor,
                        "count": len(page),
                        "total": len(records),
                    }
                ],
                "collection": page,
            }

        stdout = io.StringIO()
        argv = [str(SCRIPT), "--days", "7", "--scan-limit", "100"]
        with mock.patch.object(module, "fetch_json", side_effect=fake_fetch), mock.patch.object(
            sys, "argv", argv
        ), contextlib.redirect_stdout(stdout):
            exit_code = module.main()

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(requested_cursors, [0, 60, 30])
        self.assertEqual(payload["api"]["pages_fetched"], 3)
        self.assertEqual(payload["api"]["records_scanned"], 65)
        self.assertEqual(payload["api"]["total_available"], 65)
        self.assertFalse(payload["result_summary"]["reached_scan_limit"])

    def test_retry_backoff_covers_429_and_transient_5xx(self):
        module = load_search_module()
        errors = [
            urllib.error.HTTPError("https://example", 429, "rate", {"Retry-After": "0"}, io.BytesIO(b"rate")),
            urllib.error.HTTPError("https://example", 503, "busy", {}, io.BytesIO(b"busy")),
        ]

        class Response:
            headers = mock.Mock(get_content_charset=mock.Mock(return_value="utf-8"))
            def __enter__(self): return self
            def __exit__(self, *_): return False
            def read(self): return b'{"collection": []}'

        with mock.patch.object(module.urllib.request, "urlopen", side_effect=[*errors, Response()]), mock.patch.object(module.time, "sleep") as sleep:
            payload = module.fetch_json("https://example", 5, retries=2, retry_backoff=0)
        self.assertEqual(payload, {"collection": []})
        self.assertEqual(sleep.call_count, 2)

    def test_author_groups_and_latest_version_policy_are_explicit(self):
        module = load_search_module()
        records = [
            {"doi": "10.1/a", "authors_text": "Peter Nugent; A. Author"},
            {"doi": "10.1/b", "authors_text": "P. Nugent; B. Author"},
        ]
        groups = module.build_author_match_groups(records, ["Peter Nugent", "P. Nugent"])
        self.assertEqual([group["requested_form"] for group in groups], ["Peter Nugent", "P. Nugent"])
        self.assertFalse(groups[0]["ambiguous_initial_form"])
        self.assertTrue(groups[1]["ambiguous_initial_form"])

    def test_recent_search_scans_newest_records_first(self):
        module = load_search_module()
        records = [
            {
                "doi": f"10.1101/{index:06d}",
                "title": f"Preprint {index}",
                "abstract": "",
                "authors": "A. Author",
                "date": f"2026-07-{index + 1:02d}",
                "version": "1",
            }
            for index in range(20)
        ]
        requested_cursors = []

        def fake_fetch(url, _timeout, *_retry):
            cursor = int(url.rsplit("/", 2)[-2])
            requested_cursors.append(cursor)
            page = records[cursor : cursor + 10]
            return {
                "messages": [
                    {
                        "status": "ok",
                        "cursor": cursor,
                        "count": len(page),
                        "total": len(records),
                    }
                ],
                "collection": page,
            }

        stdout = io.StringIO()
        argv = [str(SCRIPT), "Preprint", "3", "--days", "30", "--scan-limit", "5"]
        with mock.patch.object(module, "fetch_json", side_effect=fake_fetch), mock.patch.object(
            sys, "argv", argv
        ), contextlib.redirect_stdout(stdout):
            exit_code = module.main()

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(requested_cursors, [0, 10])
        self.assertEqual(
            [record["doi"] for record in payload["results"]],
            ["10.1101/000019", "10.1101/000018", "10.1101/000017"],
        )

    def test_author_filter_matches_api_surname_initials_form(self):
        module = load_search_module()
        variants = module.expand_author_variants(["Frederik M. Schulz"])
        self.assertTrue(
            module.matches_author_filters("Schulz, F. M.; Other, A.", variants)
        )
        self.assertTrue(module.matches_author_filters("Frederik Schulz", variants))


if __name__ == "__main__":
    unittest.main()
