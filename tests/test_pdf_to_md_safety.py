from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
OCR_SCRIPT = REPO_ROOT / "skills" / "pdf-to-md" / "scripts" / "ocr_api_job.py"
LITEPARSE_SCRIPT = REPO_ROOT / "skills" / "pdf-to-md" / "scripts" / "liteparse_to_md.py"

SPEC = importlib.util.spec_from_file_location("ocr_api_job", OCR_SCRIPT)
ocr_api_job = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ocr_api_job)


class PdfToMarkdownSafetyTests(unittest.TestCase):
    def test_remote_ocr_requires_explicit_opt_in(self) -> None:
        with self.assertRaises(SystemExit):
            ocr_api_job.resolve_base_url(
                "https://api.example.org/ocr",
                allow_remote=False,
            )
        self.assertEqual(
            ocr_api_job.resolve_base_url(
                "https://api.example.org/ocr",
                allow_remote=True,
            ),
            "https://api.example.org/ocr",
        )

    def test_local_ocr_needs_no_remote_opt_in(self) -> None:
        self.assertEqual(
            ocr_api_job.resolve_base_url(None, allow_remote=False),
            ocr_api_job.LOCAL_BASE_URL,
        )

    def test_secret_values_are_not_cli_options(self) -> None:
        result = subprocess.run(
            [sys.executable, str(OCR_SCRIPT), "--help"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--allow-remote", result.stdout)
        self.assertNotIn("--api-key", result.stdout)

        liteparse_source = LITEPARSE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn('"--password-env"', liteparse_source)
        self.assertNotIn('"--password"', liteparse_source)




class OcrDeadlineTests(unittest.TestCase):
    """--timeout-seconds used to bound only the polling loop, and only after a
    request returned, so a hung upload or artifact download blocked forever."""

    def test_deadline_expires_and_names_the_step(self) -> None:
        deadline = ocr_api_job.Deadline(30)
        self.assertAlmostEqual(deadline.check("uploading"), 30, delta=1)
        deadline.started -= 60
        with self.assertRaisesRegex(TimeoutError, "before downloading"):
            deadline.check("downloading")

    def test_curl_limits_track_the_remaining_budget(self) -> None:
        """Integer truncation capped a 1.9s budget at 1s and rounded 0.6s up to
        1s, and the subprocess slack let a call outlive the whole deadline."""
        captured: dict[str, object] = {}

        def fake_run(cmd, *, input_text=None, timeout=None):
            captured["cmd"], captured["timeout"] = cmd, timeout
            return SimpleNamespace(returncode=0, stdout="{}", stderr="")

        for budget in (1.9, 0.6):
            with mock.patch.object(ocr_api_job, "run", fake_run):
                ocr_api_job.run_curl(
                    ["u"], api_key="SYNTHETIC", deadline=ocr_api_job.Deadline(budget), what="t"
                )
            cmd = captured["cmd"]
            max_time = float(cmd[cmd.index("--max-time") + 1])
            self.assertAlmostEqual(max_time, budget, delta=0.05)
            self.assertLessEqual(
                captured["timeout"], budget + ocr_api_job.SUBPROCESS_SLACK_SECONDS + 0.05
            )

    def test_every_curl_call_carries_connect_and_max_time(self) -> None:
        captured: dict[str, list[str]] = {}

        def fake_run(cmd, *, input_text=None, timeout=None):
            captured["cmd"] = cmd
            captured["timeout"] = timeout
            return SimpleNamespace(returncode=0, stdout="{}", stderr="")

        with mock.patch.object(ocr_api_job, "run", fake_run):
            ocr_api_job.run_curl(
                ["https://example.invalid/api/jobs"],
                api_key="SYNTHETIC",
                deadline=ocr_api_job.Deadline(60),
                what="uploading",
            )
        self.assertIn("--connect-timeout", captured["cmd"])
        self.assertIn("--max-time", captured["cmd"])
        self.assertIsNotNone(captured["timeout"])

    def test_an_expired_budget_refuses_to_start_another_request(self) -> None:
        deadline = ocr_api_job.Deadline(30)
        deadline.started -= 60
        with mock.patch.object(ocr_api_job, "run", lambda *a, **k: self.fail("must not run curl")):
            with self.assertRaises(TimeoutError):
                ocr_api_job.run_curl(["u"], api_key="SYNTHETIC", deadline=deadline, what="polling")

if __name__ == "__main__":
    unittest.main()
