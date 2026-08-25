from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "skills" / "public-db-lookup" / "scripts" / "lookup.py"
SPEC = importlib.util.spec_from_file_location("public_db_lookup", MODULE_PATH)
public_db_lookup = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = public_db_lookup
SPEC.loader.exec_module(public_db_lookup)


def response(status_code: int, body: object = None, headers: dict[str, str] | None = None) -> Mock:
    text = body if isinstance(body, str) else json.dumps(body if body is not None else [])
    return Mock(status_code=status_code, text=text, headers={"content-type": "application/json", **(headers or {})})


def run(argv: list[str], session: Mock, env: dict[str, str] | None = None) -> tuple[int, dict]:
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        code = public_db_lookup.main(argv, session=session, env=env or {})
    return code, json.loads(stdout.getvalue())


class PublicDbLookupTests(unittest.TestCase):
    def test_compaction_bounds_records_and_reports_totals(self) -> None:
        session = Mock()
        session.get = Mock(return_value=response(200, {"results": [{"id": i} for i in range(7)]}))
        code, envelope = run(["--service", "uniprot", "--path", "uniprotkb/search", "--max-items", "3"], session)
        self.assertEqual(code, 0)
        self.assertTrue(envelope["ok"])
        self.assertEqual(envelope["record_path"], "results")
        self.assertEqual(len(envelope["records"]), 3)
        self.assertEqual(envelope["record_count_returned"], 3)
        self.assertEqual(envelope["record_count_available"], 7)
        self.assertTrue(envelope["truncated"])

    def test_retries_after_429_and_succeeds(self) -> None:
        session = Mock()
        session.get = Mock(side_effect=[response(429, "slow down", {"Retry-After": "0"}), response(200, [{"a": 1}])])
        code, envelope = run(["--service", "alphafold", "--path", "prediction/P04637"], session)
        self.assertEqual(code, 0)
        self.assertTrue(envelope["ok"])
        self.assertEqual(session.get.call_count, 2)

    def test_rejects_foreign_urls_and_cli_api_keys(self) -> None:
        session = Mock()
        env = {"NCBI_API_KEY": "topsecretkey"}
        code, envelope = run(["--service", "ncbi-entrez", "--path", "https://example.invalid/esearch.fcgi"], session, env)
        self.assertEqual((code, envelope["error"]["code"]), (2, "invalid_input"))
        code, envelope = run(["--service", "ncbi-entrez", "--path", "esearch.fcgi", "--param", "api_key=x"], session, env)
        self.assertEqual((code, envelope["error"]["code"]), (2, "invalid_input"))
        session.get.assert_not_called()

    def test_404_is_http_error_with_exit_1(self) -> None:
        session = Mock()
        session.get = Mock(return_value=response(404, "not found"))
        code, envelope = run(["--service", "uniprot", "--path", "uniprotkb/NOPE"], session)
        self.assertEqual(code, 1)
        self.assertFalse(envelope["ok"])
        self.assertEqual(envelope["error"]["code"], "http_error")

    def test_request_construction_for_every_service(self) -> None:
        env = {"NCBI_API_KEY": "topsecretkey"}
        for service, base in public_db_lookup.BASE_URLS.items():
            with self.subTest(service=service):
                args = public_db_lookup.parse_args(["--service", service, "--path", "some/path"])
                url, params, headers = public_db_lookup.build_request(args, env)
                self.assertTrue(url.startswith(base + "/"), url)
                self.assertEqual(headers["User-Agent"], public_db_lookup.USER_AGENT)
                if service in public_db_lookup.NCBI_SERVICES:
                    self.assertEqual(params["api_key"], "topsecretkey")
                    session = Mock()
                    session.get = Mock(return_value=response(200, []))
                    _, envelope = run(["--service", service, "--path", "some/path"], session, env)
                    self.assertEqual(session.get.call_args.kwargs["params"]["api_key"], "topsecretkey")
                    self.assertNotIn("topsecretkey", envelope["url"])
                    self.assertNotIn("topsecretkey", json.dumps(envelope))
                else:
                    self.assertNotIn("api_key", params)


if __name__ == "__main__":
    unittest.main()
