#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

LOCAL_BASE_URL = "http://127.0.0.1:8002/ocr"
API_KEY_ENV_VARS = ("OCR_API_KEY", "NELLI_API_KEY")
BASE_URL_ENV = "OCR_BASE_URL"


CONNECT_TIMEOUT_SECONDS = 15
SUBPROCESS_SLACK_SECONDS = 0.5


class Deadline:
    """One wall-clock budget for the whole job. `--timeout-seconds` used to bound
    only the polling loop, and only after a request returned, so a hung upload or
    artifact download could block forever."""

    def __init__(self, seconds: float) -> None:
        self.total = seconds
        self.started = time.monotonic()

    def remaining(self) -> float:
        return self.total - (time.monotonic() - self.started)

    def check(self, what: str) -> float:
        left = self.remaining()
        if left <= 0:
            raise TimeoutError(f"OCR job exceeded {self.total:.0f}s before {what}")
        return left


def run(cmd: list[str], *, input_text: str | None = None, timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, input=input_text, capture_output=True, text=True, check=False, timeout=timeout
    )


def run_curl(args: list[str], *, api_key: str, deadline: Deadline, what: str) -> subprocess.CompletedProcess[str]:
    # Keep the API key out of the process argument list.
    config = f'header = "X-API-Key: {api_key}"\n'
    budget = deadline.check(what)
    curl = [
        "curl", "-fsS",
        "--connect-timeout", f"{min(CONNECT_TIMEOUT_SECONDS, budget):.3f}",
        "--max-time", f"{budget:.3f}",
        "-K", "-", *args,
    ]
    try:
        # Small slack so curl's own timeout message surfaces first, but never
        # enough to outlive the budget by a meaningful amount.
        return run(curl, input_text=config, timeout=budget + SUBPROCESS_SLACK_SECONDS)
    except subprocess.TimeoutExpired as error:
        raise TimeoutError(f"curl did not return within {budget:.1f}s while {what}") from error


def is_local_url(url: str) -> bool:
    return (urlparse(url).hostname or "").lower() in {"127.0.0.1", "localhost", "::1"}


def resolve_base_url(explicit: str | None, *, allow_remote: bool) -> str:
    """Return an approved OCR URL without silently uploading a document."""
    candidate = explicit
    env_url = os.getenv(BASE_URL_ENV, "").strip()
    if not candidate and env_url:
        candidate = env_url
    candidate = candidate or LOCAL_BASE_URL
    if not is_local_url(candidate) and not allow_remote:
        raise SystemExit(
            "Refusing to upload the document to a remote OCR service without "
            "--allow-remote. Confirm that external document submission is approved."
        )
    return candidate


def require_api_key(args: argparse.Namespace) -> str:
    for env_var in API_KEY_ENV_VARS:
        key = os.getenv(env_var, "").strip()
        if key:
            return key
    names = " or ".join(API_KEY_ENV_VARS)
    raise SystemExit(f"Missing OCR API key. Set {names} in the environment.")


def curl_json(url: str, *, api_key: str, deadline: Deadline, what: str, method: str = "GET", form_file: Path | None = None) -> dict:
    cmd = ["-X", method]
    if form_file is not None:
        cmd.extend(["-F", f"file=@{form_file}"])
    cmd.append(url)
    result = run_curl(cmd, api_key=api_key, deadline=deadline, what=what)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"curl failed for {url}")
    return json.loads(result.stdout)


def curl_download(url: str, *, api_key: str, output_path: Path, deadline: Deadline, what: str) -> None:
    result = run_curl(["-o", str(output_path), url], api_key=api_key, deadline=deadline, what=what)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"curl failed for {url}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Submit a PDF to the OCR API service, poll the async job, and download Markdown/JSON artifacts."
    )
    parser.add_argument("input_path", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--base-url",
        default=None,
        help="OCR API base URL. Uses OCR_BASE_URL or the local service by default.",
    )
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help="Allow upload to a non-local OCR URL after external submission is approved.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    parser.add_argument("--poll-interval-seconds", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = args.input_path.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    api_key = require_api_key(args)
    base_url = resolve_base_url(args.base_url, allow_remote=args.allow_remote).rstrip("/")
    output_dir.mkdir(parents=True, exist_ok=True)

    # The budget starts before the upload and covers polling and every download.
    deadline = Deadline(args.timeout_seconds)

    create_payload = curl_json(
        f"{base_url}/api/jobs",
        api_key=api_key,
        deadline=deadline,
        what="uploading the document",
        method="POST",
        form_file=input_path,
    )

    job_id = create_payload["job_id"]
    status_url = f"{base_url}/api/jobs/{job_id}"
    result_url = f"{base_url}/api/jobs/{job_id}/result"

    while True:
        status_payload = curl_json(status_url, api_key=api_key, deadline=deadline, what=f"polling job {job_id}")
        status = status_payload["status"]
        if status == "succeeded":
            break
        if status == "failed":
            raise RuntimeError(f"OCR API job {job_id} failed: {status_payload.get('error')}")
        deadline.check(f"job {job_id} completed")
        time.sleep(max(0.0, min(args.poll_interval_seconds, deadline.remaining())))

    result_payload = curl_json(result_url, api_key=api_key, deadline=deadline, what=f"fetching the result of job {job_id}")
    stem = input_path.stem
    markdown_path = output_dir / f"{stem}.md"
    ocr_json_path = output_dir / f"{stem}.ocr.json"
    job_meta_path = output_dir / f"{stem}.job.json"

    curl_download(f"{base_url}/api/jobs/{job_id}/artifacts/markdown", api_key=api_key, output_path=markdown_path,
                  deadline=deadline, what="downloading the Markdown artifact")
    curl_download(f"{base_url}/api/jobs/{job_id}/artifacts/json", api_key=api_key, output_path=ocr_json_path,
                  deadline=deadline, what="downloading the JSON artifact")
    deadline.check("reporting success")
    job_meta_path.write_text(
        json.dumps(
            {
                "job_create": create_payload,
                "job_status": status_payload,
                "job_result": result_payload,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"job={job_meta_path}")
    print(f"markdown={markdown_path}")
    print(f"json={ocr_json_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
