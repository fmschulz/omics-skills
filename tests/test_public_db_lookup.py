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
                    self.assertIn(("api_key", "topsecretkey"), params)
                    session = Mock()
                    session.get = Mock(return_value=response(200, []))
                    _, envelope = run(["--service", service, "--path", "some/path"], session, env)
                    self.assertIn(("api_key", "topsecretkey"), session.get.call_args.kwargs["params"])
                    self.assertNotIn("topsecretkey", envelope["url"])
                    self.assertNotIn("topsecretkey", json.dumps(envelope))
                else:
                    self.assertNotIn("api_key", params)




class CredentialHandlingTests(unittest.TestCase):
    """A key embedded in --path bypassed the --param filter and rode straight
    into the emitted `url` field; successful bodies were never redacted."""

    def test_credentials_are_rejected_wherever_they_are_supplied(self) -> None:
        import argparse

        for path, param in (
            ("esearch.fcgi?db=protein&api_key=SYNTHETIC", []),
            ("esearch.fcgi?token=SYNTHETIC", []),
            ("esearch.fcgi?access-token=SYNTHETIC", []),
            ("esearch.fcgi", ["api_key=SYNTHETIC"]),
        ):
            with self.subTest(path=path, param=param):
                args = argparse.Namespace(
                    service="ncbi-entrez", path=path, param=list(param),
                    max_items=5, max_depth=3, format="auto",
                )
                with self.assertRaisesRegex(ValueError, "through the environment"):
                    public_db_lookup.build_request(args, {})

    def test_ordinary_query_parameters_in_the_path_still_work(self) -> None:
        import argparse

        args = argparse.Namespace(
            service="ncbi-entrez", path="esearch.fcgi?db=protein&term=p53", param=[],
            max_items=5, max_depth=3, format="auto",
        )
        url, params, _ = public_db_lookup.build_request(args, {})
        self.assertTrue(url.endswith("/esearch.fcgi"))
        self.assertEqual(params, [("db", "protein"), ("term", "p53")])

    def test_api_key_is_redacted_from_a_successful_response_body(self) -> None:
        session = Mock()
        session.get = Mock(return_value=response(200, {"results": [{"echo": "api_key=SYNTHETIC"}]}))
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = public_db_lookup.main(
                ["--service", "ncbi-entrez", "--path", "esearch.fcgi"],
                session=session,
                env={"NCBI_API_KEY": "SYNTHETIC"},
            )
        self.assertEqual(code, 0)
        self.assertNotIn("SYNTHETIC", stdout.getvalue())
        self.assertIn("REDACTED", stdout.getvalue())

    def test_http_200_error_envelope_is_not_a_successful_empty_result(self) -> None:
        """Several services report failures as HTTP 200 with an error body;
        reporting ok:true turned a rejected query into a confident answer."""
        for body in ({"error": "Invalid db name"}, {"esearchresult": {"ERROR": "Invalid db name"}}):
            with self.subTest(body=body):
                session = Mock()
                session.get = Mock(return_value=response(200, body))
                code, envelope = run(["--service", "ncbi-entrez", "--path", "esearch.fcgi"], session)
                self.assertEqual(code, 1)
                self.assertFalse(envelope["ok"])
                self.assertEqual(envelope["error"]["code"], "service_error")

    def test_repeated_query_parameters_are_preserved(self) -> None:
        """Entrez ELink takes several `id=` values and pairs them with its
        outputs; collapsing them into a dict dropped all but the last."""
        import argparse

        args = argparse.Namespace(
            service="ncbi-entrez",
            path="elink.fcgi?dbfrom=protein&db=gene&id=15718680&id=157427902",
            param=[], max_items=5, max_depth=3, format="auto",
        )
        _, params, _ = public_db_lookup.build_request(args, {})
        self.assertEqual(
            [value for key, value in params if key == "id"],
            ["15718680", "157427902"],
        )

if __name__ == "__main__":
    unittest.main()
