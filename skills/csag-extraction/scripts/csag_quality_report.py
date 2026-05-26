#!/usr/bin/env python3
"""CSAG quality report.

Reads a `paper_extraction.json` (CSAG `PaperExtraction`) and prints a quality
report covering coverage, grounding, normalization, and structural integrity.
Optionally writes the same report to a JSON file for downstream tooling.

This is complementary to `validate_paper_extraction.py`:
- `validate_paper_extraction.py` enforces correctness (errors fail the run).
- `csag_quality_report.py` summarizes shape, coverage, and gaps without failing.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

WORD_RE = re.compile(r"\w+", re.UNICODE)
DATASET_SIGNAL_RE = re.compile(
    r"\b(data availability|accession|project id|repository|zenodo|img/m|data portal|sra|geo|pride|available at|downloaded at)\b",
    re.IGNORECASE,
)
FIGURE_SIGNAL_RE = re.compile(
    r"^\s*(fig(?:ure)?\.?|table|supplementary figure|supplementary table)\b",
    re.IGNORECASE | re.MULTILINE,
)

ASSERTION_CRITICALITIES = ("core", "major", "supporting", "background")
CLAIM_ROLES = (
    "background",
    "hypothesis",
    "research_question",
    "objective",
    "method_claim",
    "result_claim",
    "conclusion",
    "discovery",
    "speculation",
    "limitation",
    "future_work",
)
NORMALIZATION_STATUSES = ("raw", "partially_normalized", "fully_normalized")
POLARITIES = ("supports", "refutes", "mixed", "inconclusive")
STRENGTHS = ("very_strong", "strong", "moderate", "weak", "very_weak", "unknown")
SECTION_TYPES = (
    "title",
    "abstract",
    "introduction",
    "methods",
    "results",
    "discussion",
    "conclusion",
    "supplementary",
    "figure_caption",
    "table_caption",
    "other",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report CSAG quality stats for a PaperExtraction.")
    parser.add_argument("extraction_json", type=Path, help="Path to paper_extraction.json")
    parser.add_argument(
        "--source-markdown",
        type=Path,
        default=None,
        help="Optional canonical Markdown to count words per section.",
    )
    parser.add_argument(
        "--article-json",
        type=Path,
        default=None,
        help="Optional article sidecar to detect figure/table and dataset signals.",
    )
    parser.add_argument(
        "--report-out",
        type=Path,
        default=None,
        help="Optional path to write the JSON report.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when structural issues are detected.",
    )
    return parser.parse_args()


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text or ""))


def count_words_per_section(markdown: str) -> dict[str, int]:
    """Group word counts by `## heading` blocks. Headings before the first `##` go to `_preamble`."""
    counts: dict[str, int] = {}
    if not markdown:
        return counts
    current = "_preamble"
    buffer: list[str] = []
    for line in markdown.splitlines():
        match = re.match(r"^##+\s+(.+?)\s*$", line.strip())
        if match:
            counts[current] = counts.get(current, 0) + count_words("\n".join(buffer))
            buffer = []
            current = match.group(1).strip()
            continue
        buffer.append(line)
    counts[current] = counts.get(current, 0) + count_words("\n".join(buffer))
    return {key: value for key, value in counts.items() if value > 0}


def safe_list(extraction: dict, key: str) -> list[dict]:
    items = extraction.get(key)
    return items if isinstance(items, list) else []


def value_distribution(items: list[dict], field: str, allowed: tuple[str, ...]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for item in items:
        if not isinstance(item, dict):
            continue
        value = item.get(field)
        if isinstance(value, str):
            counter[value] += 1
    return {key: counter.get(key, 0) for key in allowed} | {
        f"_other:{name}": counter[name]
        for name in counter
        if name not in allowed
    }


def text_span_coverage(items: list[dict]) -> dict[str, int]:
    grounded = sum(
        1
        for item in items
        if isinstance(item, dict) and isinstance(item.get("text_spans"), list) and item.get("text_spans")
    )
    return {"with_text_spans": grounded, "without_text_spans": len(items) - grounded}


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def text_word_count(value: Any) -> int:
    if isinstance(value, str):
        return count_words(value)
    if isinstance(value, list):
        return sum(text_word_count(item) for item in value)
    if isinstance(value, dict):
        return sum(text_word_count(item) for item in value.values())
    return 0


def json_text_blob(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(json_text_blob(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(json_text_blob(item) for item in value.values())
    return str(value)


def article_signals(article_json: dict | None, source_markdown: str | None) -> dict[str, bool]:
    article_text = json_text_blob(article_json)
    source_text = source_markdown or ""
    combined = "\n".join([article_text, source_text])
    figure_legend_count = 0
    if isinstance(article_json, dict):
        legends = article_json.get("figure_legends")
        if isinstance(legends, list):
            figure_legend_count += len([item for item in legends if has_value(item)])
        tables = article_json.get("tables")
        if isinstance(tables, list):
            figure_legend_count += len([item for item in tables if has_value(item)])
    return {
        "figure_or_table_caption_present": bool(figure_legend_count or FIGURE_SIGNAL_RE.search(combined)),
        "dataset_signal_present": bool(DATASET_SIGNAL_RE.search(combined)),
    }


FIELD_PROFILES: dict[str, dict[str, tuple[str, ...]]] = {
    "assertions": {
        "required": ("id", "assertion_text", "claim_role", "normalization_status", "contexts"),
        "recommended": ("assertion_type", "criticality", "falsification_criteria", "text_spans"),
    },
    "evidence_items": {
        "required": ("id", "evidence_type"),
        "recommended": ("evidence_text", "contexts", "text_spans"),
    },
    "evidence_links": {
        "required": ("id", "evidence_item", "assertion", "polarity"),
        "recommended": ("strength", "rationale", "text_spans"),
    },
    "inferences": {
        "required": ("id", "output_assertion", "inference_method"),
        "recommended": ("input_assertions", "input_evidence_links", "inference_rationale", "text_spans"),
    },
    "critiques": {
        "required": ("id",),
        "recommended": ("critique_type", "risk_domain", "severity", "impacted_assertions", "text_spans"),
    },
    "knowledge_gaps": {
        "required": ("id",),
        "recommended": ("gap_type", "severity", "related_assertions", "suggested_actions", "text_spans"),
    },
    "artifacts": {
        "required": ("id", "artifact_type", "artifact_label"),
        "recommended": ("caption", "text_spans"),
    },
    "datasets": {
        "required": ("id",),
        "recommended": ("accession", "repository", "dataset_url", "text_spans"),
    },
    "qa_items": {
        "required": ("id", "question_text", "expected_answer_type", "answers"),
        "recommended": ("query_assertion", "normalized_query"),
    },
}

TEXT_FIELDS = {
    "assertions": ("assertion_text",),
    "evidence_items": ("evidence_text",),
    "evidence_links": ("rationale",),
    "inferences": ("inference_rationale",),
}


def field_quality_report(extraction: dict) -> dict:
    collections: dict[str, dict] = {}
    total_required = 0
    missing_required = 0
    total_recommended = 0
    missing_recommended = 0
    weak_text_values: list[dict[str, str]] = []

    for collection, profile in FIELD_PROFILES.items():
        items = safe_list(extraction, collection)
        required = profile["required"]
        recommended = profile["recommended"]
        required_missing_by_field = Counter()
        recommended_missing_by_field = Counter()
        object_reports = []
        for item in items:
            item_id = str(item.get("id") or "(missing id)")
            missing_req = [field for field in required if not has_value(item.get(field))]
            missing_rec = [field for field in recommended if not has_value(item.get(field))]
            for field in missing_req:
                required_missing_by_field[field] += 1
            for field in missing_rec:
                recommended_missing_by_field[field] += 1
            for field in TEXT_FIELDS.get(collection, ()):
                if has_value(item.get(field)) and text_word_count(item.get(field)) < 5:
                    weak_text_values.append(
                        {
                            "object_id": item_id,
                            "field": f"{collection}.{field}",
                            "reason": "text is very short and may be under-informative",
                        }
                    )
            object_reports.append(
                {
                    "id": item_id,
                    "missing_required": missing_req,
                    "missing_recommended": missing_rec,
                }
            )
        collection_required = len(items) * len(required)
        collection_recommended = len(items) * len(recommended)
        collection_missing_required = sum(required_missing_by_field.values())
        collection_missing_recommended = sum(recommended_missing_by_field.values())
        total_required += collection_required
        missing_required += collection_missing_required
        total_recommended += collection_recommended
        missing_recommended += collection_missing_recommended
        denominator = collection_required + collection_recommended
        score = 1.0
        if denominator:
            score = 1 - ((collection_missing_required * 1.0 + collection_missing_recommended * 0.5) / denominator)
        collections[collection] = {
            "object_count": len(items),
            "required_fields": list(required),
            "recommended_fields": list(recommended),
            "missing_required_by_field": dict(required_missing_by_field),
            "missing_recommended_by_field": dict(recommended_missing_by_field),
            "objects_with_missing_required": [
                item for item in object_reports if item["missing_required"]
            ],
            "objects_with_missing_recommended": [
                item for item in object_reports if item["missing_recommended"]
            ],
            "field_completeness_score": round(max(0.0, min(1.0, score)), 3),
        }

    denominator = total_required + total_recommended
    overall = 1.0 if not denominator else 1 - ((missing_required * 1.0 + missing_recommended * 0.5) / denominator)
    return {
        "overall_field_completeness_score": round(max(0.0, min(1.0, overall)), 3),
        "missing_required_field_count": missing_required,
        "missing_recommended_field_count": missing_recommended,
        "weak_text_values": weak_text_values,
        "collections": collections,
    }


def completeness_report(extraction: dict, counts: dict, coverage: dict, signals: dict, word_counts: dict[str, int]) -> dict:
    total_words = sum(word_counts.values())
    compact_source = bool(total_words and total_words < 1500)
    assertions = safe_list(extraction, "assertions")
    roles = Counter(item.get("claim_role") for item in assertions if isinstance(item, dict))
    result_roles = roles["result_claim"] + roles["conclusion"] + roles["discovery"]
    objective_roles = roles["hypothesis"] + roles["research_question"] + roles["objective"]
    result_target = 1 if compact_source else 2
    evidence_target = 1 if compact_source else 2
    checks = [
        {
            "name": "objective_or_question_assertion",
            "status": "pass" if objective_roles >= 1 else "warn",
            "observed": objective_roles,
            "target": 1,
            "reason": "hypothesis, research question, or objective assertion coverage",
            "suggested_fix": "Add an objective/research-question assertion, or state in notes that the source lacks one.",
        },
        {
            "name": "result_or_conclusion_assertions",
            "status": "pass" if result_roles >= result_target else "warn",
            "observed": result_roles,
            "target": result_target,
            "reason": "result/conclusion claim coverage",
            "suggested_fix": "Extract additional result or conclusion assertions from distinct manuscript sections when present.",
        },
        {
            "name": "evidence_items",
            "status": "pass" if counts["evidence_items"] >= evidence_target else "warn",
            "observed": counts["evidence_items"],
            "target": evidence_target,
            "reason": "evidence item coverage",
            "suggested_fix": "Add evidence items for the main analyses, observations, or cited support.",
        },
        {
            "name": "evidence_links",
            "status": "pass" if counts["evidence_links"] >= evidence_target else "warn",
            "observed": counts["evidence_links"],
            "target": evidence_target,
            "reason": "claim-to-evidence linkage",
            "suggested_fix": "Link each key assertion to supporting, refuting, mixed, or inconclusive evidence.",
        },
        {
            "name": "assertion_contexts",
            "status": "pass" if coverage["assertions_missing_context"] == 0 else "fail",
            "observed": coverage["assertions_with_context"],
            "target": coverage["assertions"],
            "reason": "every assertion needs at least one context",
            "suggested_fix": "Attach a Context object to each assertion.",
        },
        {
            "name": "falsification_criteria",
            "status": "pass" if coverage["assertions_with_falsification_criteria"] >= max(1, result_target) else "warn",
            "observed": coverage["assertions_with_falsification_criteria"],
            "target": max(1, result_target),
            "reason": "core or major claims should say what would weaken them",
            "suggested_fix": "Add falsification criteria to core and major assertions.",
        },
        {
            "name": "artifacts_from_captions",
            "status": "pass" if not signals["figure_or_table_caption_present"] or counts["artifacts"] > 0 else "fail",
            "observed": counts["artifacts"],
            "target": 1 if signals["figure_or_table_caption_present"] else 0,
            "reason": "figure/table captions in source should be represented as artifacts",
            "suggested_fix": "Add Artifact objects for detected figures, tables, and supplements.",
        },
        {
            "name": "datasets_from_availability_signals",
            "status": "pass" if not signals["dataset_signal_present"] or counts["datasets"] > 0 else "fail",
            "observed": counts["datasets"],
            "target": 1 if signals["dataset_signal_present"] else 0,
            "reason": "data-availability or accession signals should be represented as datasets",
            "suggested_fix": "Add Dataset objects for repository links, accessions, project IDs, and availability statements.",
        },
    ]
    passed = sum(1 for item in checks if item["status"] == "pass")
    return {
        "document_scope": "compact_or_toy" if compact_source else "full_or_unknown",
        "source_word_count": total_words,
        "score": round(passed / len(checks), 3) if checks else 1.0,
        "checks": checks,
    }


def text_span_section_distribution(extraction: dict) -> dict[str, int]:
    counter: Counter[str] = Counter()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            spans = node.get("text_spans")
            if isinstance(spans, list):
                for span in spans:
                    if isinstance(span, dict):
                        section = span.get("section_type") or "unknown"
                        counter[section] += 1
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(extraction)
    return dict(counter)


def collect_ids(items: list[dict]) -> set[str]:
    return {
        item["id"]
        for item in items
        if isinstance(item, dict) and isinstance(item.get("id"), str) and item["id"]
    }


def assertion_evidence_coverage(extraction: dict) -> dict[str, int]:
    assertions = safe_list(extraction, "assertions")
    links = safe_list(extraction, "evidence_links")
    by_assertion: dict[str, list[dict]] = {}
    for link in links:
        if isinstance(link, dict) and isinstance(link.get("assertion"), str):
            by_assertion.setdefault(link["assertion"], []).append(link)

    with_links = sum(1 for assertion in assertions if assertion.get("id") in by_assertion)
    decisive_polarities = {"supports", "refutes", "mixed"}
    with_decisive = sum(
        1
        for assertion in assertions
        if any(
            link.get("polarity") in decisive_polarities
            for link in by_assertion.get(assertion.get("id"), [])
        )
    )
    return {
        "assertions": len(assertions),
        "with_evidence_links": with_links,
        "without_evidence_links": len(assertions) - with_links,
        "with_decisive_evidence": with_decisive,
    }


def evidence_link_orphans(extraction: dict) -> dict[str, int]:
    assertion_ids = collect_ids(safe_list(extraction, "assertions"))
    evidence_ids = collect_ids(safe_list(extraction, "evidence_items"))
    dangling_assertion = 0
    dangling_evidence = 0
    for link in safe_list(extraction, "evidence_links"):
        if not isinstance(link, dict):
            continue
        if isinstance(link.get("assertion"), str) and link["assertion"] not in assertion_ids:
            dangling_assertion += 1
        if isinstance(link.get("evidence_item"), str) and link["evidence_item"] not in evidence_ids:
            dangling_evidence += 1
    return {
        "evidence_links_with_unknown_assertion": dangling_assertion,
        "evidence_links_with_unknown_evidence_item": dangling_evidence,
    }


def assertions_with_falsification(extraction: dict) -> int:
    return sum(
        1
        for assertion in safe_list(extraction, "assertions")
        if isinstance(assertion.get("falsification_criteria"), list)
        and any(isinstance(item, str) and item.strip() for item in assertion["falsification_criteria"])
    )


def context_coverage(extraction: dict) -> dict[str, int]:
    assertions = safe_list(extraction, "assertions")
    with_context = sum(
        1
        for assertion in assertions
        if isinstance(assertion.get("contexts"), list) and len(assertion["contexts"]) >= 1
    )
    return {
        "assertions_with_context": with_context,
        "assertions_missing_context": len(assertions) - with_context,
    }


def build_report(extraction: dict, source_markdown: str | None, article_json: dict | None = None) -> dict:
    assertions = safe_list(extraction, "assertions")
    evidence_items = safe_list(extraction, "evidence_items")
    evidence_links = safe_list(extraction, "evidence_links")

    counts = {
        "artifacts": len(safe_list(extraction, "artifacts")),
        "datasets": len(safe_list(extraction, "datasets")),
        "entities": len(safe_list(extraction, "entities")),
        "studies": len(safe_list(extraction, "studies")),
        "experiments": len(safe_list(extraction, "experiments")),
        "assertions": len(assertions),
        "evidence_items": len(evidence_items),
        "evidence_links": len(evidence_links),
        "inferences": len(safe_list(extraction, "inferences")),
        "assertion_relations": len(safe_list(extraction, "assertion_relations")),
        "critiques": len(safe_list(extraction, "critiques")),
        "knowledge_gaps": len(safe_list(extraction, "knowledge_gaps")),
        "qa_items": len(safe_list(extraction, "qa_items")),
    }

    distributions = {
        "claim_role": value_distribution(assertions, "claim_role", CLAIM_ROLES),
        "criticality": value_distribution(assertions, "criticality", ASSERTION_CRITICALITIES),
        "normalization_status": value_distribution(assertions, "normalization_status", NORMALIZATION_STATUSES),
        "evidence_polarity": value_distribution(evidence_links, "polarity", POLARITIES),
        "evidence_strength": value_distribution(evidence_links, "strength", STRENGTHS),
    }

    grounding = {
        "assertions": text_span_coverage(assertions),
        "evidence_items": text_span_coverage(evidence_items),
        "evidence_links": text_span_coverage(evidence_links),
        "text_spans_by_section": text_span_section_distribution(extraction),
    }

    coverage = {
        **assertion_evidence_coverage(extraction),
        **context_coverage(extraction),
        "assertions_with_falsification_criteria": assertions_with_falsification(extraction),
    }

    structural = evidence_link_orphans(extraction)

    word_counts = count_words_per_section(source_markdown) if source_markdown else {}
    signals = article_signals(article_json, source_markdown)
    completeness = completeness_report(extraction, counts, coverage, signals, word_counts)
    field_quality = field_quality_report(extraction)
    missing_or_weak = [
        {
            "category": item["name"],
            "severity": "error" if item["status"] == "fail" else "warning",
            "reason": item["reason"],
            "observed": item["observed"],
            "target": item["target"],
            "suggested_fix": item["suggested_fix"],
        }
        for item in completeness["checks"]
        if item["status"] != "pass"
    ]
    for collection, info in field_quality["collections"].items():
        for item in info["objects_with_missing_required"]:
            missing_or_weak.append(
                {
                    "category": "field_quality",
                    "severity": "error",
                    "object_id": item["id"],
                    "field": collection,
                    "reason": f"missing required fields: {', '.join(item['missing_required'])}",
                    "suggested_fix": "Populate required fields from the manuscript or remove unsupported objects.",
                }
            )
        if info["missing_recommended_by_field"]:
            missing_or_weak.append(
                {
                    "category": "field_quality",
                    "severity": "warning",
                    "field": collection,
                    "reason": f"missing recommended fields: {dict(info['missing_recommended_by_field'])}",
                    "suggested_fix": "Improve grounding, criticality, rationale, and provenance fields where the manuscript supports them.",
                }
            )

    issues: list[str] = []
    if coverage["assertions_missing_context"]:
        issues.append(
            f"{coverage['assertions_missing_context']} assertion(s) missing required Context"
        )
    if structural["evidence_links_with_unknown_assertion"]:
        issues.append(
            f"{structural['evidence_links_with_unknown_assertion']} evidence_link(s) point to unknown assertion ids"
        )
    if structural["evidence_links_with_unknown_evidence_item"]:
        issues.append(
            f"{structural['evidence_links_with_unknown_evidence_item']} evidence_link(s) point to unknown evidence_item ids"
        )
    for item in missing_or_weak:
        if item["severity"] == "error":
            issues.append(
                f"{item['category']}: {item['reason']} (suggested fix: {item['suggested_fix']})"
            )

    return {
        "extraction_id": extraction.get("id"),
        "title": extraction.get("title"),
        "doi": extraction.get("doi"),
        "pmid": extraction.get("pmid"),
        "counts": counts,
        "distributions": distributions,
        "grounding": grounding,
        "coverage": coverage,
        "completeness": completeness,
        "missing_or_weak": missing_or_weak,
        "field_quality": field_quality,
        "source_signals": signals,
        "structural_issues": structural,
        "section_word_counts": word_counts,
        "issues": issues,
    }


def render_text(report: dict) -> str:
    lines: list[str] = []
    lines.append("CSAG quality report")
    lines.append(f"  id:    {report.get('extraction_id')}")
    lines.append(f"  title: {report.get('title')}")
    lines.append(f"  doi:   {report.get('doi')}")
    lines.append(f"  pmid:  {report.get('pmid')}")
    lines.append("")
    lines.append("Counts:")
    for key, value in report["counts"].items():
        lines.append(f"  {key:<22} {value}")
    lines.append("")
    lines.append("Coverage:")
    for key, value in report["coverage"].items():
        lines.append(f"  {key:<40} {value}")
    lines.append("")
    lines.append("Completeness:")
    completeness = report.get("completeness", {})
    lines.append(f"  document_scope: {completeness.get('document_scope')}")
    lines.append(f"  score:          {completeness.get('score')}")
    for item in completeness.get("checks", []):
        status = item.get("status", "unknown")
        lines.append(
            f"  {item.get('name', ''):<36} {status:<5} "
            f"{item.get('observed')}/{item.get('target')}"
        )
    lines.append("")
    lines.append("Field quality:")
    field_quality = report.get("field_quality", {})
    lines.append(f"  overall_field_completeness_score: {field_quality.get('overall_field_completeness_score')}")
    lines.append(f"  missing_required_field_count:     {field_quality.get('missing_required_field_count')}")
    lines.append(f"  missing_recommended_field_count:  {field_quality.get('missing_recommended_field_count')}")
    for name, info in field_quality.get("collections", {}).items():
        if info.get("object_count"):
            lines.append(
                f"  {name:<22} score={info.get('field_completeness_score')} "
                f"objects={info.get('object_count')}"
            )
    lines.append("")
    if report.get("missing_or_weak"):
        lines.append("Missing or weak coverage:")
        for item in report["missing_or_weak"]:
            subject = item.get("object_id") or item.get("field") or item.get("category")
            lines.append(f"  - [{item.get('severity')}] {subject}: {item.get('reason')}")
        lines.append("")
    lines.append("Distributions:")
    for name, distribution in report["distributions"].items():
        active = {k: v for k, v in distribution.items() if v}
        rendered = ", ".join(f"{k}={v}" for k, v in active.items()) or "(empty)"
        lines.append(f"  {name:<22} {rendered}")
    lines.append("")
    lines.append("Grounding:")
    for category, info in report["grounding"].items():
        lines.append(f"  {category}: {info}")
    lines.append("")
    if report["section_word_counts"]:
        lines.append("Section word counts (from --source-markdown):")
        for section, count in sorted(report["section_word_counts"].items(), key=lambda item: -item[1]):
            lines.append(f"  {section:<40} {count}")
        lines.append("")
    if report["issues"]:
        lines.append("Issues:")
        for issue in report["issues"]:
            lines.append(f"  - {issue}")
    else:
        lines.append("Issues: none detected")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    extraction_path = args.extraction_json.expanduser().resolve()
    extraction = json.loads(extraction_path.read_text(encoding="utf-8"))
    if not isinstance(extraction, dict):
        print("ERROR: extraction JSON is not an object", file=sys.stderr)
        return 2

    markdown = None
    if args.source_markdown:
        markdown = args.source_markdown.expanduser().resolve().read_text(encoding="utf-8")

    article_json = None
    if args.article_json:
        article_json = json.loads(args.article_json.expanduser().resolve().read_text(encoding="utf-8"))

    report = build_report(extraction, markdown, article_json)
    print(render_text(report))

    if args.report_out:
        out_path = args.report_out.expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"\nreport={out_path}")

    if args.strict and report["issues"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
