#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema==4.25.1"]
# ///
"""Validate the biological truth-set registry and its cross-record invariants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "truth-sets.json"
DEFAULT_SCHEMA = ROOT / "schemas" / "truth-set-registry.schema.json"
CORE_DRIVERS = {
    "bio-annotation",
    "bio-viromics",
    "bio-interdomain-hgt",
}


def semantic_errors(registry: dict[str, object]) -> list[str]:
    errors: list[str] = []
    drivers = registry.get("drivers", [])
    skills = [driver.get("skill") for driver in drivers]
    if len(skills) != len(set(skills)):
        errors.append("driver skill names must be unique")
    missing = CORE_DRIVERS - set(skills)
    extra = set(skills) - CORE_DRIVERS
    if missing:
        errors.append(f"registry is missing core drivers: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"registry contains non-core drivers: {', '.join(sorted(extra))}")

    truth_set_ids: list[str] = []
    for driver in drivers:
        for truth_set in driver.get("truth_sets", []):
            truth_set_ids.append(truth_set.get("id"))
            metric_names = [metric.get("name") for metric in truth_set.get("metrics", [])]
            if len(metric_names) != len(set(metric_names)):
                errors.append(f"{truth_set.get('id')}: metric names must be unique")
            if "runtime_seconds" not in metric_names or "peak_rss_bytes" not in metric_names:
                errors.append(
                    f"{truth_set.get('id')}: runtime_seconds and peak_rss_bytes are required"
                )
            if truth_set.get("status") == "ready":
                for artifact in truth_set.get("artifacts", []):
                    checksum = artifact.get("checksum", {})
                    if checksum.get("algorithm") != "sha256":
                        errors.append(
                            f"{truth_set.get('id')}/{artifact.get('name')}: ready artifacts require SHA-256"
                        )
    if len(truth_set_ids) != len(set(truth_set_ids)):
        errors.append("truth-set identifiers must be globally unique")
    return errors


def validation_errors(registry_path: Path, schema_path: Path) -> list[str]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = [
        f"{'.'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(registry), key=lambda item: list(item.absolute_path))
    ]
    return errors + semantic_errors(registry)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args()
    try:
        errors = validation_errors(args.registry, args.schema)
    except (OSError, json.JSONDecodeError) as error:
        parser.error(str(error))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    truth_sets = sum(len(driver["truth_sets"]) for driver in registry["drivers"])
    ready = sum(
        truth_set["status"] == "ready"
        for driver in registry["drivers"]
        for truth_set in driver["truth_sets"]
    )
    print(f"OK: {len(registry['drivers'])} drivers, {truth_sets} truth sets, {ready} ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
