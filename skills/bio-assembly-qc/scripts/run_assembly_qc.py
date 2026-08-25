#!/usr/bin/env python3
"""Plan or execute restartable assembly and QUAST/MetaQUAST stages."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

FIELDS = ("sample_id", "mode", "read1", "read2", "read_qc_status")
MODES = {"short_isolate", "long_isolate", "short_metagenome", "long_metagenome", "hifi_metagenome"}


def resolve_file(value: str, base: Path, label: str) -> Path:
    path = Path(value)
    path = path if path.is_absolute() else base / path
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"{label} is missing or empty: {path}")
    return path.resolve()


def load(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError(f"manifest columns must be exactly: {', '.join(FIELDS)}")
        rows = list(reader)
    if not rows:
        raise ValueError("manifest has no assemblies")
    seen: set[str] = set()
    for row in rows:
        sample, mode = row["sample_id"].strip(), row["mode"].strip()
        if not sample or sample in seen:
            raise ValueError(f"sample_id must be non-empty and unique: {sample!r}")
        if mode not in MODES:
            raise ValueError(f"unsupported assembly mode for {sample}: {mode}")
        if row["read_qc_status"].strip() != "passed":
            raise ValueError(f"{sample}: read_qc_status must be passed before assembly")
        seen.add(sample)
        row["sample_id"], row["mode"] = sample, mode
        row["read1"] = str(resolve_file(row["read1"], path.parent, f"{sample} read1"))
        if mode.startswith("short_"):
            row["read2"] = str(resolve_file(row["read2"], path.parent, f"{sample} read2"))
        elif row["read2"].strip():
            raise ValueError(f"{sample}: read2 is not allowed for {mode}")
    return rows


def plan(rows: list[dict[str, str]], out: Path) -> list[dict[str, object]]:
    steps: list[dict[str, object]] = []
    for row in rows:
        sample, mode = row["sample_id"], row["mode"]
        work = out / sample / "assembler"
        normalized = out / sample / "contigs.fasta"
        if mode == "short_isolate":
            command, source = ["spades.py", "-1", row["read1"], "-2", row["read2"], "-o", str(work)], work / "scaffolds.fasta"
        elif mode == "short_metagenome":
            command, source = ["metaspades.py", "-1", row["read1"], "-2", row["read2"], "-o", str(work)], work / "scaffolds.fasta"
        elif mode == "hifi_metagenome":
            command, source = ["metaMDBG", "asm", "--in-hifi", row["read1"], "--out-dir", str(work)], work / "contigs.fasta.gz"
        else:
            command = ["flye", "--nano-hq", row["read1"], "--out-dir", str(work)]
            if mode == "long_metagenome":
                command.append("--meta")
            source = work / "assembly.fasta"
        qc_tool = "metaquast.py" if "metagenome" in mode else "quast.py"
        steps.extend([
            {"sample_id": sample, "stage": "assembly", "command": command, "outputs": [str(source)]},
            {"sample_id": sample, "stage": "normalize", "source": str(source), "outputs": [str(normalized)]},
            {"sample_id": sample, "stage": "qc", "command": [qc_tool, str(normalized), "-o", str(out / sample / "quast")], "outputs": [str(out / sample / "quast" / "report.tsv")]},
        ])
    return steps


def completion_marker(step: dict[str, object]) -> Path:
    return Path(step["outputs"][0]).parent / f"{step['stage']}.done"


def outputs_complete(step: dict[str, object]) -> bool:
    return all(Path(item).is_file() and Path(item).stat().st_size > 0 for item in step["outputs"])


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
        if step["stage"] == "normalize":
            source, target = Path(step["source"]), Path(step["outputs"][0])
            if not source.is_file() or source.stat().st_size == 0:
                raise RuntimeError(f"assembler output is missing or empty: {source}")
            temporary = target.with_suffix(target.suffix + ".tmp")
            if source.suffix == ".gz":
                import gzip
                with gzip.open(source, "rb") as src, temporary.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
            else:
                shutil.copyfile(source, temporary)
            temporary.replace(target)
        else:
            result = subprocess.run(step["command"], check=False)
            if result.returncode:
                raise RuntimeError(f"{step['stage']} command failed with exit {result.returncode}")
        if not outputs_complete(step):
            raise RuntimeError(f"{step['stage']} did not produce all declared outputs")
        mark_complete(step)
        step["status"] = "completed"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        rows = load(args.manifest.resolve())
        args.out.mkdir(parents=True, exist_ok=True)
        steps = plan(rows, args.out.resolve())
        if args.execute:
            execute(steps)
        (args.out / "run_manifest.json").write_text(json.dumps({"schema_version": "1.0", "assemblies": rows, "steps": steps}, indent=2) + "\n")
        out = args.out.resolve()
        print(json.dumps({"ok": True, "skill": "bio-assembly-qc", "out": str(out), "manifest": str(out / "run_manifest.json"), "warnings": []}))
    except (OSError, ValueError, RuntimeError) as error:
        print(json.dumps({"ok": False, "skill": "bio-assembly-qc", "error": {"code": type(error).__name__, "message": str(error)}}))
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
