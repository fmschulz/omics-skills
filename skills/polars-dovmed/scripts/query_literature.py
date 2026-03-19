#!/usr/bin/env python3
"""Small helper for grouped polars-dovmed literature queries."""

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path


def load_env_file(path):
    env_path = Path(path).expanduser()
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def parse_args():
    load_env_file("~/.config/polars-dovmed/.env")
    parser = argparse.ArgumentParser()
    parser.add_argument("--query")
    parser.add_argument("--queries-file")
    parser.add_argument("--group", action="append", default=[])
    parser.add_argument("--details", nargs="+")
    parser.add_argument(
        "--mode",
        choices=["advanced", "discovery"],
        default="discovery",
        help="Structured-search mode for --queries-file/--group. Default is discovery for fast candidate retrieval.",
    )
    parser.add_argument("--max-results", type=int, default=25)
    parser.add_argument("--fast-mode", action="store_true")
    parser.add_argument(
        "--search-columns",
        default="title,abstract_text,full_text",
        help="Comma-separated columns for advanced structured search",
    )
    parser.add_argument(
        "--extract-matches",
        choices=["primary", "secondary", "both", "none"],
        default="none",
        help="Extraction mode for advanced structured search",
    )
    parser.add_argument(
        "--add-group-counts",
        choices=["primary", "secondary", "both"],
        default="primary",
        help="Group-count mode for advanced structured search",
    )
    parser.add_argument("--year", type=int)
    parser.add_argument("--timeout", type=int)
    parser.add_argument("--base-url", default="https://api.newlineages.com")
    parser.add_argument("--api-key")
    parser.add_argument("--save-payload")
    parser.add_argument("--save-response")
    parser.add_argument("--save-discovery-payload")
    parser.add_argument("--save-discovery-response")
    parser.add_argument(
        "--discovery-fallback",
        action="store_true",
        help="If a structured advanced query fails or times out, retry a simplified flat discovery query built from query-group names",
    )
    parser.add_argument("--raw", action="store_true")
    args = parser.parse_args()
    chosen = sum(
        bool(value) for value in (args.query, args.queries_file, args.group, args.details)
    )
    if chosen != 1:
        parser.error(
            "provide exactly one of --query, --queries-file, --group, or --details"
        )
    return args


def load_api_key(explicit_key):
    api_key = explicit_key or os.environ.get("POLARS_DOVMED_API_KEY")
    if not api_key:
        raise SystemExit("missing POLARS_DOVMED_API_KEY")
    return api_key


def parse_group(spec):
    if "=" not in spec:
        raise SystemExit(f"invalid group '{spec}', expected name=term1,term2")
    name, raw_terms = spec.split("=", 1)
    terms = [term.strip() for term in raw_terms.split(",") if term.strip()]
    if not name or not terms:
        raise SystemExit(f"invalid group '{spec}', expected name=term1,term2")
    return name, [[term] for term in terms]


def load_queries_file(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise SystemExit(f"queries file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid queries file '{path}': {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"invalid queries file '{path}', expected a JSON object")
    return data


def resolve_year(paper):
    year = paper.get("year")
    if isinstance(year, int):
        return year
    if isinstance(year, str) and year.isdigit():
        return int(year)
    match = re.match(r"(\d{4})", paper.get("publication_date") or "")
    return int(match.group(1)) if match else None


def compact_paper(paper):
    return {
        "pmc_id": paper.get("pmc_id"),
        "pmid": paper.get("pmid"),
        "title": paper.get("title"),
        "journal": paper.get("journal"),
        "year": resolve_year(paper),
        "publication_date": paper.get("publication_date"),
        "doi": paper.get("doi"),
    }


def build_structured_request(primary_queries, args):
    payload = {
        "primary_queries": primary_queries,
        "search_columns": [col.strip() for col in args.search_columns.split(",") if col.strip()],
        "extract_matches": args.extract_matches,
        "add_group_counts": args.add_group_counts,
        "max_results": args.max_results,
        "mode": args.mode,
    }
    endpoint = (
        "/api/discover_literature"
        if args.mode == "discovery"
        else "/api/scan_literature_advanced"
    )
    return endpoint, payload


def structured_scan_fallback(endpoint, payload):
    if endpoint == "/api/discover_literature":
        return "/api/scan_literature_advanced", payload
    return endpoint, payload


def build_request(args):
    if args.details:
        return "/api/get_paper_details", {"pmc_ids": args.details}
    if args.queries_file:
        return build_structured_request(load_queries_file(args.queries_file), args)
    if args.group:
        return build_structured_request(dict(parse_group(spec) for spec in args.group), args)
    payload = {
        "query": args.query,
        "max_results": args.max_results,
        "extract_matches": False,
        "fast_mode": args.fast_mode,
    }
    return "/api/search_literature", payload


def build_discovery_request(args):
    if not args.queries_file:
        raise SystemExit("--discovery-fallback requires --queries-file")
    original_mode = args.mode
    args.mode = "discovery"
    try:
        return build_structured_request(load_queries_file(args.queries_file), args)
    finally:
        args.mode = original_mode


def maybe_save_json(path, payload):
    if not path:
        return
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def post_json(base_url, endpoint, api_key, payload, timeout):
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}{endpoint}",
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "X-API-Key": api_key,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def summarize_papers(papers, target_year):
    kept = []
    missing_year = 0
    filtered_year = 0
    for paper in papers:
        compact = compact_paper(paper)
        paper_year = compact["year"]
        if target_year is None:
            kept.append(compact)
            continue
        if paper_year is None:
            missing_year += 1
            continue
        if paper_year == target_year:
            kept.append(compact)
        else:
            filtered_year += 1
    return kept, missing_year, filtered_year


def has_incomplete_citation(papers):
    for paper in papers:
        if paper["year"] is None or not paper.get("doi"):
            return True
    return False


def main():
    args = parse_args()
    api_key = load_api_key(args.api_key)
    endpoint, payload = build_request(args)
    maybe_save_json(args.save_payload, {"endpoint": endpoint, "payload": payload})
    timeout = args.timeout or (600 if endpoint.endswith("advanced") else 120)
    try:
        result = post_json(args.base_url, endpoint, api_key, payload, timeout)
    except urllib.error.HTTPError as exc:
        if exc.code == 404 and endpoint == "/api/discover_literature":
            endpoint, payload = structured_scan_fallback(endpoint, payload)
            maybe_save_json(
                args.save_discovery_payload or args.save_payload,
                {
                    "endpoint": endpoint,
                    "payload": payload,
                    "note": "fallback from /api/discover_literature to /api/scan_literature_advanced with mode=discovery",
                },
            )
            result = post_json(args.base_url, endpoint, api_key, payload, timeout)
        elif args.discovery_fallback and endpoint.endswith("advanced"):
            endpoint, payload = build_discovery_request(args)
            maybe_save_json(
                args.save_discovery_payload or args.save_payload,
                {
                    "endpoint": endpoint,
                    "payload": payload,
                    "note": "discovery fallback after advanced query HTTP error",
                },
            )
            result = post_json(args.base_url, endpoint, api_key, payload, 120)
        else:
            raise SystemExit(f"http error {exc.code}: {exc.read().decode('utf-8')}") from exc
    except urllib.error.URLError as exc:
        if args.discovery_fallback and endpoint.endswith("advanced"):
            endpoint, payload = build_discovery_request(args)
            maybe_save_json(
                args.save_discovery_payload or args.save_payload,
                {
                    "endpoint": endpoint,
                    "payload": payload,
                    "note": "discovery fallback after advanced query URL error",
                },
            )
            result = post_json(args.base_url, endpoint, api_key, payload, 120)
        else:
            raise SystemExit(f"request failed: {exc.reason}") from exc
    if endpoint == "/api/discover_literature" and args.discovery_fallback:
        maybe_save_json(args.save_discovery_response or args.save_response, result)
    else:
        maybe_save_json(args.save_response, result)
    if args.raw:
        print(json.dumps(result, indent=2))
        return
    papers = result.get("papers", [])
    compact, missing_year, filtered_year = summarize_papers(papers, args.year)
    summary = {
        "endpoint": endpoint,
        "mode": args.mode if args.queries_file or args.group else None,
        "strategy_used": result.get("strategy_used"),
        "elapsed_ms": result.get("elapsed_ms"),
        "signal_terms": result.get("signal_terms"),
        "discovery_query": result.get("discovery_query"),
        "reported_total": result.get("total_found"),
        "returned": len(papers),
        "year_filter": args.year,
        "excluded_missing_year": missing_year,
        "excluded_nonmatching_year": filtered_year,
        "papers": compact,
        "warnings": [],
    }
    if missing_year:
        summary["warnings"].append(
            "Some papers lacked year metadata. Verify recent papers in PubMed or PMC."
        )
    if has_incomplete_citation(compact):
        summary["warnings"].append(
            "Some papers lacked complete citation metadata such as year or DOI."
        )
    if endpoint in ["/api/scan_literature_advanced", "/api/discover_literature"]:
        summary["warnings"].append(
            "Grouped scans improve recall for multi-concept biology queries."
        )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
