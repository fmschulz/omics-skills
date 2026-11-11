#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema>=4,<5", "pyyaml>=6,<7"]
# ///
"""Validate a run manifest (YAML or JSON) against schemas/run-manifest.schema.json.

Usage:
  python scripts/validate_run_manifest.py run_manifest.yaml
"""

import argparse
import json
from pathlib import Path

import jsonschema
import yaml

INCOMPLETE_VALUES = {"", "NOT CAPTURED", "UNKNOWN", "TBD"}
PLACEHOLDER_VALUES = INCOMPLETE_VALUES - {""}


def load_obj(path: Path):
    text = path.read_text()
    if path.suffix.lower() in {'.yml', '.yaml'}:
        return yaml.safe_load(text)
    return json.loads(text)


def require_complete(value, path: str, errors: list[str]) -> None:
    if value is None or (isinstance(value, str) and value.strip().upper() in INCOMPLETE_VALUES):
        errors.append(f"{path} is incomplete")


def placeholder_errors(value: object, path: str = "") -> list[str]:
    """Return one error per string in ``value`` that is a draft placeholder."""
    if isinstance(value, str):
        if value.strip().upper() in PLACEHOLDER_VALUES:
            return [f"{path} is incomplete"]
        return []
    if isinstance(value, dict):
        children = [
            (f"{path}.{key}" if path else str(key), item) for key, item in value.items()
        ]
    elif isinstance(value, list):
        children = [(f"{path}[{index}]", item) for index, item in enumerate(value)]
    else:
        return []
    return [
        error
        for child_path, item in children
        for error in placeholder_errors(item, child_path)
    ]


def semantic_errors(manifest: dict) -> list[str]:
    errors: list[str] = []
    require_complete(manifest.get("run_id"), "run_id", errors)
    require_complete(manifest.get("workflow_summary"), "workflow_summary", errors)
    workflow = manifest.get("workflow") or {}
    require_complete(workflow.get("engine_version"), "workflow.engine_version", errors)
    pipeline = workflow.get("pipeline") or {}
    for key in ("name", "version", "commit_sha", "launch_command"):
        require_complete(pipeline.get(key), f"workflow.pipeline.{key}", errors)
    for index, step in enumerate(manifest.get("steps") or []):
        for key in ("tool", "tool_version", "command"):
            require_complete(step.get(key), f"steps[{index}].{key}", errors)
        if not step.get("inputs"):
            errors.append(f"steps[{index}].inputs is empty")
        if not step.get("outputs"):
            errors.append(f"steps[{index}].outputs is empty")
    if not manifest.get("outputs"):
        errors.append("outputs is empty")
    errors.extend(
        error for error in placeholder_errors(manifest) if error not in errors
    )
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Run manifest in YAML or JSON format")
    return parser


def main():
    args = build_parser().parse_args()

    manifest_path = args.manifest.resolve()
    if not manifest_path.exists():
        raise SystemExit(f"ERROR: Not found: {manifest_path}")

    schema_path = Path(__file__).resolve().parents[1] / 'schemas' / 'run-manifest.schema.json'
    schema = json.loads(schema_path.read_text())

    manifest = load_obj(manifest_path)

    try:
        jsonschema.validate(instance=manifest, schema=schema)
    except jsonschema.ValidationError as e:
        print("VALIDATION FAILED:\n")
        print(e.message)
        if e.path:
            print(f"\nAt: {'/'.join([str(p) for p in e.path])}")
        raise SystemExit(1)

    errors = semantic_errors(manifest)
    if errors:
        print("MANIFEST INCOMPLETE:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Manifest validation passed.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
