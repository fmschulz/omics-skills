#!/usr/bin/env python3
"""Search bioRxiv through the official API and locally filter metadata."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shlex
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


API_BASE = "https://api.biorxiv.org/details/biorxiv"
USER_AGENT = "omics-skills-biorxiv-search/1.0 (+https://github.com/fmschulz/omics-skills)"
VALID_FIELDS = ("title", "abstract", "authors")


def compact_whitespace(text: str) -> str:
    return " ".join(text.split())


def normalize_term(text: str) -> str:
    return compact_whitespace(text).strip().lower()


def normalize_author_term(text: str) -> str:
    return compact_whitespace(re.sub(r"[^\w]+", " ", text, flags=re.UNICODE)).lower()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search bioRxiv via the official API and locally filter title/abstract/author metadata."
    )
    parser.add_argument("query", nargs="?", help="Keyword query for local filtering")
    parser.add_argument(
        "max_results",
        nargs="?",
        type=int,
        default=10,
        help="Maximum number of results to return (default: 10)",
    )
    parser.add_argument(
        "--phrase",
        action="store_true",
        help="Treat the whole query as one phrase instead of splitting on spaces",
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Use the most recent N days of bioRxiv records",
    )
    parser.add_argument("--start-date", help="Explicit interval start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="Explicit interval end date (YYYY-MM-DD)")
    parser.add_argument("--category", help="bioRxiv subject category such as genomics")
    parser.add_argument(
        "--author",
        action="append",
        default=[],
        help="Author substring to match locally; repeat for multiple variants",
    )
    parser.add_argument(
        "--fields",
        default="title,abstract,authors",
        help="Comma-delimited local keyword search fields (default: title,abstract,authors)",
    )
    parser.add_argument("--doi", help="Fetch a specific bioRxiv DOI directly")
    parser.add_argument(
        "--scan-limit",
        type=int,
        default=300,
        help="Maximum number of API records to inspect locally (default: 300)",
    )
    parser.add_argument(
        "--all-versions",
        action="store_true",
        help="Keep multiple versions of the same DOI instead of collapsing to the latest version",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Network timeout in seconds (default: 30)",
    )
    parser.add_argument("--retries", type=int, default=3, help="Retries for HTTP 429 and transient 5xx responses")
    parser.add_argument("--retry-backoff", type=float, default=1.0, help="Base seconds for exponential retry backoff")
    return parser


def parse_date(value: str | None) -> dt.date | None:
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


def parse_interval(args: argparse.Namespace) -> tuple[str, list[str]]:
    warnings: list[str] = []
    if args.doi:
        return "", warnings

    if args.days is not None and (args.start_date or args.end_date):
        raise ValueError("use either --days or --start-date/--end-date, not both")

    if args.start_date or args.end_date:
        if not (args.start_date and args.end_date):
            raise ValueError("--start-date and --end-date must be provided together")
        start = parse_date(args.start_date)
        end = parse_date(args.end_date)
        if start is None or end is None:
            raise ValueError("dates must use YYYY-MM-DD")
        if start > end:
            raise ValueError("--start-date must be <= --end-date")
        return f"{start.isoformat()}/{end.isoformat()}", warnings

    days = args.days
    if days is None:
        days = 30
        warnings.append("no interval provided; defaulted to the most recent 30 days")
    if days <= 0:
        raise ValueError("--days must be a positive integer")
    today = dt.datetime.now(dt.timezone.utc).date()
    start = today - dt.timedelta(days=days)
    return f"{start.isoformat()}/{today.isoformat()}", warnings


def parse_fields(raw: str) -> list[str]:
    fields = []
    seen = set()
    for part in raw.split(","):
        field = normalize_term(part)
        if not field:
            continue
        if field not in VALID_FIELDS:
            raise ValueError(f"unsupported field '{field}'; choose from {', '.join(VALID_FIELDS)}")
        if field not in seen:
            seen.add(field)
            fields.append(field)
    if not fields:
        raise ValueError("at least one search field is required")
    return fields


def parse_query_groups(query: str | None, phrase: bool) -> list[list[str]]:
    if not query:
        return []
    text = compact_whitespace(query)
    if not text:
        return []
    if phrase:
        return [[normalize_term(text)]]

    groups = []
    for chunk in re.split(r"\s+OR\s+", text, flags=re.IGNORECASE):
        piece = compact_whitespace(chunk)
        if not piece:
            continue
        try:
            tokens = shlex.split(piece)
        except ValueError:
            tokens = piece.split()
        terms = [normalize_term(token) for token in tokens if normalize_term(token)]
        if terms:
            groups.append(terms)
    return groups


def parse_authors(raw: str | None) -> list[str]:
    if not raw:
        return []
    if ";" in raw:
        parts = raw.split(";")
    else:
        parts = [raw]
    return [compact_whitespace(part) for part in parts if compact_whitespace(part)]


def expand_author_variants(author_filters: list[str]) -> list[str]:
    variants: set[str] = set()
    for author in author_filters:
        text = compact_whitespace(author)
        if not text:
            continue
        variants.add(normalize_author_term(text))

        if "," in text:
            surname, given_text = text.split(",", 1)
            surname = normalize_author_term(surname)
            given = normalize_author_term(given_text).split()
        else:
            tokens = normalize_author_term(text).split()
            if len(tokens) < 2:
                continue
            surname, given = tokens[-1], tokens[:-1]
        if not surname or not given:
            continue
        initials = [name[0] for name in given if name]
        first = given[0]
        variants.add(normalize_author_term(" ".join([*given, surname])))
        variants.add(normalize_author_term(" ".join([*initials, surname])))
        variants.add(normalize_author_term(" ".join([surname, *given])))
        variants.add(normalize_author_term(" ".join([surname, *initials])))
        variants.add(normalize_author_term(" ".join([first, surname])))
        variants.add(normalize_author_term(" ".join([first[0], surname])))
        variants.add(normalize_author_term(" ".join([surname, first])))
        variants.add(normalize_author_term(" ".join([surname, first[0]])))

    return sorted(variants)


def fetch_json(url: str, timeout: int, retries: int = 3, retry_backoff: float = 1.0) -> dict[str, object]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return json.loads(response.read().decode(charset))
        except urllib.error.HTTPError as exc:
            retryable = exc.code == 429 or 500 <= exc.code < 600
            if retryable and attempt < retries:
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                try:
                    delay = float(retry_after) if retry_after is not None else retry_backoff * (2**attempt)
                except ValueError:
                    delay = retry_backoff * (2**attempt)
                time.sleep(max(0, delay))
                continue
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} from bioRxiv API: {body}") from exc
    raise RuntimeError("bioRxiv API request failed after retry loop")


def build_author_match_groups(records: list[dict[str, object]], requested: list[str]) -> list[dict[str, object]]:
    groups = []
    for author in requested:
        variants = expand_author_variants([author])
        dois = [record.get("doi") for record in records if matches_author_filters(str(record.get("authors_text") or ""), variants)]
        groups.append({"requested_form": author, "expanded_variants": variants, "result_dois": dois, "ambiguous_initial_form": bool(re.match(r"^[A-Za-z]\.\s", author.strip()))})
    return groups


def build_url(args: argparse.Namespace, interval: str, cursor: int) -> str:
    if args.doi:
        doi = urllib.parse.quote(args.doi, safe="/")
        return f"{API_BASE}/{doi}/na/json"

    base = f"{API_BASE}/{interval}/{cursor}/json"
    if args.category:
        return base + "?" + urllib.parse.urlencode({"category": args.category})
    return base


def to_int(value: object) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def normalize_record(raw: dict[str, object]) -> dict[str, object]:
    doi = compact_whitespace(str(raw.get("doi", "") or ""))
    title = compact_whitespace(str(raw.get("title", "") or ""))
    abstract = compact_whitespace(str(raw.get("abstract", "") or ""))
    authors_raw = compact_whitespace(str(raw.get("authors", "") or ""))
    version = to_int(raw.get("version"))
    biorxiv_url = None
    if doi:
        if version is not None:
            biorxiv_url = f"https://www.biorxiv.org/content/{doi}v{version}"
        else:
            biorxiv_url = f"https://www.biorxiv.org/search/{urllib.parse.quote(doi)}"

    return {
        "doi": doi or None,
        "title": title or None,
        "authors": parse_authors(authors_raw),
        "authors_text": authors_raw or None,
        "author_corresponding": compact_whitespace(str(raw.get("author_corresponding", "") or "")) or None,
        "author_corresponding_institution": compact_whitespace(
            str(raw.get("author_corresponding_institution", "") or "")
        )
        or None,
        "date": compact_whitespace(str(raw.get("date", "") or "")) or None,
        "version": version,
        "type": compact_whitespace(str(raw.get("type", "") or "")) or None,
        "license": compact_whitespace(str(raw.get("license", "") or "")) or None,
        "category": compact_whitespace(str(raw.get("category", "") or "")) or None,
        "abstract": abstract or None,
        "published": compact_whitespace(str(raw.get("published", "") or "")) or None,
        "server": compact_whitespace(str(raw.get("server", "") or "")) or None,
        "doi_url": f"https://doi.org/{doi}" if doi else None,
        "biorxiv_url": biorxiv_url,
    }


def select_text(record: dict[str, object], fields: list[str]) -> dict[str, str]:
    selected: dict[str, str] = {}
    if "title" in fields:
        selected["title"] = str(record.get("title") or "")
    if "abstract" in fields:
        selected["abstract"] = str(record.get("abstract") or "")
    if "authors" in fields:
        selected["authors"] = str(record.get("authors_text") or "")
    return selected


def matches_groups(text: str, groups: list[list[str]]) -> bool:
    if not groups:
        return True
    haystack = normalize_term(text)
    if not haystack:
        return False
    return any(all(term in haystack for term in group) for group in groups)


def matches_author_filters(authors_text: str, author_variants: list[str]) -> bool:
    if not author_variants:
        return True
    haystack = normalize_author_term(authors_text)
    if not haystack:
        return False
    padded = f" {haystack} "
    return any(f" {variant} " in padded for variant in author_variants)


def matched_fields(
    selected_text: dict[str, str], query_groups: list[list[str]], author_variants: list[str]
) -> list[str]:
    fields: list[str] = []
    for field, value in selected_text.items():
        if field == "authors":
            if author_variants and matches_author_filters(value, author_variants):
                fields.append(field)
                continue
        if query_groups and matches_groups(value, query_groups):
            fields.append(field)
    return fields


def record_matches(
    record: dict[str, object], fields: list[str], query_groups: list[list[str]], author_variants: list[str]
) -> tuple[bool, list[str]]:
    selected = select_text(record, fields)
    combined_text = " ".join(selected.values())
    if not matches_groups(combined_text, query_groups):
        return False, []
    if not matches_author_filters(str(record.get("authors_text") or ""), author_variants):
        return False, []
    return True, matched_fields(selected, query_groups, author_variants)


def dedupe_latest(records: list[dict[str, object]]) -> tuple[list[dict[str, object]], int]:
    by_doi: dict[str, dict[str, object]] = {}
    dropped = 0
    for record in records:
        doi = str(record.get("doi") or "")
        if not doi:
            key = f"__no_doi__::{record.get('title')}::{record.get('date')}::{record.get('version')}"
            by_doi[key] = record
            continue

        existing = by_doi.get(doi)
        if existing is None:
            by_doi[doi] = record
            continue

        existing_version = to_int(existing.get("version")) or -1
        current_version = to_int(record.get("version")) or -1
        existing_date = parse_date(str(existing.get("date") or ""))
        current_date = parse_date(str(record.get("date") or ""))

        replace = False
        if current_version > existing_version:
            replace = True
        elif current_version == existing_version:
            if current_date and existing_date:
                replace = current_date > existing_date
            elif current_date and not existing_date:
                replace = True

        if replace:
            by_doi[doi] = record
            dropped += 1
        else:
            dropped += 1

    return list(by_doi.values()), dropped


def sort_records(records: list[dict[str, object]]) -> list[dict[str, object]]:
    def sort_key(record: dict[str, object]) -> tuple[dt.date, int]:
        date_value = parse_date(str(record.get("date") or "")) or dt.date.min
        version = to_int(record.get("version")) or -1
        return (date_value, version)

    return sorted(records, key=sort_key, reverse=True)


def page_metadata(
    data: dict[str, object],
) -> tuple[list[dict[str, object]], int | None, int | None, int | None]:
    collection = data.get("collection", [])
    if not isinstance(collection, list):
        raise RuntimeError("unexpected bioRxiv API response: missing collection list")
    if not all(isinstance(record, dict) for record in collection):
        raise RuntimeError("unexpected bioRxiv API response: collection contains a non-record")

    page_count = None
    response_cursor = None
    reported_total = None
    messages = data.get("messages", [])
    if isinstance(messages, list) and messages and isinstance(messages[0], dict):
        message = messages[0]
        page_count = to_int(message.get("count"))
        response_cursor = to_int(message.get("cursor"))
        reported_total = to_int(message.get("total"))
    return collection, page_count, response_cursor, reported_total


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.max_results < 1:
            raise ValueError("max_results must be >= 1")
        if args.scan_limit < 1:
            raise ValueError("--scan-limit must be >= 1")
        if args.timeout < 1:
            raise ValueError("--timeout must be >= 1")
        if args.retries < 0 or args.retry_backoff < 0:
            raise ValueError("--retries and --retry-backoff must be >= 0")

        fields = parse_fields(args.fields)
        query_groups = parse_query_groups(args.query, args.phrase)
        author_variants = expand_author_variants(args.author)
        interval, warnings = parse_interval(args)

        if not args.doi and not query_groups and not author_variants and not args.category:
            warnings.append("no keyword or author filter supplied; returning recent bioRxiv records only")

        request_urls: list[str] = []
        matched: list[dict[str, object]] = []
        total_available = None
        pages_fetched = 0
        records_scanned = 0
        reached_scan_limit = False

        if args.doi:
            url = build_url(args, "", 0)
            request_urls.append(url)
            data = fetch_json(url, args.timeout, args.retries, args.retry_backoff)
            pages_fetched = 1
            collection = data.get("collection", [])
            if not isinstance(collection, list):
                raise RuntimeError("unexpected bioRxiv API response: missing collection list")
            total_available = len(collection)
            records_scanned = len(collection)
            for raw in collection:
                record = normalize_record(raw)
                is_match, where = record_matches(record, fields, query_groups, author_variants)
                if is_match:
                    record["matched_in"] = where
                    matched.append(record)
        else:
            first_url = build_url(args, interval, 0)
            request_urls.append(first_url)
            first_data = fetch_json(first_url, args.timeout, args.retries, args.retry_backoff)
            pages_fetched = 1
            first_collection, first_count, _, total_available = page_metadata(first_data)
            page_size = first_count if first_count is not None and first_count > 0 else len(first_collection)

            if total_available is not None and page_size > 0:
                cursor = ((max(total_available, 1) - 1) // page_size) * page_size
                while records_scanned < args.scan_limit:
                    if cursor == 0:
                        data = first_data
                    else:
                        url = build_url(args, interval, cursor)
                        request_urls.append(url)
                        data = fetch_json(url, args.timeout, args.retries, args.retry_backoff)
                        pages_fetched += 1

                    collection, _, _, reported_total = page_metadata(data)
                    if reported_total is not None:
                        total_available = reported_total
                    if not collection:
                        break

                    for raw in reversed(collection):
                        records_scanned += 1
                        record = normalize_record(raw)
                        is_match, where = record_matches(record, fields, query_groups, author_variants)
                        if is_match:
                            record["matched_in"] = where
                            matched.append(record)
                        if records_scanned >= args.scan_limit:
                            reached_scan_limit = records_scanned < total_available
                            break

                    if reached_scan_limit or cursor == 0:
                        break
                    cursor = max(0, cursor - page_size)
            else:
                warnings.append(
                    "bioRxiv API omitted pagination totals; scanned forward because the newest cursor was unavailable"
                )
                cursor = 0
                data = first_data
                while records_scanned < args.scan_limit:
                    collection, page_count, response_cursor, reported_total = page_metadata(data)
                    if reported_total is not None:
                        total_available = reported_total
                    if not collection:
                        break

                    for raw in collection:
                        records_scanned += 1
                        record = normalize_record(raw)
                        is_match, where = record_matches(record, fields, query_groups, author_variants)
                        if is_match:
                            record["matched_in"] = where
                            matched.append(record)
                        if records_scanned >= args.scan_limit:
                            reached_scan_limit = (
                                total_available is None or records_scanned < total_available
                            )
                            break

                    if reached_scan_limit:
                        break
                    if total_available is not None and records_scanned >= total_available:
                        break

                    page_advance = (
                        page_count
                        if page_count is not None and page_count > 0
                        else len(collection)
                    )
                    if page_advance <= 0:
                        break
                    next_cursor = (
                        response_cursor if response_cursor is not None else cursor
                    ) + page_advance
                    if next_cursor <= cursor:
                        raise RuntimeError("bioRxiv API pagination did not advance the cursor")
                    cursor = next_cursor
                    url = build_url(args, interval, cursor)
                    request_urls.append(url)
                    data = fetch_json(url, args.timeout, args.retries, args.retry_backoff)
                    pages_fetched += 1

        deduped = matched
        versions_collapsed = 0
        if not args.all_versions:
            deduped, versions_collapsed = dedupe_latest(matched)

        ordered = sort_records(deduped)
        results = ordered[: args.max_results]

        output = {
            "success": True,
            "request": {
                "query": args.query,
                "query_groups": query_groups,
                "phrase": args.phrase,
                "doi": args.doi,
                "days": args.days,
                "start_date": args.start_date,
                "end_date": args.end_date,
                "interval": interval or None,
                "category": args.category,
                "author_filters": args.author,
                "expanded_author_variants": author_variants,
                "search_fields": fields,
                "max_results": args.max_results,
                "scan_limit": args.scan_limit,
                "all_versions": args.all_versions,
                "timeout": args.timeout,
                "retries": args.retries,
                "retry_backoff": args.retry_backoff,
            },
            "api": {
                "base_url": API_BASE,
                "pages_fetched": pages_fetched,
                "records_scanned": records_scanned,
                "total_available": total_available,
                "request_urls": request_urls,
            },
            "result_summary": {
                "matched_records_before_dedup": len(matched),
                "matched_records_after_dedup": len(deduped),
                "returned": len(results),
                "versions_collapsed": versions_collapsed,
                "version_policy": "all_versions" if args.all_versions else "latest_numeric_version_per_doi_then_latest_date",
                "reached_scan_limit": reached_scan_limit,
            },
            "warnings": warnings,
            "results": results,
            "author_match_groups": build_author_match_groups(results, args.author),
        }

        if reached_scan_limit:
            output["warnings"].append(
                "scan limit reached before exhausting the interval; broaden recall by increasing --scan-limit"
            )

        json.dump(output, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    except Exception as exc:  # pragma: no cover - CLI surface
        json.dump({"success": False, "error": str(exc)}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
