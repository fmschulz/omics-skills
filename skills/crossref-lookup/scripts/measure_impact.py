#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DOI_PATTERN = re.compile(r"^10\.\d{4,}/\S+$", re.IGNORECASE)
DEFAULT_CACHE_TTL = 86_400.0
DEFAULT_MIN_INTERVAL = 0.1
MAX_ATTEMPTS = 4
MAX_RETRY_WAIT_S = 60.0
OPENALEX_KEY_ENV = "OPENALEX_API_KEY"


def normalize_doi(raw_doi: str) -> str:
    doi = raw_doi.strip()
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.IGNORECASE)
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    if not DOI_PATTERN.match(doi):
        raise ValueError(f"Invalid DOI: {raw_doi}")
    return doi


def normalize_openalex_id(raw_id: str) -> str:
    candidate = raw_id.strip()
    if candidate.startswith("https://openalex.org/"):
        candidate = candidate.rsplit("/", 1)[-1]
    if not re.fullmatch(r"W\d+", candidate):
        raise ValueError(f"Invalid OpenAlex ID: {raw_id}")
    return candidate


def fetch_json(url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "crossref-lookup-impact/1.0 (+https://github.com/fmschulz/omics-skills)",
            **(headers or {}),
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def retry_wait_s(error: urllib.error.HTTPError, attempt: int) -> float:
    """Return seconds to wait after a 429: Retry-After if usable, else backoff."""
    try:
        wait = float(error.headers.get("Retry-After", ""))
    except (AttributeError, TypeError, ValueError):
        wait = 2.0**attempt
    return min(max(wait, 0.0), MAX_RETRY_WAIT_S)


def try_fetch_json(
    url: str, headers: dict[str, str] | None
) -> tuple[dict[str, Any] | None, urllib.error.HTTPError | None]:
    """Return ``(payload, None)``, or ``(None, error)`` for an HTTP error."""
    try:
        return fetch_json(url, headers), None
    except urllib.error.HTTPError as error:
        return None, error


def fetch_openalex_json(url: str) -> dict[str, Any]:
    """Fetch one OpenAlex URL, retrying HTTP 429 a bounded number of times.

    The optional key (``OPENALEX_API_KEY``, environment only) goes in an
    ``Authorization`` header, so it never appears in a URL, cache key or error.
    """
    key = os.environ.get(OPENALEX_KEY_ENV)
    headers = {"Authorization": f"Bearer {key}"} if key else None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        payload, error = try_fetch_json(url, headers)
        if error is None:
            return payload or {}
        if error.code != 429 or attempt == MAX_ATTEMPTS:
            raise error
        time.sleep(retry_wait_s(error, attempt))
    raise AssertionError("unreachable")  # pragma: no cover


def default_cache_dir() -> Path:
    return Path(
        os.environ.get(
            "OPENALEX_CACHE_DIR", Path.home() / ".cache" / "omics-skills" / "openalex"
        )
    )


def fetch_openalex_cached(
    url: str, *, cache_dir: Path, cache_ttl: float, min_interval: float
) -> dict[str, Any]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = cache_dir / "responses" / f"{hashlib.sha256(url.encode()).hexdigest()}.json"
    try:
        if time.time() - cache.stat().st_mtime <= cache_ttl:
            return json.loads(cache.read_text(encoding="utf-8"))
    except OSError:
        pass
    lock_path = cache_dir / "pacing.lock"
    state_path = cache_dir / "last_request_unix.txt"
    with lock_path.open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            last = float(state_path.read_text().strip())
        except (OSError, ValueError):
            last = None
        if last is not None and min_interval > 0:
            time.sleep(max(0, min_interval - (time.time() - last)))
        payload = fetch_openalex_json(url)
        state_path.write_text(f"{time.time():.6f}\n")
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    return payload


def openalex_url_from_args(
    doi: str | None, openalex_id: str | None, mailto: str | None
) -> str:
    base = "https://api.openalex.org/works"
    if doi:
        target = f"https://doi.org/{doi}"
        path = urllib.parse.quote(target, safe=":/")
    else:
        path = normalize_openalex_id(openalex_id or "")
    url = f"{base}/{path}"
    if mailto:
        url = f"{url}?{urllib.parse.urlencode({'mailto': mailto})}"
    return url


def fetch_openalex_work(
    doi: str | None,
    openalex_id: str | None,
    mailto: str | None,
    *,
    cache_dir: Path | None = None,
    cache_ttl: float = DEFAULT_CACHE_TTL,
    min_interval: float = DEFAULT_MIN_INTERVAL,
) -> dict[str, Any]:
    return fetch_openalex_cached(
        openalex_url_from_args(doi=doi, openalex_id=openalex_id, mailto=mailto),
        cache_dir=cache_dir or default_cache_dir(),
        cache_ttl=cache_ttl,
        min_interval=min_interval,
    )


def parse_openalex_work(payload: dict[str, Any]) -> dict[str, Any]:
    ids = payload.get("ids") or {}
    primary_source = (payload.get("primary_location") or {}).get("source") or {}
    doi = ids.get("doi") or payload.get("doi")
    normalized_doi = normalize_doi(doi) if doi else None
    percentile = payload.get("cited_by_percentile_year") or {}
    return {
        "openalex_id": ids.get("openalex") or payload.get("id"),
        "doi": normalized_doi,
        "title": payload.get("display_name"),
        "publication_year": payload.get("publication_year"),
        "cited_by_count": payload.get("cited_by_count"),
        "citation_percentile_min": percentile.get("min"),
        "citation_percentile_max": percentile.get("max"),
        "counts_by_year": payload.get("counts_by_year") or [],
        "journal_name": primary_source.get("display_name"),
        "journal_issn_l": primary_source.get("issn_l"),
        "type": payload.get("type"),
    }


def summarize_altmetric_payload(
    payload: dict[str, Any] | None, reason: str | None = None
) -> dict[str, Any]:
    if payload is None:
        return {"status": "unavailable", "reason": reason or "not_requested"}
    return {
        "status": "available",
        "score": payload.get("score"),
        "journal": payload.get("journal"),
        "details_url": payload.get("details_url") or payload.get("url"),
        "cited_by_posts_count": payload.get("cited_by_posts_count"),
        "cited_by_news_outlets_count": payload.get("cited_by_msm_count"),
        "cited_by_tweeters_count": payload.get("cited_by_tweeters_count"),
        "cited_by_policies_count": payload.get("cited_by_policies_count"),
        "cited_by_patents_count": payload.get("cited_by_patents_count"),
        "readers_count": payload.get("readers_count"),
    }


def fetch_altmetric_summary(
    doi: str | None, api_key: str | None, *, min_interval: float = DEFAULT_MIN_INTERVAL
) -> dict[str, Any]:
    if not doi:
        return summarize_altmetric_payload(None, reason="doi_required")
    if not api_key:
        return summarize_altmetric_payload(None, reason="no_api_key")
    # OpenAlex is paced across processes with a lock file; Altmetric only gets
    # this per-caller delay, which spaces a serial shortlist run but does not
    # coordinate concurrent callers.
    if min_interval > 0:
        time.sleep(min_interval)
    encoded_doi = urllib.parse.quote(doi, safe="")
    url = f"https://api.altmetric.com/v1/doi/{encoded_doi}?{urllib.parse.urlencode({'key': api_key})}"
    try:
        payload = fetch_json(url)
    except urllib.error.HTTPError as exc:
        return summarize_altmetric_payload(None, reason=f"http_{exc.code}")
    except (OSError, ValueError):
        # The request URL carries the API key, so no exception text is kept.
        return summarize_altmetric_payload(None, reason="network_error")
    return summarize_altmetric_payload(payload)


def build_report_from_payloads(
    openalex_payload: dict[str, Any],
    *,
    altmetric_payload: dict[str, Any] | None = None,
    altmetric_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "openalex": parse_openalex_work(openalex_payload),
        "altmetric": summarize_altmetric_payload(
            altmetric_payload, reason=altmetric_reason
        ),
    }


def build_live_report(args: argparse.Namespace) -> dict[str, Any]:
    doi = normalize_doi(args.doi) if args.doi else None
    openalex_id = normalize_openalex_id(args.openalex_id) if args.openalex_id else None
    cache_dir = Path(getattr(args, "cache_dir", None) or default_cache_dir())
    cache_ttl = getattr(args, "cache_ttl", DEFAULT_CACHE_TTL)
    min_interval = getattr(args, "min_interval", DEFAULT_MIN_INTERVAL)
    openalex_payload = fetch_openalex_work(
        doi=doi,
        openalex_id=openalex_id,
        mailto=args.mailto,
        cache_dir=cache_dir,
        cache_ttl=cache_ttl,
        min_interval=min_interval,
    )
    openalex_summary = parse_openalex_work(openalex_payload)
    # An OpenAlex-ID lookup can still resolve a DOI. Use the canonical DOI from
    # the returned work for Altmetric instead of treating ID-based input as
    # permanently DOI-less.
    resolved_doi = openalex_summary.get("doi")
    if args.altmetric:
        altmetric_summary = fetch_altmetric_summary(
            doi=resolved_doi,
            api_key=os.environ.get("ALTMETRIC_API_KEY"),
            min_interval=min_interval,
        )
    else:
        altmetric_summary = summarize_altmetric_payload(None, reason="not_requested")
    return {
        "openalex": openalex_summary,
        "altmetric": altmetric_summary,
        "request_policy": {
            "cache_dir": str(cache_dir),
            "cache_ttl_seconds": cache_ttl,
            "min_interval_seconds": min_interval,
        },
    }


def format_text(report: dict[str, Any]) -> str:
    openalex = report["openalex"]
    altmetric = report["altmetric"]
    lines = [
        f"Title: {openalex.get('title') or 'n/a'}",
        f"DOI: {openalex.get('doi') or 'n/a'}",
        f"OpenAlex ID: {openalex.get('openalex_id') or 'n/a'}",
        f"Publication year: {openalex.get('publication_year') or 'n/a'}",
        f"Cited by count: {openalex.get('cited_by_count')}",
        f"Journal: {openalex.get('journal_name') or 'n/a'}",
    ]
    if altmetric.get("status") == "available":
        lines.append(f"Altmetric score: {altmetric.get('score')}")
    else:
        lines.append(f"Altmetric: unavailable ({altmetric.get('reason')})")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Report OpenAlex citation counts for a work. An optional OpenAlex API key "
            "comes only from the OPENALEX_API_KEY environment variable. "
            "Pass --altmetric to add Altmetric attention data; its key comes only from "
            "the ALTMETRIC_API_KEY environment variable. Neither key is ever printed."
        )
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--doi", help="DOI for the work to assess")
    group.add_argument("--openalex-id", help="OpenAlex work ID, e.g. W2741809807")
    parser.add_argument(
        "--mailto",
        help=(
            "Contact address for the OpenAlex polite pool. Pass it only when the user "
            "gave one for this purpose; no environment variable supplies it."
        ),
    )
    parser.add_argument(
        "--altmetric",
        action="store_true",
        help="Also request Altmetric data (needs ALTMETRIC_API_KEY in the environment)",
    )
    parser.add_argument("--cache-dir", help="OpenAlex response cache directory")
    parser.add_argument(
        "--cache-ttl",
        type=float,
        default=DEFAULT_CACHE_TTL,
        help="Maximum cached response age in seconds",
    )
    parser.add_argument(
        "--min-interval",
        type=float,
        default=DEFAULT_MIN_INTERVAL,
        help="Minimum seconds between OpenAlex requests across processes",
    )
    parser.add_argument("--format", choices=("json", "text"), default="json")
    parser.add_argument("--output", help="Write output to a file instead of stdout")
    parser.add_argument(
        "--force", action="store_true", help="Overwrite an existing --output file"
    )
    return parser


def redact(text: str, *secrets: str | None) -> str:
    """Replace every non-empty secret in ``text``."""
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[redacted]")
    return text


def refuse_overwrite(output: Path) -> int:
    """Report that `output` exists and return the failure exit code."""
    print(f"Error: refusing to overwrite {output}; pass --force", file=sys.stderr)
    return 1


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    output = Path(args.output) if args.output else None
    if output and output.exists() and not args.force:
        return refuse_overwrite(output)
    try:
        report = build_live_report(args)
    except Exception as exc:  # noqa: BLE001  # top-level boundary: report and exit
        message = redact(
            str(exc),
            os.environ.get(OPENALEX_KEY_ENV),
            os.environ.get("ALTMETRIC_API_KEY"),
        )
        print(f"Error: {message}", file=sys.stderr)
        return 1

    rendered = (
        json.dumps(report, indent=2) if args.format == "json" else format_text(report)
    )
    if output:
        try:
            # Exclusive creation: a file that appeared during the run is kept.
            with output.open("w" if args.force else "x", encoding="utf-8") as handle:
                handle.write(rendered.rstrip("\n") + "\n")
        except FileExistsError:
            return refuse_overwrite(output)
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
