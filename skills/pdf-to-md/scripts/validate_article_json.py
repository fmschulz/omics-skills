#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from article_extraction import default_audit_path


EXPECTED_KEYS = {
    "title": str,
    "authors": str,
    "affiliations": str,
    "abstract": str,
    "main": str,
    "methods": str,
    "figure_legends": list,
    "figure_interpretation": str,
    "references": list,
}

MIN_NONEMPTY_FOR_PAPER = ["title", "authors", "main"]
LIST_FIELDS = ["figure_legends", "references"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an Article-schema JSON file.")
    parser.add_argument("json_path", type=Path)
    parser.add_argument("--scientific-paper", action="store_true")
    parser.add_argument(
        "--section-audit",
        type=Path,
        default=None,
        help="Path to the section audit JSON. Defaults to <stem>.section_audit.json next to the article JSON.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def article_value_populated(value) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value)
    return bool(value)


def inferred_default_audit_path(json_path: Path) -> Path:
    if json_path.name.endswith(".article.json"):
        return json_path.with_name(json_path.name[: -len(".article.json")] + ".section_audit.json")
    return default_audit_path(json_path.with_suffix(".md"))


def validate_against_audit(data: dict, audit: dict) -> list[str]:
    errors: list[str] = []
    field_audit = audit.get("field_audit", {})
    for field, info in field_audit.items():
        expected = bool(info.get("expected"))
        if not expected:
            continue
        if field not in data:
            errors.append(f"{field} is expected by section audit but is missing from article JSON")
            continue
        if not article_value_populated(data[field]):
            errors.append(f"{field} is expected by section audit but is empty")

    for field in ("figure_legends", "references"):
        info = field_audit.get(field, {})
        expected_count = int(info.get("count", 0) or 0)
        actual_count = len(data.get(field, []))
        if expected_count and actual_count < expected_count:
            errors.append(f"{field} has {actual_count} entries but section audit found {expected_count}")

    return errors


def main() -> int:
    args = parse_args()
    json_path = args.json_path.expanduser().resolve()
    data = load_json(json_path)

    errors: list[str] = []
    keys = set(data.keys())
    expected = set(EXPECTED_KEYS.keys())

    missing = sorted(expected - keys)
    extra = sorted(keys - expected)
    if missing:
        errors.append(f"missing keys: {missing}")
    if extra:
        errors.append(f"extra keys: {extra}")

    for key, expected_type in EXPECTED_KEYS.items():
        if key not in data:
            continue
        if not isinstance(data[key], expected_type):
            errors.append(f"{key} has wrong type: expected {expected_type.__name__}, got {type(data[key]).__name__}")
            continue
        if key in LIST_FIELDS and any(not isinstance(item, str) for item in data[key]):
            errors.append(f"{key} must contain only strings")

    if args.scientific_paper:
        for key in MIN_NONEMPTY_FOR_PAPER:
            if isinstance(data.get(key), str) and not data[key].strip():
                errors.append(f"{key} is empty but is expected to be populated for a scientific paper")

        audit_path = args.section_audit.expanduser().resolve() if args.section_audit else inferred_default_audit_path(json_path)
        if not audit_path.exists():
            errors.append(f"section audit is required for scientific-paper validation but was not found: {audit_path}")
        else:
            audit = load_json(audit_path)
            errors.extend(validate_against_audit(data, audit))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
