#!/usr/bin/env python3
"""Small helper for grouped polars-dovmed literature queries."""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query")
    parser.add_argument("--group", action="append", default=[])
    parser.add_argument("--details", nargs="+")
    parser.add_argument("--max-results", type=int, default=25)
    parser.add_argument("--fast-mode", action="store_true")
    parser.add_argument("--year", type=int)
    parser.add_argument("--timeout", type=int)
    parser.add_argument("--base-url", default="https://api.newlineages.com")
    parser.add_argument("--api-key")
    parser.add_argument("--raw", action="store_true")
    args = parser.parse_args()
    chosen = sum(bool(value) for value in (args.query, args.group, args.details))
    if chosen != 1:
        parser.error("provide exactly one of --query, --group, or --details")
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


def build_request(args):
    if args.details:
        return "/api/get_paper_details", {"pmc_ids": args.details}
    if args.group:
        primary_queries = dict(parse_group(spec) for spec in args.group)
        payload = {
            "primary_queries": primary_queries,
            "search_columns": ["title", "abstract_text", "full_text"],
            "extract_matches": "primary",
            "add_group_counts": "primary",
            "max_results": args.max_results,
        }
        return "/api/scan_literature_advanced", payload
    payload = {
        "query": args.query,
        "max_results": args.max_results,
        "extract_matches": False,
        "fast_mode": args.fast_mode,
    }
    return "/api/search_literature", payload


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
    timeout = args.timeout or (600 if endpoint.endswith("advanced") else 120)
    try:
        result = post_json(args.base_url, endpoint, api_key, payload, timeout)
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"http error {exc.code}: {exc.read().decode('utf-8')}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"request failed: {exc.reason}") from exc
    if args.raw:
        print(json.dumps(result, indent=2))
        return
    papers = result.get("papers", [])
    compact, missing_year, filtered_year = summarize_papers(papers, args.year)
    summary = {
        "endpoint": endpoint,
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
    if endpoint == "/api/scan_literature_advanced":
        summary["warnings"].append(
            "Grouped scans improve recall for multi-concept biology queries."
        )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
