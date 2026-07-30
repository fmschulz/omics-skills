#!/usr/bin/env python3
"""Validate DOI registration and title metadata for tracked skill Markdown."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CACHE = ROOT / "catalog" / "citation-cache.json"
DOI_PATTERN = re.compile(r"10\.\d{4,9}/[^\s<>\"'`]+", re.IGNORECASE)
FRONTMATTER_DOI = re.compile(r"^\s*doi:\s*[\"']?([^\"'#\s]+)", re.IGNORECASE | re.MULTILINE)
FRONTMATTER_TITLE = re.compile(
    r"^\s*title:\s*(?:[\"'](.*?)[\"']|([^#\n]+))\s*$",
    re.IGNORECASE | re.MULTILINE,
)
TITLE_TOKEN = re.compile(r"[a-z0-9]+")
TITLE_CHECK_SKIP_PREFIXES = ("10.48550/", "10.5281/")


@dataclass(frozen=True)
class Citation:
    doi: str
    path: Path
    line: int
    title: str | None = None


def normalize_doi(raw: str) -> str | None:
    doi = raw.strip()
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
    return doi.lower() if re.fullmatch(r"10\.\d{4,9}/\S+", doi, re.IGNORECASE) else None


def frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end >= 0 else ""


def tracked_markdown(repo_root: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "skills"],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return sorted((repo_root / "skills").rglob("*.md"))
    return sorted(
        repo_root / raw.decode()
        for raw in result.stdout.split(b"\0")
        if raw and raw.decode().endswith(".md") and (repo_root / raw.decode()).is_file()
    )


def collect_citations(paths: list[Path]) -> list[Citation]:
    citations: list[Citation] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        header = frontmatter(text)
        title_match = FRONTMATTER_TITLE.search(header)
        title = None
        if title_match:
            title = (title_match.group(1) or title_match.group(2) or "").strip()
        for match in FRONTMATTER_DOI.finditer(header):
            doi = normalize_doi(match.group(1))
            if doi:
                citations.append(Citation(doi, path, text[: match.start()].count("\n") + 2, title))
        if path.name != "SKILL.md":
            continue
        header_dois = {citation.doi for citation in citations if citation.path == path}
        for match in DOI_PATTERN.finditer(text):
            doi = normalize_doi(match.group(0))
            if doi and doi not in header_dois:
                citations.append(Citation(doi, path, text[: match.start()].count("\n") + 1))
    return citations


def title_overlap(left: str, right: str) -> float:
    left_tokens = set(TITLE_TOKEN.findall(left.lower()))
    right_tokens = set(TITLE_TOKEN.findall(right.lower()))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(len(left_tokens), len(right_tokens))


def fetch_json(url: str, timeout: float) -> dict[str, object]:
    request = Request(url, headers={"User-Agent": "omics-skills-citation-validator/1.0"})
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise HTTPError(url, response.status, response.reason, response.headers, None)
        return json.load(response)


def refresh_cache(
    citations: list[Citation], cache_path: Path, timeout: float
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    transient: list[str] = []
    records: dict[str, dict[str, object]] = {}
    by_doi: dict[str, list[Citation]] = {}
    for citation in citations:
        by_doi.setdefault(citation.doi, []).append(citation)

    for doi, sources in sorted(by_doi.items()):
        try:
            handle_url = f"https://doi.org/api/handles/{quote(doi, safe='/')}"
            handle = fetch_json(handle_url, timeout)
            if handle.get("responseCode") != 1:
                errors.append(f"{doi}: DOI handle responseCode={handle.get('responseCode')}")
                continue

            cached_title = None
            declared_title = next((source.title for source in sources if source.title), None)
            if declared_title and not doi.startswith(TITLE_CHECK_SKIP_PREFIXES):
                crossref_url = f"https://api.crossref.org/works/{quote(doi, safe='')}"
                payload = fetch_json(crossref_url, timeout)
                message = payload.get("message")
                titles = message.get("title", []) if isinstance(message, dict) else []
                cached_title = str(titles[0]) if isinstance(titles, list) and titles else None
                if not cached_title:
                    errors.append(f"{doi}: Crossref returned no title")
                    continue
            records[doi] = {"registered": True, "title": cached_title}
        except HTTPError as error:
            if error.code == 404:
                errors.append(f"{doi}: HTTP 404")
            else:
                transient.append(f"{doi}: HTTP {error.code}")
        except (URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
            transient.append(f"{doi}: {error}")

    if not errors and not transient:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = cache_path.with_suffix(cache_path.suffix + ".tmp")
        temporary.write_text(
            json.dumps({"version": 1, "records": records}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(cache_path)
    return errors, transient


def validate_cache(citations: list[Citation], cache_path: Path) -> list[str]:
    if not cache_path.exists():
        return [f"citation cache missing: {cache_path}; run with --refresh"]
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"citation cache unreadable: {error}"]
    records = payload.get("records", {})
    if payload.get("version") != 1 or not isinstance(records, dict):
        return ["citation cache has an unsupported schema"]

    errors: list[str] = []
    for citation in citations:
        location = f"{citation.path}:{citation.line}"
        record = records.get(citation.doi)
        if not isinstance(record, dict) or record.get("registered") is not True:
            errors.append(
                f"{location}: {citation.doi} is not in the validated cache; run with --refresh"
            )
            continue
        if citation.title and not citation.doi.startswith(TITLE_CHECK_SKIP_PREFIXES):
            registered_title = record.get("title")
            if not isinstance(registered_title, str):
                errors.append(f"{location}: {citation.doi} has no cached Crossref title")
            elif title_overlap(citation.title, registered_title) < 0.6:
                errors.append(
                    f"{location}: title does not match Crossref for {citation.doi} "
                    f"({citation.title!r} vs {registered_title!r})"
                )
    return errors


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--timeout", type=float, default=20.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    citations = collect_citations(tracked_markdown(args.repo_root))
    if args.refresh:
        errors, transient = refresh_cache(citations, args.cache, args.timeout)
        for error in errors + transient:
            print(f"- {error}", file=sys.stderr)
        if transient:
            return 2
        if errors:
            return 1
    errors = validate_cache(citations, args.cache)
    if errors:
        print("Citation validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Citation validation passed ({len({item.doi for item in citations})} DOIs).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
