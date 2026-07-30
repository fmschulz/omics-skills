#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema==4.25.1"]
# ///
"""Validate a read sample sheet and build or execute a restartable QC/mapping plan."""

from __future__ import annotations

import argparse
import csv
import json
import shlex
import subprocess
from pathlib import Path

from jsonschema import ValidationError, validate

FIELDS = ("sample_id", "read_type", "read1", "read2", "reference")
READ_TYPES = {"paired_short", "single_short", "long"}
SCHEMA = Path(__file__).resolve().parents[1] / "schemas" / "sample-sheet.schema.json"


def existing_file(value: str, base: Path, label: str) -> Path:
    path = Path(value)
    path = path if path.is_absolute() else base / path
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"{label} is missing or empty: {path}")
    return path.resolve()


def load_samples(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError(f"sample sheet columns must be exactly: {', '.join(FIELDS)}")
        rows = list(reader)
    if not rows:
        raise ValueError("sample sheet has no data rows")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    seen: set[str] = set()
    base = path.parent
    for row in rows:
        validate(row, schema)
        sample = row["sample_id"].strip()
        kind = row["read_type"].strip()
        if not sample or sample in seen:
            raise ValueError(f"sample_id must be non-empty and unique: {sample!r}")
        if kind not in READ_TYPES:
            raise ValueError(f"unsupported read_type for {sample}: {kind}")
        seen.add(sample)
        row["sample_id"] = sample
        row["read_type"] = kind
        row["read1"] = str(existing_file(row["read1"], base, f"{sample} read1"))
        if kind == "paired_short":
            row["read2"] = str(existing_file(row["read2"], base, f"{sample} read2"))
        elif row["read2"].strip():
            raise ValueError(f"{sample}: read2 is only allowed for paired_short")
        if row["reference"].strip():
            row["reference"] = str(existing_file(row["reference"], base, f"{sample} reference"))
    return rows


def build_steps(rows: list[dict[str, str]], out: Path) -> list[dict[str, object]]:
    steps: list[dict[str, object]] = []
    for row in rows:
        sample, kind = row["sample_id"], row["read_type"]
        sample_dir = out / sample
        if kind == "paired_short":
            clean1, clean2 = sample_dir / "reads_R1.fastq", sample_dir / "reads_R2.fastq"
            steps.append({"sample_id": sample, "stage": "qc", "command": ["fastp", "--in1", row["read1"], "--in2", row["read2"], "--out1", str(clean1), "--out2", str(clean2), "--json", str(sample_dir / "fastp.json"), "--html", str(sample_dir / "fastp.html")], "outputs": [str(clean1), str(clean2), str(sample_dir / "fastp.json")]})
            mapped_reads = [clean1, clean2]
        elif kind == "single_short":
            clean1 = sample_dir / "reads.fastq"
            steps.append({"sample_id": sample, "stage": "qc", "command": ["fastp", "--in1", row["read1"], "--out1", str(clean1), "--json", str(sample_dir / "fastp.json"), "--html", str(sample_dir / "fastp.html")], "outputs": [str(clean1), str(sample_dir / "fastp.json")]})
            mapped_reads = [clean1]
        else:
            clean1 = sample_dir / "reads.fastq"
            steps.append({"sample_id": sample, "stage": "qc", "command": ["filtlong", row["read1"]], "stdout": str(clean1), "outputs": [str(clean1)]})
            mapped_reads = [clean1]
        if row["reference"]:
            sam = sample_dir / "mapped.sam"
            if kind == "long":
                command = ["minimap2", "-ax", "map-ont", row["reference"], str(mapped_reads[0])]
            else:
                command = ["bwa-mem2", "mem", row["reference"], *map(str, mapped_reads)]
            steps.append({"sample_id": sample, "stage": "mapping", "command": command, "stdout": str(sam), "outputs": [str(sam)]})
    return steps


def completion_marker(step: dict[str, object]) -> Path:
    return Path(step["outputs"][0]).parent / f"{step['stage']}.done"


def outputs_complete(step: dict[str, object]) -> bool:
    return all(Path(p).is_file() and Path(p).stat().st_size > 0 for p in step["outputs"])


def complete(step: dict[str, object]) -> bool:
    return completion_marker(step).is_file() and outputs_complete(step)


def mark_complete(step: dict[str, object]) -> None:
    marker = completion_marker(step)
    partial = marker.with_suffix(marker.suffix + ".partial")
    partial.write_text("complete\n", encoding="utf-8")
    partial.replace(marker)


def execute(steps: list[dict[str, object]]) -> None:
    for step in steps:
        if complete(step):
            step["status"] = "reused"
            continue
        completion_marker(step).unlink(missing_ok=True)
        for output in step["outputs"]:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
        stdout_path = step.get("stdout")
        with Path(stdout_path).open("wb") if stdout_path else open("/dev/null", "wb") as stdout:
            result = subprocess.run(step["command"], stdout=stdout if stdout_path else None, check=False)
        if result.returncode or not outputs_complete(step):
            raise RuntimeError(f"step failed or produced an empty output: {shlex.join(step['command'])}")
        mark_complete(step)
        step["status"] = "completed"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sample_sheet", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        rows = load_samples(args.sample_sheet.resolve())
        args.out.mkdir(parents=True, exist_ok=True)
        steps = build_steps(rows, args.out.resolve())
        if args.execute:
            execute(steps)
        manifest = {"schema_version": "1.0", "mapping_required": any(r["reference"] for r in rows), "samples": rows, "steps": steps}
        (args.out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        with (args.out / "mapping_stats.tsv").open("w", encoding="utf-8") as handle:
            handle.write("sample_id\tmapping_status\treference\n")
            for row in rows:
                handle.write(f"{row['sample_id']}\t{'planned' if row['reference'] else 'not_requested'}\t{row['reference']}\n")
    except (OSError, ValueError, RuntimeError, ValidationError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
