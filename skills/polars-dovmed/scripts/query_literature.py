#!/usr/bin/env python3
"""Small helper for grouped polars-dovmed literature queries."""

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ASYNC_ENDPOINTS = {
    "/api/search_literature": "search_literature",
    "/api/scan_literature_advanced": "scan_literature_advanced",
}
SUPPORT_CONCEPT_TOKENS = (
    "host",
    "hosts",
    "infect",
    "infection",
    "interact",
    "interaction",
    "symbio",
    "pathway",
    "metab",
    "association",
    "range",
)
GENERIC_SUPPORT_TERMS = {
    "host",
    "hosts",
    "infect",
    "infects",
    "infected",
    "infection",
    "infections",
    "amoeba",
    "amoebae",
    "protist",
    "protists",
    "microeukaryote",
    "microeukaryotes",
    "symbiont",
    "symbionts",
    "association",
    "associations",
    "range",
}


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
    parser.add_argument(
        "--allow-flat-query",
        action="store_true",
        help="Explicitly allow exploratory free-text search via /api/search_literature",
    )
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
        "--details-rerank-limit",
        type=int,
        default=8,
        help="How many discovery candidates to fetch with get_paper_details for second-pass reranking",
    )
    parser.add_argument(
        "--skip-details-rerank",
        action="store_true",
        help="Skip the automatic discovery -> details -> rerank second pass",
    )
    parser.add_argument(
        "--auto-advanced-refinement",
        action="store_true",
        help="Run an additional advanced structured scan after discovery when the first pass is still too loose",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Use the legacy synchronous request path instead of async jobs",
    )
    parser.add_argument(
        "--poll-timeout",
        type=int,
        default=900,
        help="Maximum seconds to wait for async job completion",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=2,
        help="Fallback poll interval in seconds when the API does not specify one",
    )
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
    if args.query and not args.allow_flat_query:
        parser.error(
            "--query is exploratory free-text search only; use --queries-file/--group from create_patterns, "
            "or pass --allow-flat-query to opt in explicitly"
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
    ranking = paper.get("ranking") or {}
    triage = paper.get("triage") or {}
    return {
        "pmc_id": paper.get("pmc_id"),
        "pmid": paper.get("pmid"),
        "title": paper.get("title"),
        "journal": paper.get("journal"),
        "year": resolve_year(paper),
        "publication_date": paper.get("publication_date"),
        "doi": paper.get("doi"),
        "ranking_score": ranking.get("score"),
        "title_signal_hits": ranking.get("title_signal_hits"),
        "abstract_signal_hits": ranking.get("abstract_signal_hits"),
        "group_count_total": ranking.get("group_count_total"),
        "total_matches": ranking.get("total_matches"),
        "triage_score": triage.get("score"),
        "concept_coverage": triage.get("concept_coverage"),
        "support_concept_coverage": triage.get("support_concept_coverage"),
        "support_specificity_score": triage.get("support_specificity_score"),
        "specific_support_group_hits": triage.get("specific_support_group_hits"),
        "matched_concepts": triage.get("matched_concepts"),
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
    return "/api/scan_literature_advanced", payload


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


def companion_json_path(path, suffix):
    if not path:
        return None
    output = Path(path)
    ext = output.suffix or ".json"
    return str(output.with_name(f"{output.stem}_{suffix}{ext}"))


def make_request(base_url, endpoint, api_key, *, method="GET", payload=None):
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-API-Key": api_key,
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    return urllib.request.Request(
        f"{base_url}{endpoint}",
        data=data,
        headers={
            **headers,
        },
        method=method,
    )


def request_json(base_url, endpoint, api_key, *, timeout, method="GET", payload=None):
    request = make_request(
        base_url,
        endpoint,
        api_key,
        method=method,
        payload=payload,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(base_url, endpoint, api_key, payload, timeout):
    return request_json(
        base_url,
        endpoint,
        api_key,
        timeout=timeout,
        method="POST",
        payload=payload,
    )


def build_submitted_request(endpoint, payload, use_async_jobs):
    if not use_async_jobs:
        return endpoint, payload
    return "/api/jobs", {
        "job_type": ASYNC_ENDPOINTS[endpoint],
        "payload": payload,
    }


def run_async_job(
    base_url,
    endpoint,
    api_key,
    payload,
    *,
    poll_timeout,
    poll_interval,
):
    submitted_endpoint, submitted_payload = build_submitted_request(
        endpoint,
        payload,
        use_async_jobs=True,
    )
    job = post_json(
        base_url,
        submitted_endpoint,
        api_key,
        submitted_payload,
        timeout=min(max(poll_timeout, 30), 120),
    )
    job_id = job.get("job_id")
    if not job_id:
        raise RuntimeError(f"async job submission failed: {job}")

    deadline = time.monotonic() + poll_timeout
    result_endpoint = f"/api/jobs/{job_id}/result"
    while True:
        result_wrapper = request_json(
            base_url,
            result_endpoint,
            api_key,
            timeout=60,
        )
        status = result_wrapper.get("status")
        if status == "succeeded":
            result = result_wrapper.get("result")
            if isinstance(result, dict):
                return result
            raise RuntimeError(f"async job {job_id} succeeded without a JSON result")
        if status == "failed":
            result = result_wrapper.get("result") or {}
            error = result_wrapper.get("error") or result.get("error") or "async job failed"
            raise RuntimeError(f"async job {job_id} failed: {error}")
        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"async job {job_id} timed out after {poll_timeout}s"
            )
        sleep_for = result_wrapper.get("poll_after_sec") or poll_interval
        time.sleep(max(1, int(sleep_for)))


def execute_request(
    base_url,
    endpoint,
    api_key,
    payload,
    *,
    timeout,
    use_async_jobs,
    poll_timeout,
    poll_interval,
):
    try:
        if use_async_jobs:
            return run_async_job(
                base_url,
                endpoint,
                api_key,
                payload,
                poll_timeout=poll_timeout,
                poll_interval=poll_interval,
            )
        return post_json(base_url, endpoint, api_key, payload, timeout)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"http error {exc.code}: {exc.read().decode('utf-8')}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"request failed: {exc.reason}") from exc


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


def normalize_pattern(pattern):
    cleaned = pattern.replace("(?i)", "")
    return cleaned.replace("\\b", r"\b")


def pattern_matches_text(pattern, text):
    if not text:
        return False
    cleaned = normalize_pattern(pattern)
    try:
        return re.search(cleaned, text, flags=re.IGNORECASE) is not None
    except re.error:
        return re.search(re.escape(cleaned), text, flags=re.IGNORECASE) is not None


def field_texts(paper):
    return {
        "title": paper.get("title") or "",
        "abstract": paper.get("abstract_text") or paper.get("abstract") or "",
        "full_text": paper.get("full_text") or "",
    }


def is_support_concept(concept_name):
    lower = concept_name.lower()
    return any(token in lower for token in SUPPORT_CONCEPT_TOKENS)


def term_specificity(term):
    cleaned = normalize_pattern(term).strip().strip("\"'").lower()
    if not cleaned:
        return 0.0
    score = 1.0
    if cleaned in GENERIC_SUPPORT_TERMS:
        score -= 0.6
    if " " in cleaned:
        score += 2.0
    if "-" in cleaned or "/" in cleaned:
        score += 0.5
    if len(cleaned) >= 10:
        score += 0.8
    if any(char.isdigit() for char in cleaned):
        score += 0.5
    return max(score, 0.2)


def group_specificity(group):
    return max((term_specificity(term) for term in group if term), default=0.0)


def analyze_paper_against_queries(paper, primary_queries):
    texts = field_texts(paper)
    combined_text = " ".join(value for value in texts.values() if value)
    matched_group_counts = {}
    matched_group_scores = {}
    title_support_hits = 0
    abstract_support_hits = 0
    full_text_support_hits = 0
    support_specificity_score = 0.0
    specific_support_group_hits = 0

    for concept, groups in primary_queries.items():
        if concept == "disqualifying_terms":
            continue
        matched_groups = 0
        matched_score = 0.0
        for group in groups:
            terms = [term for term in group if term]
            if terms and all(pattern_matches_text(term, combined_text) for term in terms):
                matched_groups += 1
                matched_score += group_specificity(group)
                if is_support_concept(concept) and group_specificity(group) >= 2.0:
                    specific_support_group_hits += 1
        matched_group_counts[concept] = matched_groups
        matched_group_scores[concept] = round(matched_score, 3)
        if is_support_concept(concept):
            support_specificity_score += matched_score
        if matched_groups <= 0 or not is_support_concept(concept):
            continue
        if any(
            group and all(pattern_matches_text(term, texts["title"]) for term in group if term)
            for group in groups
        ):
            title_support_hits += 1
        if any(
            group and all(pattern_matches_text(term, texts["abstract"]) for term in group if term)
            for group in groups
        ):
            abstract_support_hits += 1
        if any(
            group and all(pattern_matches_text(term, texts["full_text"]) for term in group if term)
            for group in groups
        ):
            full_text_support_hits += 1

    matched_concepts = [concept for concept, count in matched_group_counts.items() if count > 0]
    support_concepts = [concept for concept in matched_concepts if is_support_concept(concept)]
    total_group_matches = sum(matched_group_counts.values())
    return {
        "matched_group_counts": matched_group_counts,
        "matched_group_scores": matched_group_scores,
        "matched_concepts": matched_concepts,
        "concept_coverage": len(matched_concepts),
        "support_concept_coverage": len(support_concepts),
        "support_specificity_score": round(support_specificity_score, 3),
        "specific_support_group_hits": specific_support_group_hits,
        "title_support_hits": title_support_hits,
        "abstract_support_hits": abstract_support_hits,
        "full_text_support_hits": full_text_support_hits,
        "total_group_matches": total_group_matches,
    }


def triage_score(paper, analysis):
    discovery_ranking = paper.get("ranking") or {}
    score = (
        int(discovery_ranking.get("score") or 0)
        + analysis["concept_coverage"] * 240
        + analysis["support_concept_coverage"] * 120
        + int(analysis["support_specificity_score"] * 110)
        + analysis["specific_support_group_hits"] * 90
        + analysis["title_support_hits"] * 120
        + analysis["abstract_support_hits"] * 70
        + analysis["full_text_support_hits"] * 25
        + analysis["total_group_matches"] * 20
    )
    if analysis["support_concept_coverage"] > 0 and analysis["specific_support_group_hits"] == 0:
        score -= 80
    return score


def merge_and_rerank_details(discovery_result, details_result, primary_queries):
    discovery_by_id = {
        paper.get("pmc_id"): paper for paper in discovery_result.get("papers") or []
    }
    triaged = []
    for paper in details_result.get("papers") or []:
        pmc_id = paper.get("pmc_id")
        discovery_paper = discovery_by_id.get(pmc_id, {})
        analysis = analyze_paper_against_queries(paper, primary_queries)
        triaged_paper = dict(paper)
        triaged_paper["ranking"] = discovery_paper.get("ranking") or {}
        triaged_paper["triage"] = {
            "score": triage_score(discovery_paper, analysis),
            **analysis,
        }
        triaged.append(triaged_paper)
    triaged.sort(
        key=lambda paper: (
            paper["triage"]["score"],
            paper["triage"]["support_concept_coverage"],
            paper["triage"]["concept_coverage"],
            (paper.get("ranking") or {}).get("score") or 0,
        ),
        reverse=True,
    )
    return triaged


def recommended_next_step(triaged_papers, primary_queries):
    concept_count = len([key for key in primary_queries if key != "disqualifying_terms"])
    if not triaged_papers:
        return "advanced_refinement_recommended"
    top = triaged_papers[0].get("triage") or {}
    if concept_count > 1 and top.get("concept_coverage", 0) < min(2, concept_count):
        return "advanced_refinement_recommended"
    if any(is_support_concept(key) for key in primary_queries if key != "disqualifying_terms"):
        if top.get("support_concept_coverage", 0) == 0:
            return "advanced_refinement_recommended"
    return "details_triage_sufficient"


def main():
    args = parse_args()
    api_key = load_api_key(args.api_key)
    endpoint, payload = build_request(args)
    timeout = args.timeout or (600 if endpoint.endswith("advanced") else 120)
    use_async_jobs = not args.sync and endpoint in ASYNC_ENDPOINTS
    submitted_endpoint, submitted_payload = build_submitted_request(
        endpoint,
        payload,
        use_async_jobs,
    )
    maybe_save_json(
        args.save_payload,
        {
            "endpoint": submitted_endpoint,
            "payload": submitted_payload,
            "target_endpoint": endpoint,
            "target_payload": payload,
        },
    )
    try:
        result = execute_request(
            args.base_url,
            endpoint,
            api_key,
            payload,
            timeout=timeout,
            use_async_jobs=use_async_jobs,
            poll_timeout=args.poll_timeout,
            poll_interval=args.poll_interval,
        )
    except RuntimeError as exc:
        if args.discovery_fallback and endpoint.endswith("advanced"):
            endpoint, payload = build_discovery_request(args)
            use_async_jobs = not args.sync and endpoint in ASYNC_ENDPOINTS
            submitted_endpoint, submitted_payload = build_submitted_request(
                endpoint,
                payload,
                use_async_jobs,
            )
            maybe_save_json(
                args.save_discovery_payload or args.save_payload,
                {
                    "endpoint": submitted_endpoint,
                    "payload": submitted_payload,
                    "target_endpoint": endpoint,
                    "target_payload": payload,
                    "note": f"discovery fallback after advanced query failure: {exc}",
                },
            )
            result = execute_request(
                args.base_url,
                endpoint,
                api_key,
                payload,
                timeout=120,
                use_async_jobs=use_async_jobs,
                poll_timeout=args.poll_timeout,
                poll_interval=args.poll_interval,
            )
        else:
            raise SystemExit(str(exc)) from None
    if (
        not args.skip_details_rerank
        and endpoint.endswith("advanced")
        and payload.get("mode") == "discovery"
        and payload.get("primary_queries")
        and result.get("papers")
    ):
        candidate_ids = [
            paper.get("pmc_id")
            for paper in (result.get("papers") or [])[: max(1, args.details_rerank_limit)]
            if paper.get("pmc_id")
        ]
        if candidate_ids:
            details_payload = {"pmc_ids": candidate_ids}
            details_result = execute_request(
                args.base_url,
                "/api/get_paper_details",
                api_key,
                details_payload,
                timeout=120,
                use_async_jobs=False,
                poll_timeout=args.poll_timeout,
                poll_interval=args.poll_interval,
            )
            maybe_save_json(
                companion_json_path(args.save_payload, "details_payload"),
                {
                    "endpoint": "/api/get_paper_details",
                    "payload": details_payload,
                },
            )
            maybe_save_json(
                companion_json_path(args.save_response, "details_response"),
                details_result,
            )
            triaged_papers = merge_and_rerank_details(
                result,
                details_result,
                payload["primary_queries"],
            )
            result["details_lookup"] = {
                "requested": details_result.get("requested"),
                "found": details_result.get("found"),
                "missing_ids": details_result.get("missing_ids"),
                "candidate_pmc_ids": candidate_ids,
            }
            result["triaged_papers"] = triaged_papers
            result["recommended_next_step"] = recommended_next_step(
                triaged_papers,
                payload["primary_queries"],
            )
    if (
        args.auto_advanced_refinement
        and endpoint.endswith("advanced")
        and payload.get("mode") == "discovery"
        and payload.get("primary_queries")
        and (
            result.get("strategy_used") == "discovery_fallback"
            or result.get("recommended_next_step") == "advanced_refinement_recommended"
        )
    ):
        advanced_payload = dict(payload)
        advanced_payload["mode"] = "advanced"
        advanced_payload["max_results"] = max(
            args.max_results,
            min(args.details_rerank_limit, args.max_results),
        )
        try:
            advanced_result = execute_request(
                args.base_url,
                endpoint,
                api_key,
                advanced_payload,
                timeout=args.timeout or 600,
                use_async_jobs=use_async_jobs,
                poll_timeout=args.poll_timeout,
                poll_interval=args.poll_interval,
            )
            result["advanced_refinement"] = advanced_result
            result["recommended_next_step"] = "advanced_refinement_completed"
            maybe_save_json(
                companion_json_path(args.save_payload, "advanced_payload"),
                {
                    "endpoint": endpoint,
                    "payload": advanced_payload,
                },
            )
            maybe_save_json(
                companion_json_path(args.save_response, "advanced_response"),
                advanced_result,
            )
        except RuntimeError as exc:
            result["advanced_refinement"] = {"error": str(exc)}
            result["recommended_next_step"] = "advanced_refinement_failed"
    if (
        args.discovery_fallback
        and endpoint.endswith("advanced")
        and payload.get("mode") == "discovery"
    ):
        maybe_save_json(args.save_discovery_response or args.save_response, result)
    else:
        maybe_save_json(args.save_response, result)
    if args.raw:
        print(json.dumps(result, indent=2))
        return
    papers = (
        (result.get("advanced_refinement") or {}).get("papers")
        or result.get("triaged_papers")
        or result.get("papers")
        or []
    )
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
        "paper_source": (
            "advanced_refinement"
            if (result.get("advanced_refinement") or {}).get("papers")
            else "details_triage"
            if result.get("triaged_papers")
            else "discovery"
        ),
        "details_lookup": result.get("details_lookup"),
        "advanced_refinement": (
            {
                "strategy_used": (result.get("advanced_refinement") or {}).get("strategy_used"),
                "elapsed_ms": (result.get("advanced_refinement") or {}).get("elapsed_ms"),
                "returned": len((result.get("advanced_refinement") or {}).get("papers") or []),
                "error": (result.get("advanced_refinement") or {}).get("error"),
            }
            if result.get("advanced_refinement") is not None
            else None
        ),
        "recommended_next_step": result.get("recommended_next_step"),
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
