#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import json
import re
from pathlib import Path
from typing import Any


DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
PMID_RE = re.compile(r"\bPMID[:\s]+(\d{6,9})\b", re.IGNORECASE)
DATASET_SIGNAL_RE = re.compile(
    r"\b(data availability|accession|project id|repository|zenodo|img/m|data portal|sra|geo|pride|available at|downloaded at)\b",
    re.IGNORECASE,
)
FIGURE_SIGNAL_RE = re.compile(
    r"^\s*(fig(?:ure)?\.?|table|supplementary figure|supplementary table)\b",
    re.IGNORECASE,
)

ASSERTION_CRITICALITIES = {"core", "major", "supporting", "background"}
CLAIM_ROLES = {
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
}
NORMALIZATION_STATUSES = {"raw", "partially_normalized", "fully_normalized"}
DECISIVE_POLARITIES = {"supports", "refutes", "mixed"}
POLARITIES = DECISIVE_POLARITIES | {"inconclusive"}
STRENGTH_LEVELS = {"very_strong", "strong", "moderate", "weak", "very_weak", "unknown"}
ADEQUATE_STRENGTH_LEVELS = {"very_strong", "strong", "moderate"}
PROMOTED_CURATION_STATUSES = {"human_verified", "human_corrected"}
ARTIFACT_TYPES = {"figure", "table", "supplementary", "equation", "protocol", "code", "other"}
VALIDATOR_VERSION = "0.6.0"
PROFILE_ALIASES = {
    "candidate": "paper_local",
    "ground_truth": "benchmark_key",
}
PROFILE_CHOICES = ("paper_local", "promoted_claim", "benchmark_key", "candidate", "ground_truth")
ID_LIST_KEYS = (
    "artifacts",
    "datasets",
    "entities",
    "studies",
    "experiments",
    "assertions",
    "evidence_items",
    "evidence_links",
    "inferences",
    "assertion_relations",
    "critiques",
    "knowledge_gaps",
    "qa_items",
    "extraction_activities",
)
ID_PATTERNS = {
    "artifacts": ("artifact", "F"),
    "datasets": ("dataset", "D"),
    "entities": ("entity", "N"),
    "studies": ("study", "S"),
    "experiments": ("experiment", "X"),
    "assertions": ("assertion", "A"),
    "evidence_items": ("evidence", "E"),
    "evidence_links": ("elink", "L"),
    "inferences": ("inference", "I"),
    "assertion_relations": ("relation", "AR"),
    "critiques": ("critique", "R"),
    "knowledge_gaps": ("gap", "G"),
    "qa_items": ("qa", "Q"),
    "extraction_activities": ("activity", "ACT"),
}
CRITICALITY_REPAIRS = {
    "high": "core",
    "medium": "major",
    "moderate": "major",
    "low": "supporting",
    "minor": "supporting",
    "none": "background",
}
FIELD_ALIASES = {
    "evidence_links": {
        "evidence_id": "evidence_item",
        "evidenceItem": "evidence_item",
        "evidenceItemId": "evidence_item",
        "assertion_id": "assertion",
        "assertionId": "assertion",
    },
    "inferences": {
        "output_assertion_id": "output_assertion",
        "outputAssertion": "output_assertion",
        "outputAssertionId": "output_assertion",
    },
    "assertion_relations": {
        "source_assertion": "from_assertion",
        "source_assertion_id": "from_assertion",
        "from_assertion_id": "from_assertion",
        "target_assertion": "to_assertion",
        "target_assertion_id": "to_assertion",
        "to_assertion_id": "to_assertion",
    },
    "datasets": {
        "url": "dataset_url",
        "data_url": "dataset_url",
        "project_id": "accession",
        "accession_id": "accession",
        "database": "repository",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a CSAG PaperExtraction with repo-specific enforcement rules."
    )
    parser.add_argument("extraction_json", type=Path)
    parser.add_argument("--source-markdown", type=Path, default=None)
    parser.add_argument("--article-json", type=Path, default=None)
    parser.add_argument("--report-out", type=Path, required=True)
    parser.add_argument(
        "--profile",
        choices=PROFILE_CHOICES,
        default="paper_local",
        help=(
            "Validation strictness. Use paper_local for extraction outputs, "
            "promoted_claim for curated claims, and benchmark_key for scoring keys. "
            "candidate and ground_truth are legacy aliases."
        ),
    )
    parser.add_argument(
        "--repair-out",
        type=Path,
        default=None,
        help=(
            "Write a mechanically repaired extraction before validation. Repairs are "
            "limited to deterministic schema-shape fixes such as field aliases, enum "
            "aliases, scalar-to-list coercions, missing deterministic IDs, and inferred "
            "artifact types."
        ),
    )
    return parser.parse_args()


def load_json(path: Path | None) -> dict | None:
    if path is None:
        return None
    return json.loads(path.expanduser().resolve().read_text(encoding="utf-8"))


def front_matter_only(markdown: str) -> str:
    if not markdown:
        return ""
    for marker in ("\n# 1 ", "\n# Introduction", "\n## Introduction"):
        idx = markdown.find(marker)
        if idx != -1:
            return markdown[:idx]
    return markdown[:4000]


def collect_parameter_map(extraction: dict) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for activity in extraction.get("extraction_activities", []):
        for item in activity.get("parameters", []):
            key = item.get("key")
            value = item.get("value")
            if isinstance(key, str) and isinstance(value, str):
                mapping[key] = value
    return mapping


def expect(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def issue(object_id: object, field_path: str, reason: str, suggested_fix: str) -> str:
    object_label = object_id if isinstance(object_id, str) and object_id else "(unknown id)"
    return (
        f"object={object_label}; field={field_path}; reason={reason}; "
        f"suggested_fix={suggested_fix}"
    )


def issue_code(reason: str) -> str:
    code = re.sub(r"[^a-z0-9]+", "_", reason.lower()).strip("_")
    return code[:80] or "validation_error"


def structured_issue(message: str) -> dict[str, str]:
    match = re.match(
        r"^object=(?P<object_id>.*?); field=(?P<field_path>.*?); reason=(?P<reason>.*?); suggested_fix=(?P<suggested_fix>.*)$",
        message,
    )
    if not match:
        return {
            "code": issue_code(message),
            "object_id": "",
            "field_path": "",
            "reason": message,
            "suggested_fix": "",
        }
    payload = {key: value.strip() for key, value in match.groupdict().items()}
    payload["code"] = issue_code(payload["reason"])
    return payload


def error_summary(errors: list[str]) -> dict[str, int]:
    counter = Counter(item["code"] for item in (structured_issue(error) for error in errors))
    return dict(sorted(counter.items()))


def repair_doc_id(extraction: dict) -> str:
    doc_id = extraction.get("id")
    if isinstance(doc_id, str) and doc_id:
        return doc_id
    doi = extraction.get("doi")
    if isinstance(doi, str) and doi:
        return f"doi:{doi}"
    pmid = extraction.get("pmid")
    if isinstance(pmid, str) and pmid:
        return f"pmid:{pmid}"
    return "csag:doc/unknown"


def repair_action(actions: list[dict[str, Any]], code: str, path: str, before: Any, after: Any) -> None:
    actions.append({"code": code, "path": path, "before": before, "after": after})


def infer_artifact_type(artifact: dict) -> str:
    text = " ".join(
        str(artifact.get(field) or "")
        for field in ("artifact_type", "artifact_label", "label", "caption", "description")
    ).lower()
    if "table" in text:
        return "table"
    if "supplement" in text:
        return "supplementary"
    if "equation" in text:
        return "equation"
    if "protocol" in text:
        return "protocol"
    if "code" in text or "software" in text:
        return "code"
    if "fig" in text:
        return "figure"
    return "other"


def repair_paper_extraction(extraction: dict) -> tuple[dict, list[dict[str, Any]]]:
    repaired = deepcopy(extraction)
    actions: list[dict[str, Any]] = []
    doc_id = repair_doc_id(repaired)

    for collection, (namespace, prefix) in ID_PATTERNS.items():
        items = repaired.get(collection)
        if not isinstance(items, list):
            continue
        seen = {item.get("id") for item in items if isinstance(item, dict) and isinstance(item.get("id"), str)}
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict) or item.get("id"):
                continue
            candidate_index = index
            while True:
                candidate = f"csag:{namespace}/{doc_id}/{prefix}{candidate_index:04d}"
                if candidate not in seen:
                    break
                candidate_index += 1
            item["id"] = candidate
            seen.add(candidate)
            repair_action(actions, "assign_missing_id", f"{collection}[{index - 1}].id", "", candidate)

    for collection, aliases in FIELD_ALIASES.items():
        items = repaired.get(collection)
        if not isinstance(items, list):
            continue
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            for alias, canonical in aliases.items():
                if not item.get(canonical) and item.get(alias):
                    item[canonical] = item[alias]
                    repair_action(actions, "copy_field_alias", f"{collection}[{index}].{canonical}", alias, canonical)

    for index, assertion in enumerate(repaired.get("assertions", []) or []):
        if not isinstance(assertion, dict):
            continue
        criticality = assertion.get("criticality")
        if isinstance(criticality, str):
            normalized = CRITICALITY_REPAIRS.get(criticality.strip().lower())
            if normalized:
                assertion["criticality"] = normalized
                repair_action(actions, "normalize_criticality", f"assertions[{index}].criticality", criticality, normalized)
        criteria = assertion.get("falsification_criteria")
        if isinstance(criteria, str) and criteria.strip():
            assertion["falsification_criteria"] = [criteria.strip()]
            repair_action(
                actions,
                "coerce_falsification_criteria_list",
                f"assertions[{index}].falsification_criteria",
                criteria,
                assertion["falsification_criteria"],
            )
        contexts = assertion.get("contexts")
        if isinstance(contexts, dict):
            assertion["contexts"] = [contexts]
            repair_action(actions, "coerce_contexts_list", f"assertions[{index}].contexts", "object", "list")

    for index, artifact in enumerate(repaired.get("artifacts", []) or []):
        if not isinstance(artifact, dict):
            continue
        artifact_type = artifact.get("artifact_type")
        if not isinstance(artifact_type, str) or artifact_type not in ARTIFACT_TYPES:
            inferred = infer_artifact_type(artifact)
            artifact["artifact_type"] = inferred
            repair_action(actions, "infer_artifact_type", f"artifacts[{index}].artifact_type", artifact_type, inferred)

    for index, activity in enumerate(repaired.get("extraction_activities", []) or []):
        if not isinstance(activity, dict):
            continue
        parameters = activity.get("parameters")
        if isinstance(parameters, dict):
            converted = [{"key": str(key), "value": str(value)} for key, value in parameters.items()]
            activity["parameters"] = converted
            repair_action(actions, "coerce_parameters_list", f"extraction_activities[{index}].parameters", "object", "list")

    return repaired, actions


def nonempty_string_list(value: object) -> bool:
    return isinstance(value, list) and any(isinstance(item, str) and item.strip() for item in value)


def has_text_spans(item: dict | None) -> bool:
    return bool(isinstance(item, dict) and isinstance(item.get("text_spans"), list) and item.get("text_spans"))


def collect_ids(extraction: dict, errors: list[str]) -> dict[str, set[str]]:
    ids_by_key: dict[str, set[str]] = {}
    for key in ID_LIST_KEYS:
        seen: set[str] = set()
        duplicates: set[str] = set()
        for item in extraction.get(key, []) or []:
            if not isinstance(item, dict):
                continue
            item_id = item.get("id")
            if not isinstance(item_id, str) or not item_id:
                continue
            if item_id in seen:
                duplicates.add(item_id)
            seen.add(item_id)
        if duplicates:
            errors.append(
                issue(
                    ",".join(sorted(duplicates)),
                    key,
                    "duplicate IDs are present",
                    "Rename duplicate objects so every ID is unique within the PaperExtraction.",
                )
            )
        ids_by_key[key] = seen
    return ids_by_key


def expect_required_ref(ref: object, known_ids: set[str], label: str, errors: list[str]) -> None:
    if not isinstance(ref, str) or not ref:
        errors.append(issue(label, label, "required reference is missing", "Populate this field with an ID from the same PaperExtraction."))
        return
    expect(ref in known_ids, issue(ref, label, "reference does not resolve", "Use an ID that exists in the same PaperExtraction."), errors)


def expect_optional_ref(ref: object, known_ids: set[str], message: str, errors: list[str]) -> None:
    if isinstance(ref, str) and ref:
        expect(ref in known_ids, issue(ref, message, "reference does not resolve", "Use an ID that exists in the same PaperExtraction or remove the optional reference."), errors)


def expect_refs(refs: object, known_ids: set[str], message_prefix: str, errors: list[str]) -> None:
    if not isinstance(refs, list):
        return
    for ref in refs:
        if isinstance(ref, str) and ref:
            expect(ref in known_ids, issue(ref, message_prefix, "reference does not resolve", "Use an ID that exists in the same PaperExtraction."), errors)


def validate_nested_artifact_refs(value: object, artifact_ids: set[str], path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        if "artifact_ref" in value:
            expect_optional_ref(
                value.get("artifact_ref"),
                artifact_ids,
                f"{path}.artifact_ref references missing id {value.get('artifact_ref')}",
                errors,
            )
        if "associated_artifacts" in value:
            expect_refs(value.get("associated_artifacts"), artifact_ids, f"{path}.associated_artifacts", errors)
        for key, item in value.items():
            validate_nested_artifact_refs(item, artifact_ids, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            validate_nested_artifact_refs(item, artifact_ids, f"{path}[{index}]", errors)


def is_limitation_or_speculation(assertion: dict) -> bool:
    return assertion.get("claim_role") in {"limitation", "speculation"}


def validate_optional_assertion_metadata(extraction: dict, errors: list[str]) -> None:
    for item in extraction.get("assertions", []) or []:
        if not isinstance(item, dict):
            continue
        criticality = item.get("criticality")
        if criticality is not None:
            expect(
                criticality in ASSERTION_CRITICALITIES,
                issue(
                    item.get("id"),
                    "assertions[].criticality",
                    f"invalid criticality {criticality}",
                    "Use core, major, supporting, or background.",
                ),
                errors,
            )
        falsification_criteria = item.get("falsification_criteria")
        if falsification_criteria is not None:
            expect(
                nonempty_string_list(falsification_criteria),
                issue(
                    item.get("id"),
                    "assertions[].falsification_criteria",
                    "invalid falsification_criteria",
                    "Use a JSON list of one or more concrete falsification criteria strings.",
                ),
                errors,
            )


def validate_cross_references(extraction: dict, ids_by_key: dict[str, set[str]], errors: list[str]) -> None:
    assertion_ids = ids_by_key.get("assertions", set())
    evidence_ids = ids_by_key.get("evidence_items", set())
    evidence_link_ids = ids_by_key.get("evidence_links", set())
    artifact_ids = ids_by_key.get("artifacts", set())
    experiment_ids = ids_by_key.get("experiments", set())

    validate_nested_artifact_refs(extraction, artifact_ids, "paper_extraction", errors)

    for item in extraction.get("evidence_items", []) or []:
        expect_optional_ref(
            item.get("associated_experiment"),
            experiment_ids,
            f"evidence_item {item.get('id')} references missing associated_experiment {item.get('associated_experiment')}",
            errors,
        )

    for item in extraction.get("evidence_links", []) or []:
        expect_required_ref(
            item.get("evidence_item"),
            evidence_ids,
            f"evidence_link {item.get('id')} evidence_item",
            errors,
        )
        expect_required_ref(
            item.get("assertion"),
            assertion_ids,
            f"evidence_link {item.get('id')} assertion",
            errors,
        )

    for item in extraction.get("inferences", []) or []:
        expect_required_ref(
            item.get("output_assertion"),
            assertion_ids,
            f"inference {item.get('id')} output_assertion",
            errors,
        )
        expect_refs(
            item.get("input_assertions"),
            assertion_ids,
            f"inference {item.get('id')} input_assertions",
            errors,
        )
        expect_refs(
            item.get("input_evidence_links"),
            evidence_link_ids,
            f"inference {item.get('id')} input_evidence_links",
            errors,
        )

    for item in extraction.get("assertion_relations", []) or []:
        expect_required_ref(
            item.get("from_assertion"),
            assertion_ids,
            f"assertion_relation {item.get('id')} from_assertion",
            errors,
        )
        expect_required_ref(
            item.get("to_assertion"),
            assertion_ids,
            f"assertion_relation {item.get('id')} to_assertion",
            errors,
        )

    for item in extraction.get("critiques", []) or []:
        expect_refs(
            item.get("impacted_assertions"),
            assertion_ids,
            f"critique {item.get('id')} impacted_assertions",
            errors,
        )
        expect_refs(
            item.get("impacted_evidence_items"),
            evidence_ids,
            f"critique {item.get('id')} impacted_evidence_items",
            errors,
        )

    for item in extraction.get("knowledge_gaps", []) or []:
        expect_refs(
            item.get("related_assertions"),
            assertion_ids,
            f"knowledge_gap {item.get('id')} related_assertions",
            errors,
        )

    for item in extraction.get("qa_items", []) or []:
        expect_optional_ref(
            item.get("query_assertion"),
            assertion_ids,
            f"qa_item {item.get('id')} references missing query_assertion {item.get('query_assertion')}",
            errors,
        )
        for answer in item.get("answers", []) or []:
            expect_refs(
                answer.get("supporting_assertions"),
                assertion_ids,
                f"qa_item {item.get('id')} answer supporting_assertions",
                errors,
            )
            expect_refs(
                answer.get("supporting_evidence_links"),
                evidence_link_ids,
                f"qa_item {item.get('id')} answer supporting_evidence_links",
                errors,
            )


def validate_semantic_field_placement(extraction: dict, errors: list[str]) -> None:
    placement_rules = {
        "polarity": {"evidence_links"},
        "relation_type": {"assertion_relations"},
        "inference_method": {"inferences"},
        "inference_rationale": {"inferences"},
        "input_assertions": {"inferences"},
        "input_evidence_links": {"inferences"},
        "output_assertion": {"inferences"},
    }
    for collection in ID_LIST_KEYS:
        for item in extraction.get(collection, []) or []:
            if not isinstance(item, dict):
                continue
            for field, allowed_collections in placement_rules.items():
                if field in item and collection not in allowed_collections:
                    errors.append(
                        issue(
                            item.get("id"),
                            f"{collection}[].{field}",
                            "semantic field is recorded on the wrong object type",
                            f"Move {field} to {', '.join(sorted(allowed_collections))}.",
                        )
                    )


def validate_promoted_claim_profile(extraction: dict, ids_by_key: dict[str, set[str]], errors: list[str]) -> None:
    review_activities = [
        activity
        for activity in extraction.get("extraction_activities", []) or []
        if isinstance(activity, dict)
        and re.search(r"\b(human review|curation|curator review)\b", str(activity.get("activity_type", "")), re.IGNORECASE)
    ]
    expect(
        bool(review_activities),
        issue(
            extraction.get("id"),
            "extraction_activities[].activity_type",
            "missing promotion review provenance",
            "Record an ExtractionActivity whose activity_type names human review or curation before using the promoted_claim profile.",
        ),
        errors,
    )

    evidence_by_id = {
        item.get("id"): item
        for item in extraction.get("evidence_items", []) or []
        if isinstance(item, dict) and item.get("id")
    }
    links_by_assertion: dict[str, list[dict]] = {}
    for link in extraction.get("evidence_links", []) or []:
        if not isinstance(link, dict):
            continue
        assertion_id = link.get("assertion")
        if isinstance(assertion_id, str):
            links_by_assertion.setdefault(assertion_id, []).append(link)
        expect(
            link.get("strength") in STRENGTH_LEVELS,
            issue(link.get("id"), "evidence_links[].strength", "missing or invalid strength", "Use one of the StrengthLevel values."),
            errors,
        )
        expect(
            bool(link.get("rationale")),
            issue(link.get("id"), "evidence_links[].rationale", "missing rationale", "Explain why this evidence supports, refutes, or qualifies the assertion."),
            errors,
        )
        expect(
            link.get("polarity") in POLARITIES,
            issue(link.get("id"), "evidence_links[].polarity", "invalid polarity", "Use supports, refutes, mixed, or inconclusive."),
            errors,
        )
        expect(
            link.get("curation_status") in PROMOTED_CURATION_STATUSES,
            issue(link.get("id"), "evidence_links[].curation_status", "missing human curation status", "Use human_verified or human_corrected before promoting the link."),
            errors,
        )

    for assertion in extraction.get("assertions", []) or []:
        if not isinstance(assertion, dict):
            continue
        assertion_id = assertion.get("id")
        criticality = assertion.get("criticality")
        links = links_by_assertion.get(assertion_id, [])
        linked_evidence = [evidence_by_id.get(link.get("evidence_item")) for link in links]

        expect(
            criticality in ASSERTION_CRITICALITIES,
            issue(assertion_id, "assertions[].criticality", "missing or invalid criticality", "Use core, major, supporting, or background."),
            errors,
        )
        expect(
            nonempty_string_list(assertion.get("falsification_criteria")),
            issue(assertion_id, "assertions[].falsification_criteria", "missing falsification criteria", "Add at least one concrete observation or analysis that would weaken the claim."),
            errors,
        )
        expect(
            assertion.get("curation_status") in PROMOTED_CURATION_STATUSES,
            issue(assertion_id, "assertions[].curation_status", "missing human curation status", "Use human_verified or human_corrected before promoting the assertion."),
            errors,
        )
        if criticality != "background":
            expect(
                bool(links),
                issue(assertion_id, "evidence_links", "no evidence links target this assertion", "Add at least one EvidenceLink from a supporting or refuting EvidenceItem."),
                errors,
            )
            expect(
                any(link.get("polarity") in DECISIVE_POLARITIES for link in links),
                issue(assertion_id, "evidence_links[].polarity", "no decisive evidence link", "At least one linked evidence item should use supports, refutes, or mixed."),
                errors,
            )
            expect(
                has_text_spans(assertion) or any(has_text_spans(item) for item in linked_evidence),
                issue(assertion_id, "assertions[].text_spans", "missing assertion/evidence grounding", "Add TextSpan grounding on the assertion or one of its linked EvidenceItems."),
                errors,
            )


def validate_benchmark_key_profile(extraction: dict, ids_by_key: dict[str, set[str]], errors: list[str]) -> None:
    validate_promoted_claim_profile(extraction, ids_by_key, errors)

    links_by_assertion: dict[str, list[dict]] = {}
    for link in extraction.get("evidence_links", []) or []:
        if isinstance(link, dict) and isinstance(link.get("assertion"), str):
            links_by_assertion.setdefault(link["assertion"], []).append(link)

    for assertion in extraction.get("assertions", []) or []:
        if not isinstance(assertion, dict):
            continue
        assertion_id = assertion.get("id")
        criticality = assertion.get("criticality")
        links = links_by_assertion.get(assertion_id, [])
        if criticality in {"core", "major"} and not is_limitation_or_speculation(assertion):
            expect(
                any(
                    link.get("polarity") in DECISIVE_POLARITIES
                    and link.get("strength") in ADEQUATE_STRENGTH_LEVELS
                    for link in links
                ),
                issue(assertion_id, "evidence_links[].strength", "core or major assertion has no moderate-or-strong decisive evidence", "Add a decisive EvidenceLink with strength moderate, strong, or very_strong, or lower the assertion criticality if justified."),
                errors,
            )


def main() -> int:
    args = parse_args()
    profile = PROFILE_ALIASES.get(args.profile, args.profile)
    extraction_path = args.extraction_json.expanduser().resolve()
    extraction = load_json(extraction_path)
    article = load_json(args.article_json)
    source_markdown = (
        args.source_markdown.expanduser().resolve().read_text(encoding="utf-8")
        if args.source_markdown
        else ""
    )
    repair_actions: list[dict[str, Any]] = []
    if isinstance(extraction, dict) and args.repair_out:
        extraction, repair_actions = repair_paper_extraction(extraction)
        args.repair_out.expanduser().resolve().write_text(
            json.dumps(extraction, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    errors: list[str] = []
    warnings: list[str] = []

    expect(
        isinstance(extraction, dict),
        issue("(input)", "paper_extraction", "paper extraction is not a JSON object", "Provide a PaperExtraction JSON object."),
        errors,
    )
    if errors:
        return write_report(args.report_out, extraction_path, False, errors, warnings, {}, profile, repair_actions)

    root_id = extraction.get("id") or "(paper extraction)"
    expect(bool(extraction.get("id")), issue(root_id, "id", "missing top-level id", "Set the PaperExtraction document ID."), errors)
    expect(bool(extraction.get("title")), issue(root_id, "title", "missing top-level title", "Set the manuscript title."), errors)
    expect(bool(extraction.get("schema_version")), issue(root_id, "schema_version", "missing schema version", "Set the CSAG schema version used for the extraction."), errors)
    expect(bool(extraction.get("validator_version")), issue(root_id, "validator_version", "missing validator version", "Set the validator version used for the validation report."), errors)
    expect(isinstance(extraction.get("assertions"), list), issue(root_id, "assertions", "missing assertions list", "Add an assertions array, even if empty only for non-paper material."), errors)
    expect(isinstance(extraction.get("evidence_items"), list), issue(root_id, "evidence_items", "missing evidence_items list", "Add an evidence_items array."), errors)
    expect(isinstance(extraction.get("evidence_links"), list), issue(root_id, "evidence_links", "missing evidence_links list", "Add an evidence_links array."), errors)
    expect(isinstance(extraction.get("extraction_activities"), list) and extraction.get("extraction_activities"), issue(root_id, "extraction_activities", "missing extraction activities", "Record at least one extraction activity with DOI/PMID status parameters."), errors)

    ids_by_key = collect_ids(extraction, errors)

    for item in extraction.get("assertions", []):
        assertion_id = item.get("id")
        expect(bool(assertion_id), issue(assertion_id, "assertions[].id", "assertion ID is missing", "Assign a deterministic assertion ID."), errors)
        expect(bool(item.get("assertion_text")), issue(assertion_id, "assertions[].assertion_text", "missing assertion text", "Add the natural-language assertion."), errors)
        expect(bool(item.get("claim_role")), issue(assertion_id, "assertions[].claim_role", "missing claim role", "Set claim_role from the controlled vocabulary."), errors)
        if item.get("claim_role"):
            expect(
                item.get("claim_role") in CLAIM_ROLES,
                issue(assertion_id, "assertions[].claim_role", "invalid claim role", "Set claim_role from the controlled vocabulary."),
                errors,
            )
        expect(bool(item.get("normalization_status")), issue(assertion_id, "assertions[].normalization_status", "missing normalization status", "Set raw, partially_normalized, or fully_normalized."), errors)
        if item.get("normalization_status"):
            expect(
                item.get("normalization_status") in NORMALIZATION_STATUSES,
                issue(assertion_id, "assertions[].normalization_status", "invalid normalization status", "Set raw, partially_normalized, or fully_normalized."),
                errors,
            )
        expect(isinstance(item.get("contexts"), list) and len(item.get("contexts")) >= 1, issue(assertion_id, "assertions[].contexts", "missing contexts", "Attach at least one Context object to every Assertion."), errors)

    for item in extraction.get("evidence_links", []):
        expect(bool(item.get("polarity")), issue(item.get("id"), "evidence_links[].polarity", "missing polarity", "Use supports, refutes, mixed, or inconclusive."), errors)
        if item.get("polarity"):
            expect(
                item.get("polarity") in POLARITIES,
                issue(item.get("id"), "evidence_links[].polarity", "invalid polarity", "Use supports, refutes, mixed, or inconclusive."),
                errors,
            )

    validate_optional_assertion_metadata(extraction, errors)
    validate_semantic_field_placement(extraction, errors)
    validate_cross_references(extraction, ids_by_key, errors)
    if profile == "promoted_claim":
        validate_promoted_claim_profile(extraction, ids_by_key, errors)
    if profile == "benchmark_key":
        validate_benchmark_key_profile(extraction, ids_by_key, errors)

    param_map = collect_parameter_map(extraction)
    source_text = front_matter_only(source_markdown)
    if article is not None:
        source_text += "\n" + article.get("title", "")
        source_text += "\n" + article.get("authors", "")
        source_text += "\n" + article.get("affiliations", "")
        source_text += "\n" + article.get("abstract", "")

    source_doi = DOI_RE.search(source_text)
    source_pmid = PMID_RE.search(source_text)
    doi = extraction.get("doi", "")
    pmid = extraction.get("pmid", "")
    doi_status = param_map.get("doi_status")
    pmid_status = param_map.get("pmid_status")

    if source_doi:
        expect(bool(doi), issue(root_id, "doi", "DOI appears recoverable from the source but extraction.doi is empty", "Populate extraction.doi from the source or remove the incorrect DOI signal from the sidecar."), errors)
    else:
        expect(doi_status in {"resolved", "unresolved"}, issue(root_id, "extraction_activities[].parameters.doi_status", "missing explicit DOI status", "Record doi_status as resolved or unresolved in extraction activity parameters."), errors)
    if doi:
        expect(doi_status in {None, "resolved"}, issue(root_id, "extraction_activities[].parameters.doi_status", "extraction.doi is populated but doi_status is not resolved", "Set doi_status to resolved when extraction.doi is populated."), errors)

    if source_pmid:
        expect(bool(pmid), issue(root_id, "pmid", "PMID appears recoverable from the source but extraction.pmid is empty", "Populate extraction.pmid from the source or remove the incorrect PMID signal from the sidecar."), errors)
    else:
        expect(pmid_status in {"resolved", "unresolved"}, issue(root_id, "extraction_activities[].parameters.pmid_status", "missing explicit PMID status", "Record pmid_status as resolved or unresolved in extraction activity parameters."), errors)
    if pmid:
        expect(pmid_status in {None, "resolved"}, issue(root_id, "extraction_activities[].parameters.pmid_status", "extraction.pmid is populated but pmid_status is not resolved", "Set pmid_status to resolved when extraction.pmid is populated."), errors)

    figure_legends = article.get("figure_legends", []) if isinstance(article, dict) else []
    figure_signals = bool(figure_legends)
    if not figure_signals and source_markdown:
        figure_signals = any(FIGURE_SIGNAL_RE.match(line) for line in source_markdown.splitlines())
    if figure_signals:
        artifacts = extraction.get("artifacts", [])
        expect(isinstance(artifacts, list) and len(artifacts) > 0, issue(root_id, "artifacts", "figure/table captions are present in the source but extraction.artifacts is empty", "Add Artifact entries for source figures or tables, or correct the article sidecar if captions were detected incorrectly."), errors)
        for artifact in artifacts:
            artifact_id = artifact.get("id")
            expect(bool(artifact_id), issue(artifact_id, "artifacts[].id", "artifact ID is missing", "Assign a deterministic Artifact ID."), errors)
            expect(bool(artifact.get("artifact_type")), issue(artifact_id, "artifacts[].artifact_type", "missing artifact type", "Set artifact_type from the controlled vocabulary."), errors)
            if artifact.get("artifact_type"):
                expect(
                    artifact.get("artifact_type") in ARTIFACT_TYPES,
                    issue(artifact_id, "artifacts[].artifact_type", "invalid artifact type", "Use figure, table, supplementary, equation, protocol, code, or other."),
                    errors,
                )
            expect(bool(artifact.get("artifact_label")) or bool(artifact.get("caption")), issue(artifact_id, "artifacts[].artifact_label", "missing artifact label or caption", "Populate artifact_label or caption from the source."), errors)

    dataset_signals = bool(source_markdown and DATASET_SIGNAL_RE.search(source_markdown))
    if dataset_signals:
        datasets = extraction.get("datasets", [])
        expect(isinstance(datasets, list) and len(datasets) > 0, issue(root_id, "datasets", "dataset/data-availability signals are present in the source but extraction.datasets is empty", "Add Dataset entries for accessions or repositories mentioned by the source, or correct the source sidecar if the signal was detected incorrectly."), errors)
        for dataset in datasets:
            dataset_id = dataset.get("id")
            expect(bool(dataset_id), issue(dataset_id, "datasets[].id", "dataset ID is missing", "Assign a deterministic Dataset ID."), errors)
            expect(
                bool(dataset.get("accession")) or bool(dataset.get("repository")) or bool(dataset.get("dataset_url")),
                issue(dataset_id, "datasets[].accession", "missing accession, repository, or dataset URL", "Populate accession, repository, or dataset_url from the source data-availability statement."),
                errors,
            )

    report = {
        "ok": not errors,
        "profile": profile,
        "validator_version": VALIDATOR_VERSION,
        "extraction_json": str(extraction_path),
        "errors": errors,
        "structured_errors": [structured_issue(error) for error in errors],
        "error_summary": error_summary(errors),
        "warnings": warnings,
        "repair_actions": repair_actions,
        "metrics": {
            "assertions": len(extraction.get("assertions", [])),
            "assertions_with_criticality": sum(
                1 for item in extraction.get("assertions", []) if item.get("criticality")
            ),
            "assertions_with_falsification_criteria": sum(
                1 for item in extraction.get("assertions", []) if nonempty_string_list(item.get("falsification_criteria"))
            ),
            "evidence_items": len(extraction.get("evidence_items", [])),
            "evidence_links": len(extraction.get("evidence_links", [])),
            "artifacts": len(extraction.get("artifacts", [])),
            "datasets": len(extraction.get("datasets", [])),
        },
    }
    args.report_out.expanduser().resolve().write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("OK")
    return 0


def write_report(
    report_path: Path,
    extraction_path: Path,
    ok: bool,
    errors: list[str],
    warnings: list[str],
    metrics: dict,
    profile: str = "candidate",
    repair_actions: list[dict[str, Any]] | None = None,
) -> int:
    report = {
        "ok": ok,
        "profile": profile,
        "validator_version": VALIDATOR_VERSION,
        "extraction_json": str(extraction_path),
        "errors": errors,
        "structured_errors": [structured_issue(error) for error in errors],
        "error_summary": error_summary(errors),
        "warnings": warnings,
        "repair_actions": repair_actions or [],
        "metrics": metrics,
    }
    report_path.expanduser().resolve().write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
