#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests==2.34.2"]
# ///
"""GET one endpoint of a public life-science database and print a compact JSON envelope."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests


BASE_URLS = {
    "uniprot": "https://rest.uniprot.org",
    "ncbi-entrez": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
    "ncbi-datasets": "https://api.ncbi.nlm.nih.gov/datasets/v2",
    "mgnify": "https://www.ebi.ac.uk/metagenomics/api/v1",
    "interpro": "https://www.ebi.ac.uk/interpro/api",
    "alphafold": "https://alphafold.ebi.ac.uk/api",
    "string": "https://string-db.org/api",
    "ena": "https://www.ebi.ac.uk/ena/portal/api",
}
NCBI_SERVICES = {"ncbi-entrez", "ncbi-datasets"}
NCBI_ENV_PARAMS = (("api_key", "NCBI_API_KEY"), ("email", "NCBI_EMAIL"), ("tool", "NCBI_TOOL"))
RECORD_KEYS = ("results", "data", "collection", "records", "items", "hits", "reports", "esearchresult.idlist")
USER_AGENT = "omics-skills-public-db-lookup (+https://github.com/fmschulz/omics-skills)"
MAX_STRING = 240
TEXT_HEAD = 800
RETRY_SLEEPS = (1, 2, 4)
EXIT_CODES = {"invalid_input": 2}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service", required=True, choices=sorted(BASE_URLS))
    parser.add_argument("--path", required=True, help="endpoint path relative to the service base URL, or a full URL under that base")
    parser.add_argument("--param", action="append", default=[], metavar="KEY=VALUE")
    parser.add_argument("--record-path", help="dotted path to the list of records (inferred when omitted)")
    parser.add_argument("--max-items", type=int, default=5)
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--format", choices=("auto", "json", "text"), default="auto")
    parser.add_argument("--save-raw", type=Path, help="write the full response body to this path")
    parser.add_argument("--timeout", type=float, default=30)
    return parser.parse_args(argv)


def build_request(args: argparse.Namespace, env: dict[str, str]) -> tuple[str, dict[str, str], dict[str, str]]:
    """Return (url, params, headers); raise ValueError on invalid input."""
    if args.max_items < 1 or args.max_depth < 1:
        raise ValueError("--max-items and --max-depth must be at least 1")
    base = BASE_URLS[args.service]
    if "://" in args.path:
        if not args.path.startswith(base + "/"):
            raise ValueError(f"full URLs must start with {base}/")
        url = args.path
    else:
        url = f"{base}/{args.path.lstrip('/')}"
    params: dict[str, str] = {}
    for item in args.param:
        key, sep, value = item.partition("=")
        if not sep or not key:
            raise ValueError(f"--param expects KEY=VALUE, got {item!r}")
        if key in ("api_key", "api-key"):
            raise ValueError("pass the NCBI key through NCBI_API_KEY, not --param")
        params[key] = value
    if args.service in NCBI_SERVICES:
        for key, env_name in NCBI_ENV_PARAMS:
            if env.get(env_name) and key not in params:
                params[key] = env[env_name]
    headers = {"User-Agent": USER_AGENT}
    if args.format != "text":
        headers["Accept"] = "application/json"
    return url, params, headers


def retry_delay(retry_after: str | None, attempt: int) -> float:
    try:
        return max(float(retry_after), 0.0)
    except (TypeError, ValueError):
        return RETRY_SLEEPS[attempt]


def fetch(session: Any, url: str, params: dict[str, str], headers: dict[str, str], timeout: float) -> Any:
    """GET with up to three retries on 429 and 5xx; return the last response."""
    for attempt in range(len(RETRY_SLEEPS) + 1):
        response = session.get(url, params=params, headers=headers, timeout=timeout)
        if response.status_code != 429 and response.status_code < 500:
            return response
        if attempt < len(RETRY_SLEEPS):
            time.sleep(retry_delay(response.headers.get("Retry-After"), attempt))
    return response


def compact(value: Any, max_items: int, max_depth: int, depth: int = 0) -> Any:
    if isinstance(value, str):
        return value if len(value) <= MAX_STRING else value[:MAX_STRING] + "..."
    if isinstance(value, dict):
        if depth >= max_depth:
            return "..."
        keys = list(value)
        out = {key: compact(value[key], max_items, max_depth, depth + 1) for key in keys[:max_items]}
        if len(keys) > max_items:
            out["_truncated_keys"] = len(keys) - max_items
        return out
    if isinstance(value, list):
        if depth >= max_depth:
            return "..."
        out = [compact(item, max_items, max_depth, depth + 1) for item in value[:max_items]]
        if len(value) > max_items:
            out.append(f"... (+{len(value) - max_items} more)")
        return out
    return value


def get_path(payload: Any, path: str) -> Any:
    for key in path.split("."):
        if not isinstance(payload, dict) or key not in payload:
            return None
        payload = payload[key]
    return payload


def find_records(payload: Any, record_path: str | None) -> tuple[str | None, list[Any] | None, list[str]]:
    if record_path:
        records = get_path(payload, record_path)
        if isinstance(records, list):
            return record_path, records, []
        return None, None, [f"--record-path {record_path!r} did not resolve to a list; returning summary"]
    if isinstance(payload, list):
        return None, payload, []
    for key in RECORD_KEYS:
        records = get_path(payload, key)
        if isinstance(records, list):
            return key, records, []
    return None, None, []


def redact(text: str, secret: str | None) -> str:
    return text.replace(secret, "REDACTED") if secret else text


def emit(payload: dict[str, Any]) -> int:
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if payload["ok"]:
        return 0
    return EXIT_CODES.get(payload["error"]["code"], 1)


def fail(source: str, code: str, message: str) -> int:
    return emit({"ok": False, "source": source, "error": {"code": code, "message": message}})


def main(argv: list[str] | None = None, session: Any = None, env: dict[str, str] | None = None) -> int:
    args = parse_args(argv)
    env = os.environ if env is None else env
    try:
        url, params, headers = build_request(args, env)
    except ValueError as error:
        return fail(args.service, "invalid_input", str(error))
    secret = params.get("api_key")
    shown = {key: value for key, value in params.items() if key != "api_key"}
    display_url = str(requests.Request("GET", url, params=shown).prepare().url)

    try:
        response = fetch(session or requests.Session(), url, params, headers, args.timeout)
    except requests.RequestException as error:
        return fail(args.service, "network_error", redact(str(error), secret))
    text = response.text
    if not 200 <= response.status_code < 300:
        head = redact(text[:200], secret)
        return fail(args.service, "http_error", f"HTTP {response.status_code} from {display_url}: {head}")

    raw_output_path = None
    if args.save_raw:
        try:
            args.save_raw.write_text(text, encoding="utf-8")
        except OSError as error:
            return fail(args.service, "invalid_input", f"cannot write --save-raw: {error}")
        raw_output_path = str(args.save_raw)

    result: dict[str, Any] = {
        "ok": True,
        "source": args.service,
        "url": display_url,
        "status_code": response.status_code,
    }
    content_type = str({k.lower(): v for k, v in response.headers.items()}.get("content-type", ""))
    looks_json = "json" in content_type.lower() or text.lstrip()[:1] in ("{", "[")
    if args.format == "text" or (args.format == "auto" and not looks_json):
        result["text_head"] = text[:TEXT_HEAD]
        result["text_head_truncated"] = len(text) > TEXT_HEAD
        result["warnings"] = []
    else:
        try:
            payload = json.loads(text)
        except ValueError as error:
            return fail(args.service, "invalid_response", f"response is not valid JSON: {error}")
        record_path, records, warnings = find_records(payload, args.record_path)
        if records is not None:
            result["record_path"] = record_path
            result["record_count_returned"] = min(len(records), args.max_items)
            result["record_count_available"] = len(records)
            result["truncated"] = len(records) > args.max_items
            result["records"] = [compact(item, args.max_items, args.max_depth) for item in records[: args.max_items]]
        else:
            result["summary"] = compact(payload, args.max_items, args.max_depth)
            result["top_keys"] = list(payload)[:50] if isinstance(payload, dict) else []
        result["warnings"] = warnings
    result["raw_output_path"] = raw_output_path
    return emit(result)


if __name__ == "__main__":
    sys.exit(main())
