#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests==2.34.2"]
# ///
"""Query Crossref and audit DOI records with explicit failure classes."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests


CROSSREF_API_BASE = "https://api.crossref.org"
DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$", re.IGNORECASE)
DOI_IN_TEXT = re.compile(
    r"(?:doi:\s*|https?://(?:dx\.)?doi\.org/)?(10\.\d{4,9}/[^\s\"']+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class LookupResult:
    status: str
    doi: str | None
    metadata: dict[str, Any] | None = None
    detail: str = ""


def normalize_doi(raw_doi: str) -> str | None:
    doi = raw_doi.strip()
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.IGNORECASE)
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    previous = ""
    while doi != previous:
        previous = doi
        doi = doi.rstrip(".,;:")
        while doi.endswith(("}", "]")):
            doi = doi[:-1]
        while doi.endswith(")") and doi.count(")") > doi.count("("):
            doi = doi[:-1]
    return doi if DOI_PATTERN.fullmatch(doi) else None


class CrossrefClient:
    def __init__(self, email: str | None = None, timeout: float = 15.0) -> None:
        suffix = f" (mailto:{email})" if email else ""
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": f"omics-skills-crossref/1.5{suffix}"})
        self.timeout = timeout
        self._last_request = 0.0

    def _pace(self) -> None:
        remaining = 0.05 - (time.monotonic() - self._last_request)
        if remaining > 0:
            time.sleep(remaining)
        self._last_request = time.monotonic()

    def fetch_doi(self, raw_doi: str) -> LookupResult:
        doi = normalize_doi(raw_doi)
        if doi is None:
            return LookupResult("invalid", None, detail="invalid DOI format")
        self._pace()
        try:
            response = self.session.get(
                f"{CROSSREF_API_BASE}/works/{quote(doi, safe='')}",
                timeout=self.timeout,
            )
        except requests.RequestException as error:
            return LookupResult("transient_error", doi, detail=f"request failed: {error}")
        if response.status_code == 404:
            return LookupResult("not_found", doi, detail="DOI not found in Crossref")
        if response.status_code == 429 or 500 <= response.status_code < 600:
            return LookupResult(
                "transient_error",
                doi,
                detail=f"Crossref returned HTTP {response.status_code}",
            )
        if response.status_code != 200:
            return LookupResult("http_error", doi, detail=f"Crossref returned HTTP {response.status_code}")
        try:
            payload = response.json()
        except requests.JSONDecodeError as error:
            return LookupResult("transient_error", doi, detail=f"invalid JSON response: {error}")
        if payload.get("status") != "ok" or not isinstance(payload.get("message"), dict):
            return LookupResult("transient_error", doi, detail="unexpected Crossref response")
        return LookupResult("valid", doi, metadata=payload["message"])

    def search_title(self, title: str, rows: int = 5) -> list[dict[str, Any]]:
        self._pace()
        response = self.session.get(
            f"{CROSSREF_API_BASE}/works",
            params={"query.title": title, "rows": rows},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("message", {}).get("items", []) if payload.get("status") == "ok" else []


def first(value: object) -> str:
    return str(value[0]) if isinstance(value, list) and value else str(value or "")


def year(metadata: dict[str, Any]) -> str:
    for key in ("published-print", "published-online", "issued"):
        parts = metadata.get(key, {}).get("date-parts", [[]])
        if parts and parts[0]:
            return str(parts[0][0])
    return "n.d."


def format_record(result: LookupResult) -> dict[str, object]:
    metadata = result.metadata or {}
    return {
        "status": result.status,
        "doi": result.doi,
        "detail": result.detail,
        "title": first(metadata.get("title")),
        "journal": first(metadata.get("container-title")),
        "year": year(metadata) if metadata else "",
    }


def extract_dois(text: str) -> list[str]:
    normalized = {normalize_doi(match) for match in DOI_IN_TEXT.findall(text)}
    return sorted(doi for doi in normalized if doi)


def exit_code(results: list[LookupResult], strict: bool, missing_dois: int = 0) -> int:
    if any(result.status == "transient_error" for result in results):
        return 2
    if strict and (missing_dois or any(result.status != "valid" for result in results)):
        return 1
    if len(results) == 1 and results[0].status != "valid":
        return 1
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--doi")
    modes.add_argument("--title")
    modes.add_argument("--validate-file", type=Path)
    modes.add_argument("--audit-bibliography", type=Path)
    parser.add_argument("--email")
    parser.add_argument("--rows", type=int, default=5)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    client = CrossrefClient(args.email)
    results: list[LookupResult] = []
    missing_dois = 0
    payload: dict[str, object]
    try:
        if args.doi:
            results = [client.fetch_doi(args.doi)]
            payload = format_record(results[0])
        elif args.title:
            items = client.search_title(args.title, args.rows)
            payload = {
                "query": args.title,
                "candidates": [
                    {
                        "doi": item.get("DOI"),
                        "title": first(item.get("title")),
                        "journal": first(item.get("container-title")),
                        "year": year(item),
                    }
                    for item in items
                ],
            }
        else:
            path = args.validate_file or args.audit_bibliography
            assert path is not None
            text = path.expanduser().resolve().read_text(encoding="utf-8")
            if args.validate_file:
                dois = [line.strip() for line in text.splitlines() if line.strip()]
            else:
                dois = extract_dois(text)
                titles = re.findall(r'title\s*=\s*["{]([^"}]+)', text, re.IGNORECASE)
                missing_dois = max(len(titles) - len(dois), 0)
            results = [client.fetch_doi(doi) for doi in dois]
            payload = {
                "records": [format_record(result) for result in results],
                "counts": {
                    status: sum(result.status == status for result in results)
                    for status in ("valid", "invalid", "not_found", "transient_error", "http_error")
                },
                "potentially_missing_dois": missing_dois,
            }
    except (OSError, requests.RequestException, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        if args.output.exists():
            print(f"ERROR: refusing to overwrite {args.output}", file=sys.stderr)
            return 1
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return exit_code(results, args.strict, missing_dois)


if __name__ == "__main__":
    raise SystemExit(main())
