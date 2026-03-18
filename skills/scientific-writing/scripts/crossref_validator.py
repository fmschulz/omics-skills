#!/usr/bin/env python3
"""
Validate and enrich scientific references with the Crossref REST API.

Examples:
    python scripts/crossref_validator.py --doi "10.1038/nature12373"
    python scripts/crossref_validator.py --title "CRISPR-Cas9 genome editing"
    python scripts/crossref_validator.py --validate-file references.txt
    python scripts/crossref_validator.py --audit-bibliography refs.bib
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    print("Error: requests is required. Install it with `pip install requests`.", file=sys.stderr)
    raise SystemExit(1)


CROSSREF_API_BASE = "https://api.crossref.org"
RATE_LIMIT_DELAY_SECONDS = 0.05
DOI_PATTERN = re.compile(r"^10\.\d{4,}/\S+$")


class CrossrefClient:
    def __init__(self, user_agent: str) -> None:
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": user_agent})
        self._last_request = 0.0

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_request
        if elapsed < RATE_LIMIT_DELAY_SECONDS:
            time.sleep(RATE_LIMIT_DELAY_SECONDS - elapsed)
        self._last_request = time.time()

    def fetch_doi(self, raw_doi: str) -> tuple[bool, dict[str, Any] | None]:
        doi = normalize_doi(raw_doi)
        if doi is None:
            return False, {"error": "invalid DOI format"}

        self._rate_limit()
        try:
            response = self._session.get(f"{CROSSREF_API_BASE}/works/{doi}", timeout=10)
        except requests.RequestException as exc:
            return False, {"error": f"request failed: {exc}"}

        if response.status_code == 404:
            return False, {"error": "DOI not found in Crossref"}
        if response.status_code != 200:
            return False, {"error": f"HTTP {response.status_code}"}

        payload = response.json()
        if payload.get("status") != "ok":
            return False, {"error": "unexpected Crossref response"}
        return True, payload.get("message", {})

    def search_title(self, title: str, max_results: int = 5) -> list[dict[str, Any]]:
        self._rate_limit()
        try:
            response = self._session.get(
                f"{CROSSREF_API_BASE}/works",
                params={"query.title": title, "rows": max_results},
                timeout=10,
            )
        except requests.RequestException as exc:
            print(f"Error searching title: {exc}", file=sys.stderr)
            return []

        if response.status_code != 200:
            print(f"Error searching title: HTTP {response.status_code}", file=sys.stderr)
            return []

        payload = response.json()
        if payload.get("status") != "ok":
            return []
        return payload.get("message", {}).get("items", [])


def normalize_doi(raw_doi: str) -> str | None:
    doi = raw_doi.strip()
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.IGNORECASE)
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    if DOI_PATTERN.match(doi):
        return doi
    return None


def extract_year(metadata: dict[str, Any]) -> str:
    for field in ("published-print", "published-online", "issued"):
        date_parts = metadata.get(field, {}).get("date-parts", [[]])
        if date_parts and date_parts[0]:
            return str(date_parts[0][0])
    return "n.d."


def format_authors(authors: list[dict[str, Any]], style: str) -> str:
    if not authors:
        return "Unknown"

    formatted: list[str] = []
    for author in authors[:6]:
        family = author.get("family", "").strip()
        given = author.get("given", "").strip()
        initials = "".join(part[0] for part in given.split() if part)
        spaced_initials = " ".join(f"{part[0]}." for part in given.split() if part)

        if style in {"apa", "chicago"}:
            name = f"{family}, {spaced_initials}".strip().rstrip(",")
        else:
            name = f"{family} {initials}".strip()
        formatted.append(name)

    if len(authors) > 6:
        formatted.append("et al.")
    elif len(formatted) > 1 and style in {"apa", "chicago"}:
        formatted[-1] = f"& {formatted[-1]}"
    elif len(formatted) > 1 and style == "ieee":
        formatted[-1] = f"and {formatted[-1]}"

    return ", ".join(formatted)


def format_citation(metadata: dict[str, Any], style: str) -> str:
    authors = format_authors(metadata.get("author", []), style)
    title = first_string(metadata.get("title"))
    journal = first_string(metadata.get("container-title"))
    year = extract_year(metadata)
    volume = metadata.get("volume", "")
    issue = metadata.get("issue", "")
    pages = metadata.get("page", "")
    doi = metadata.get("DOI", "")

    if style == "apa":
        citation = f"{authors} ({year}). {title}. {journal}"
        if volume:
            citation += f", {volume}"
        if issue:
            citation += f"({issue})"
        if pages:
            citation += f", {pages}"
        if doi:
            citation += f". https://doi.org/{doi}"
        return citation

    if style in {"ama", "vancouver"}:
        citation = f"{authors} {title}. {journal}. {year}"
        if volume:
            citation += f";{volume}"
        if issue:
            citation += f"({issue})"
        if pages:
            citation += f":{pages}"
        if doi:
            citation += f". doi:{doi}"
        return citation

    if style == "ieee":
        citation = f'{authors}, "{title}," {journal}'
        if volume:
            citation += f", vol. {volume}"
        if issue:
            citation += f", no. {issue}"
        if pages:
            citation += f", pp. {pages}"
        if year:
            citation += f", {year}"
        if doi:
            citation += f". doi: {doi}"
        return citation

    citation = f'{authors} {year}. "{title}." {journal}'
    if volume:
        citation += f" {volume}"
    if issue:
        citation += f"({issue})"
    if pages:
        citation += f": {pages}"
    if doi:
        citation += f". https://doi.org/{doi}"
    return citation


def first_string(value: Any) -> str:
    if isinstance(value, list):
        return str(value[0]) if value else ""
    if value is None:
        return ""
    return str(value)


def validate_file(client: CrossrefClient, path: Path) -> dict[str, list[Any]]:
    results: dict[str, list[Any]] = {"valid": [], "invalid": [], "errors": []}
    for line in path.read_text().splitlines():
        raw = line.strip()
        if not raw:
            continue
        is_valid, metadata = client.fetch_doi(raw)
        if is_valid:
            results["valid"].append({"doi": raw, "metadata": metadata})
        elif metadata and metadata.get("error") == "invalid DOI format":
            results["invalid"].append(raw)
        else:
            results["errors"].append({"doi": raw, "error": metadata.get("error") if metadata else "unknown"})
    return results


def audit_bibliography(client: CrossrefClient, path: Path) -> dict[str, Any]:
    content = path.read_text()
    doi_matches = set(
        re.findall(r"(?:doi:|https?://(?:dx\.)?doi\.org/)?(10\.\d{4,}/\S+)", content, flags=re.IGNORECASE)
    )
    title_matches = re.findall(r'title\s*=\s*["{]([^"}]+)["}]', content, flags=re.IGNORECASE)

    valid: list[dict[str, str]] = []
    invalid: list[str] = []
    for doi in sorted(doi_matches):
        is_valid, metadata = client.fetch_doi(doi)
        if is_valid and metadata:
            valid.append({"doi": doi, "title": first_string(metadata.get("title"))})
        else:
            invalid.append(doi)

    return {
        "total_dois": len(doi_matches),
        "valid_dois": len(valid),
        "invalid_dois": len(invalid),
        "valid_list": valid,
        "invalid_list": invalid,
        "total_titles": len(title_matches),
        "missing_dois": max(len(title_matches) - len(doi_matches), 0),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate DOIs and retrieve citation metadata with Crossref")
    parser.add_argument("--doi", help="Validate a single DOI")
    parser.add_argument("--title", help="Search works by title")
    parser.add_argument("--validate-file", help="Validate DOIs from a file, one per line")
    parser.add_argument("--audit-bibliography", help="Audit a bibliography file for DOI coverage")
    parser.add_argument(
        "--style",
        default="apa",
        choices=["apa", "vancouver", "ama", "ieee", "chicago"],
        help="Citation style for formatted output",
    )
    parser.add_argument("--output", help="Write output to a file instead of stdout")
    parser.add_argument(
        "--email",
        default="your-email@example.com",
        help="Email used in the Crossref polite-pool user agent",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    user_agent = f"scientific-writing-skill/1.0 (mailto:{args.email})"
    client = CrossrefClient(user_agent=user_agent)

    output_handle = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout
    try:
        if args.doi:
            is_valid, metadata = client.fetch_doi(args.doi)
            if not is_valid or metadata is None:
                print(f"INVALID DOI: {args.doi}", file=output_handle)
                print(f"Error: {metadata.get('error') if metadata else 'unknown'}", file=output_handle)
                return 1

            print(f"VALID DOI: {normalize_doi(args.doi)}", file=output_handle)
            print(f"Title: {first_string(metadata.get('title'))}", file=output_handle)
            print(f"Journal: {first_string(metadata.get('container-title'))}", file=output_handle)
            print(f"Year: {extract_year(metadata)}", file=output_handle)
            print(f"Citation ({args.style}): {format_citation(metadata, args.style)}", file=output_handle)
            return 0

        if args.title:
            works = client.search_title(args.title)
            if not works:
                print("No matching works found.", file=output_handle)
                return 1

            print(f"Found {len(works)} matching works:", file=output_handle)
            for index, work in enumerate(works, start=1):
                print(f"{index}. {first_string(work.get('title'))}", file=output_handle)
                print(f"   DOI: {work.get('DOI', 'N/A')}", file=output_handle)
                print(f"   Year: {extract_year(work)}", file=output_handle)
                print(f"   Journal: {first_string(work.get('container-title'))}", file=output_handle)
            return 0

        if args.validate_file:
            results = validate_file(client, Path(args.validate_file))
            print(f"Valid DOIs: {len(results['valid'])}", file=output_handle)
            print(f"Invalid DOIs: {len(results['invalid'])}", file=output_handle)
            print(f"Errors: {len(results['errors'])}", file=output_handle)
            if results["invalid"]:
                print("", file=output_handle)
                print("Invalid DOI entries:", file=output_handle)
                for doi in results["invalid"]:
                    print(f"- {doi}", file=output_handle)
            if results["errors"]:
                print("", file=output_handle)
                print("Validation errors:", file=output_handle)
                for error in results["errors"]:
                    print(f"- {error['doi']}: {error['error']}", file=output_handle)
            return 0

        if args.audit_bibliography:
            report = audit_bibliography(client, Path(args.audit_bibliography))
            print("Bibliography audit", file=output_handle)
            print("=================", file=output_handle)
            print(f"Total DOIs found: {report['total_dois']}", file=output_handle)
            print(f"Valid DOIs: {report['valid_dois']}", file=output_handle)
            print(f"Invalid DOIs: {report['invalid_dois']}", file=output_handle)
            print(f"Total titles: {report['total_titles']}", file=output_handle)
            print(f"Potentially missing DOIs: {report['missing_dois']}", file=output_handle)
            if report["invalid_list"]:
                print("", file=output_handle)
                print("Invalid DOIs:", file=output_handle)
                for doi in report["invalid_list"]:
                    print(f"- {doi}", file=output_handle)
            return 0

        parser.print_help(file=output_handle)
        return 0
    finally:
        if args.output:
            output_handle.close()


if __name__ == "__main__":
    raise SystemExit(main())
