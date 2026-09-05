#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema==4.26.0"]
# ///
"""Validate issue records and deterministic artifact paths for a council review."""

import argparse
import json
from pathlib import Path

import jsonschema

DEFAULT_ROLES = {"domain", "methods-statistics", "skeptic"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    schema = json.loads((Path(__file__).parents[1] / "schemas" / "review-bundle.schema.json").read_text())
    bundle = json.loads(args.bundle.read_text())
    try:
        jsonschema.validate(bundle, schema)
    except jsonschema.ValidationError as error:
        parser.error(f"schema validation failed at {'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}")
    root = f"reviews/{bundle['manuscript_slug']}/{bundle['run_id']}"
    expected = {"packet_path": f"{root}/packet.json", "conflicts_path": f"{root}/conflicts.json", "editor_path": f"{root}/editor.json"}
    for field, path in expected.items():
        if bundle[field] != path:
            parser.error(f"{field} must be {path}")
    roles = [report["role"] for report in bundle["reviewer_reports"]]
    if len(roles) != len(set(roles)):
        parser.error("reviewer roles must be unique")
    for report in bundle["reviewer_reports"]:
        expected_path = f"{root}/reviewers/{report['role']}.json"
        if report["path"] != expected_path:
            parser.error(f"reviewer path must be {expected_path}")
    issue_ids = [issue["issue_id"] for issue in bundle["issues"]]
    if len(issue_ids) != len(set(issue_ids)):
        parser.error("issue_id values must be unique")
    # An issue must be attributable to a reviewer who actually reported. Without
    # this, a bundle can credit a finding to a reviewer that never ran.
    known_roles = set(roles)
    for issue in bundle["issues"]:
        unknown = sorted(set(issue["source_roles"]) - known_roles)
        if unknown:
            parser.error(
                f"{issue['issue_id']} cites reviewers absent from reviewer_reports: {', '.join(unknown)}"
            )
    # SKILL.md launches three default reviewers. A smaller council is allowed
    # only when the bundle says why, so a silently truncated review is caught.
    missing_defaults = sorted(DEFAULT_ROLES - known_roles)
    if missing_defaults and not bundle.get("reduced_council_reason", "").strip():
        parser.error(
            f"council is missing default reviewer(s) {', '.join(missing_defaults)}; "
            "record why in reduced_council_reason"
        )
    print("Review bundle validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
