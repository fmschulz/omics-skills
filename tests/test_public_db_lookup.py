from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

import requests

QUOTE = "\N{RIGHT SINGLE QUOTATION MARK}"
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

    def test_text_without_a_charset_is_decoded_as_utf8(self) -> None:
        """requests decodes text/* without a charset as ISO-8859-1, which garbles
        UTF-8 text (ENA searchFields serves text/plain with no charset)."""
        real = requests.Response()
        real.status_code = 200
        real._content = f"field\tdescription\nname\tit{QUOTE}s\n".encode()
        real.headers["Content-Type"] = "text/plain"
        # The HTTP adapter sets this the same way when it builds a response.
        real.encoding = requests.utils.get_encoding_from_headers(real.headers)
        session = Mock()
        session.get = Mock(return_value=real)
        with tempfile.TemporaryDirectory() as tmp:
            saved = Path(tmp) / "raw.txt"
            code, envelope = run(
                [
                    "--service",
                    "ena",
                    "--path",
                    "searchFields",
                    "--format",
                    "text",
                    "--save-raw",
                    str(saved),
                ],
                session,
            )
            self.assertEqual(code, 0)
            self.assertIn(f"it{QUOTE}s", envelope["text_head"])
            self.assertIn(f"it{QUOTE}s", saved.read_text(encoding="utf-8"))

    def test_esearch_reports_the_hit_count_not_the_idlist_length(self) -> None:
        body = {
            "esearchresult": {
                "count": "11018",
                "retmax": "20",
                "idlist": [str(i) for i in range(20)],
            }
        }
        session = Mock()
        session.get = Mock(return_value=response(200, body))
        code, envelope = run(
            ["--service", "ncbi-entrez", "--path", "esearch.fcgi", "--max-items", "5"],
            session,
        )
        self.assertEqual(code, 0)
        self.assertEqual(envelope["record_path"], "esearchresult.idlist")
        self.assertEqual(envelope["record_count_returned"], 5)
        self.assertEqual(envelope["record_count_available"], 11018)
        self.assertTrue(envelope["truncated"])

    def test_mgnify_uses_api_v2_and_its_items_key(self) -> None:
        """MGnify API v1 is deprecated; v2 list responses put records under `items`."""
        session = Mock()
        session.get = Mock(
            return_value=response(
                200, {"count": 644, "items": [{"accession": "MGYS00001031"}]}
            )
        )
        code, envelope = run(["--service", "mgnify", "--path", "studies/"], session)
        self.assertEqual(code, 0)
        self.assertTrue(
            session.get.call_args.args[0].startswith(
                "https://www.ebi.ac.uk/metagenomics/api/v2/"
            )
        )
        self.assertEqual(envelope["record_path"], "items")

    def test_a_list_response_with_a_total_reports_it_as_available(self) -> None:
        """MGnify v2 lists carry the total as `count`; the page holds fewer records."""
        body = {
            "count": 644,
            "items": [{"accession": f"MGYS{i:08d}"} for i in range(25)],
        }
        session = Mock()
        session.get = Mock(return_value=response(200, body))
        code, envelope = run(
            ["--service", "mgnify", "--path", "studies/", "--max-items", "5"], session
        )
        self.assertEqual(code, 0)
        self.assertEqual(envelope["record_count_returned"], 5)
        self.assertEqual(envelope["record_count_available"], 644)
        self.assertTrue(envelope["truncated"])

    def test_a_list_response_without_a_total_reports_the_page_length(self) -> None:
        body = {"results": [{"id": i} for i in range(7)], "count": "not a number"}
        session = Mock()
        session.get = Mock(return_value=response(200, body))
        _code, envelope = run(
            ["--service", "uniprot", "--path", "uniprotkb/search", "--max-items", "3"],
            session,
        )
        self.assertEqual(envelope["record_count_available"], 7)

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




class ContactAddressTests(unittest.TestCase):
    """A contact address is sent only when the user passes --email, and it never
    comes back out in the envelope, the displayed URL or an error."""

    ADDRESS = "you@example.org"

    def ncbi(self, session: Mock, *extra: str, env: dict[str, str] | None = None):
        argv = ["--service", "ncbi-entrez", "--path", "esearch.fcgi", *extra]
        return run(argv, session, env if env is not None else {})

    def test_an_ambient_ncbi_email_is_not_sent(self) -> None:
        session = Mock()
        session.get = Mock(return_value=response(200, []))
        env = {"NCBI_EMAIL": self.ADDRESS, "NCBI_API_KEY": "k", "NCBI_TOOL": "my-tool"}
        _, envelope = self.ncbi(session, env=env)
        sent = dict(session.get.call_args.kwargs["params"])
        self.assertNotIn("email", sent)
        self.assertEqual(sent["api_key"], "k")
        self.assertEqual(sent["tool"], "my-tool")
        self.assertNotIn(self.ADDRESS, json.dumps(envelope))

    def test_the_email_flag_is_sent_and_kept_out_of_the_output(self) -> None:
        session = Mock()
        echo = {"results": [{"echo": f"contact {self.ADDRESS}"}]}
        session.get = Mock(return_value=response(200, echo))
        code, envelope = self.ncbi(session, "--email", self.ADDRESS)
        self.assertEqual(code, 0)
        self.assertIn(("email", self.ADDRESS), session.get.call_args.kwargs["params"])
        self.assertNotIn(self.ADDRESS, json.dumps(envelope))
        self.assertNotIn("email=", envelope["url"])

    def test_http_errors_do_not_echo_the_address(self) -> None:
        session = Mock()
        session.get = Mock(
            return_value=response(400, f"bad request from {self.ADDRESS}")
        )
        code, envelope = self.ncbi(session, "--email", self.ADDRESS)
        self.assertEqual((code, envelope["error"]["code"]), (1, "http_error"))
        self.assertNotIn(self.ADDRESS, json.dumps(envelope))

    def test_network_errors_do_not_echo_the_address(self) -> None:
        session = Mock()
        session.get = Mock(
            side_effect=requests.ConnectionError(f"failed: email={self.ADDRESS}")
        )
        code, envelope = self.ncbi(session, "--email", self.ADDRESS)
        self.assertEqual((code, envelope["error"]["code"]), (1, "network_error"))
        self.assertNotIn(self.ADDRESS, json.dumps(envelope))

    def test_network_errors_do_not_echo_the_url_encoded_address_or_key(self) -> None:
        key = "FAKE/KEY+VALUE"
        url = (
            requests.Request(
                "GET",
                "https://example.org",
                params={"email": self.ADDRESS, "api_key": key},
            )
            .prepare()
            .url
        )
        session = Mock()
        session.get = Mock(side_effect=requests.ConnectionError(f"failed: {url}"))
        code, envelope = self.ncbi(
            session, "--email", self.ADDRESS, env={"NCBI_API_KEY": key}
        )
        self.assertEqual((code, envelope["error"]["code"]), (1, "network_error"))
        shown = json.dumps(envelope)
        for leaked in ("you%40example.org", "FAKE%2FKEY%2BVALUE", "FAKE%2FKEY%2bVALUE"):
            self.assertNotIn(leaked, shown)

    def test_the_address_and_the_key_stay_out_of_a_service_error(self) -> None:
        session = Mock()
        body = {"esearchresult": {"ERROR": f"unknown {self.ADDRESS} and topsecretkey"}}
        session.get = Mock(return_value=response(200, body))
        _, envelope = self.ncbi(
            session, "--email", self.ADDRESS, env={"NCBI_API_KEY": "topsecretkey"}
        )
        self.assertEqual(envelope["error"]["code"], "service_error")
        self.assertNotIn(self.ADDRESS, json.dumps(envelope))
        self.assertNotIn("topsecretkey", json.dumps(envelope))

    def test_the_email_flag_is_for_ncbi_only(self) -> None:
        session = Mock()
        code, envelope = run(
            [
                "--service",
                "uniprot",
                "--path",
                "uniprotkb/P04637",
                "--email",
                self.ADDRESS,
            ],
            session,
        )
        self.assertEqual((code, envelope["error"]["code"]), (2, "invalid_input"))
        session.get.assert_not_called()

    def test_an_address_in_param_or_path_points_to_the_flag(self) -> None:
        session = Mock()
        for argv in (
            ["--param", f"email={self.ADDRESS}"],
            ["--path", f"esearch.fcgi?email={self.ADDRESS}"],
        ):
            with self.subTest(argv=argv):
                full = ["--service", "ncbi-entrez", "--path", "esearch.fcgi", *argv]
                code, envelope = run(full, session)
                self.assertEqual(
                    (code, envelope["error"]["code"]), (2, "invalid_input")
                )
                self.assertIn("--email", envelope["error"]["message"])
        session.get.assert_not_called()


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
                    service="ncbi-entrez",
                    path=path,
                    param=list(param),
                    max_items=5,
                    max_depth=3,
                    format="auto",
                    email=None,
                )
                with self.assertRaisesRegex(ValueError, "through the environment"):
                    public_db_lookup.build_request(args, {})

    def test_ordinary_query_parameters_in_the_path_still_work(self) -> None:
        import argparse

        args = argparse.Namespace(
            service="ncbi-entrez",
            path="esearch.fcgi?db=protein&term=p53",
            param=[],
            max_items=5,
            max_depth=3,
            format="auto",
            email=None,
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
            param=[],
            max_items=5,
            max_depth=3,
            format="auto",
            email=None,
        )
        _, params, _ = public_db_lookup.build_request(args, {})
        self.assertEqual(
            [value for key, value in params if key == "id"],
            ["15718680", "157427902"],
        )


    def test_rate_limit_state_is_shared_across_invocations(self) -> None:
        """One lookup per run means an in-process pacer would only space
        retries while a caller in a loop still hammers the service."""
        import tempfile
        import time

        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            started = time.monotonic()
            for _ in range(3):
                public_db_lookup.pace_across_processes("string", 0.3, state)
            elapsed = time.monotonic() - started
        self.assertGreaterEqual(elapsed, 0.55)

    def test_an_unwritable_state_directory_falls_back_to_a_plain_sleep(self) -> None:
        """With interval 0.0 the function returns before touching the directory,
        so the fallback was never exercised."""
        import time

        started = time.monotonic()
        public_db_lookup.pace_across_processes("string", 0.2, Path("/proc/nonexistent/x"))
        self.assertGreaterEqual(time.monotonic() - started, 0.19)

if __name__ == "__main__":
    unittest.main()
