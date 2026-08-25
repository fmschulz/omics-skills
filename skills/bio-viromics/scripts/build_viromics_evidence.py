#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema==4.25.1"]
# ///
"""Validate pinned viromics resources and assemble comparative discovery evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

from jsonschema import ValidationError, validate

METRIC_FIELDS = ("genome", "role", "group", "genome_size", "gene_count", "literature_min", "literature_max", "literature_doi")
HYPOTHESIS_FIELDS = ("hypothesis_id", "hypothesis", "type", "status", "evidence", "revision_stage")
REFLECTION_FIELDS = ("stage", "observed", "qc_status", "hypotheses_gained", "hypotheses_lost", "alternatives", "next_check", "literature_id")
REQUIRED_RESOURCES = {"genomad", "checkv", "gvclass", "vcontact3", "genomad_db", "checkv_db", "gvclass_db", "vcontact3_db"}
COMPARATIVE = ("marker_census.tsv", "family_copy_number_comparison.tsv", "conserved_neighborhoods.tsv", "ncRNA_census.tsv")
SCHEMA = Path(__file__).resolve().parents[1] / "schemas" / "evidence-bundle.schema.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    files = sorted(item for item in path.rglob("*") if item.is_file())
    if not files:
        raise ValueError(f"database directory has no files: {path}")
    for item in files:
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256(item).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def read(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != fields:
            raise ValueError(f"{path}: columns must be exactly {', '.join(fields)}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path}: no rows")
    return rows


def load_resources(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "1.0" or set(data.get("resources", {})) != REQUIRED_RESOURCES:
        raise ValueError("resource manifest must use schema 1.0 and declare all four tools and databases")
    for name, item in data["resources"].items():
        if not item.get("version") or not item.get("sha256"):
            raise ValueError(f"resource {name} requires version and sha256")
        if name.endswith("_db"):
            db = Path(item.get("path", ""))
            db = db if db.is_absolute() else path.parent / db
            kind = item.get("kind", "file")
            if kind == "file":
                if not db.is_file() or db.stat().st_size == 0:
                    raise ValueError(f"database resource file is missing or empty: {db}")
                actual = sha256(db)
            elif kind == "directory":
                if not db.is_dir():
                    raise ValueError(f"database resource directory is missing: {db}")
                actual = tree_sha256(db)
            else:
                raise ValueError(f"database resource kind must be file or directory: {name}")
            if actual != item["sha256"]:
                raise ValueError(f"database checksum mismatch for {name}")
            item["path"] = str(db.resolve())
            item["kind"] = kind
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("metrics", type=Path)
    parser.add_argument("--resources", type=Path, required=True)
    parser.add_argument("--hypotheses", type=Path, required=True)
    parser.add_argument("--reflections", type=Path, required=True)
    parser.add_argument("--comparative-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        metrics = read(args.metrics, METRIC_FIELDS)
        hypotheses = read(args.hypotheses, HYPOTHESIS_FIELDS)
        reflections = read(args.reflections, REFLECTION_FIELDS)
        resources = load_resources(args.resources)
        if len({row["hypothesis_id"] for row in hypotheses}) < 5:
            raise ValueError("at least five distinct hypotheses are required")
        if not any(row["type"] in {"technical", "null"} for row in hypotheses):
            raise ValueError("hypothesis register requires a technical or null explanation")
        stages = [row["stage"] for row in reflections]
        if stages[:1] != ["initial"] or "final" not in stages or len(stages) < 4:
            raise ValueError("reflections must start at initial, include final, and cover at least four stages")
        if any(row["qc_status"] not in {"passed", "failed", "conditional"} for row in reflections):
            raise ValueError("reflection qc_status must be passed, failed, or conditional")
        for name in COMPARATIVE:
            path = args.comparative_dir / name
            if not path.is_file() or path.stat().st_size == 0:
                raise ValueError(f"required comparative artifact is missing or empty: {path}")
        if args.out.exists() and any(args.out.iterdir()):
            raise ValueError(f"output directory is not empty: {args.out}")
        args.out.mkdir(parents=True, exist_ok=True)
        for name in COMPARATIVE:
            shutil.copyfile(args.comparative_dir / name, args.out / name)
        shutil.copyfile(args.hypotheses, args.out / "hypothesis_register.tsv")
        shutil.copyfile(args.reflections, args.out / "intermediate_reflections.tsv")

        by_group: dict[str, list[int]] = {}
        for row in metrics:
            if row["role"] == "reference":
                by_group.setdefault(row["group"], []).append(int(row["genome_size"]))
        frontier = []
        for row in metrics:
            if row["role"] != "query":
                continue
            baseline = sorted(by_group.get(row["group"], []))
            if len(baseline) < 2:
                raise ValueError(f"query {row['genome']} requires at least two same-group references")
            size = int(row["genome_size"])
            percentile = 100 * sum(value <= size for value in baseline) / len(baseline)
            median = (baseline[(len(baseline) - 1) // 2] + baseline[len(baseline) // 2]) / 2
            frontier.append({**row, "relative_percentile": f"{percentile:.1f}", "relative_median": f"{median:g}", "distance_from_median": f"{size - median:g}", "record_class": "above_literature_max" if size > int(row["literature_max"]) else "within_known_range"})
        fields = (*METRIC_FIELDS, "relative_percentile", "relative_median", "distance_from_median", "record_class")
        with (args.out / "genome_size_frontier.tsv").open("x", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(frontier)
        manifest = {"schema_version": "1.0", "resources": resources["resources"], "hypothesis_count": len(hypotheses), "reflection_stages": stages, "comparative_artifacts": list(COMPARATIVE)}
        validate(manifest, json.loads(SCHEMA.read_text(encoding="utf-8")))
        (args.out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        out = args.out.resolve()
        print(json.dumps({"ok": True, "skill": "bio-viromics", "out": str(out), "manifest": str(out / "run_manifest.json"), "warnings": []}))
    except (OSError, ValueError, json.JSONDecodeError, ValidationError) as error:
        print(json.dumps({"ok": False, "skill": "bio-viromics", "error": {"code": type(error).__name__, "message": str(error)}}))
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
