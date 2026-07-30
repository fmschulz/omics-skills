#!/usr/bin/env python3
"""Create a restartable marker-to-tree plan with checksum and support normalization gates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

MARKER_FIELDS = ("marker_id", "fasta", "sequence_type")
REFERENCE_FIELDS = ("accession", "path", "sha256")
SUPPORT_RE = re.compile(
    r"\)([0-9]+(?:\.[0-9]+)?(?:/[0-9]+(?:\.[0-9]+)?)?)(?=[:;,])"
)


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_tsv(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != fields:
            raise ValueError(f"{path}: columns must be exactly {', '.join(fields)}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path}: no rows")
    return rows


def resolve_inputs(rows: list[dict[str, str]], source: Path, field: str) -> None:
    for row in rows:
        path = Path(row[field])
        path = path if path.is_absolute() else source.parent / path
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"input is missing or empty: {path}")
        row[field] = str(path.resolve())


def normalize_tree(tree: Path, output: Path) -> None:
    labels = SUPPORT_RE.findall(tree.read_text(encoding="utf-8"))
    if not labels:
        raise ValueError(f"no internal support values found in {tree}")
    parsed: list[tuple[int, str, float]] = []
    for node_index, label in enumerate(labels, 1):
        parts = [float(value) for value in label.split("/")]
        if len(parts) == 1:
            parsed.append((node_index, "support", parts[0]))
        elif len(parts) == 2:
            parsed.extend(
                (
                    (node_index, "sh_alrt", parts[0]),
                    (node_index, "ufboot", parts[1]),
                )
            )
        else:
            raise ValueError(f"unsupported internal support label: {label}")
    if any(value < 0 or value > 100 for _, _, value in parsed):
        raise ValueError("tree support values must be within 0..1 or 0..100")
    scales = {}
    for metric in {name for _, name, _ in parsed}:
        values = [value for _, name, value in parsed if name == metric]
        if any(value > 1 for value in values) and any(0 < value < 1 for value in values):
            raise ValueError(f"mixed 0..1 and 0..100 support conventions for {metric}")
        scales[metric] = 1 if max(values) <= 1 else 100
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        handle.write("node_index\tsupport_type\traw_support\tnormalized_support\n")
        for node_index, metric, value in parsed:
            handle.write(f"{node_index}\t{metric}\t{value:g}\t{value / scales[metric]:.6f}\n")


def build_plan(markers: list[dict[str, str]], out: Path, tree_tool: str, seed: int) -> list[dict[str, object]]:
    plan: list[dict[str, object]] = []
    for row in markers:
        marker = row["marker_id"]
        target = out / marker
        alignment, trimmed = target / "alignment.fasta", target / "trimmed.fasta"
        plan.append({"marker_id": marker, "stage": "alignment", "command": ["mafft", "--auto", row["fasta"]], "stdout": str(alignment), "outputs": [str(alignment)]})
        plan.append({"marker_id": marker, "stage": "trimming", "command": ["trimal", "-in", str(alignment), "-out", str(trimmed), "-automated1"], "outputs": [str(trimmed)]})
        if tree_tool == "iqtree3":
            tree = Path(str(trimmed) + ".treefile")
            command = ["iqtree3", "-s", str(trimmed), "-m", "MFP", "-B", "1000", "--alrt", "1000", "-seed", str(seed)]
        else:
            tree = target / "tree.nwk"
            command = ["VeryFastTree", "-boot", "1000", "-seed", str(seed), "-threads", "1"]
            if row["sequence_type"] == "nucleotide":
                command.append("-nt")
            command.append(str(trimmed))
        plan.append({"marker_id": marker, "stage": "tree", "command": command, "stdout": str(tree) if tree_tool == "veryfasttree" else None, "outputs": [str(tree)]})
        plan.append({"marker_id": marker, "stage": "normalize_support", "source": str(tree), "outputs": [str(target / "support.tsv")]})
    return plan


def completion_marker(step: dict[str, object]) -> Path:
    return Path(step["outputs"][0]).parent / f"{step['stage']}.done"


def outputs_complete(step: dict[str, object]) -> bool:
    return all(Path(path).is_file() and Path(path).stat().st_size > 0 for path in step["outputs"])


def complete(step: dict[str, object]) -> bool:
    return completion_marker(step).is_file() and outputs_complete(step)


def mark_complete(step: dict[str, object]) -> None:
    marker = completion_marker(step)
    partial = marker.with_suffix(marker.suffix + ".partial")
    partial.write_text("complete\n", encoding="utf-8")
    partial.replace(marker)


def execute(plan: list[dict[str, object]]) -> None:
    for step in plan:
        if complete(step):
            step["status"] = "reused"
            continue
        completion_marker(step).unlink(missing_ok=True)
        for output in step["outputs"]:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
        if step["stage"] == "normalize_support":
            normalize_tree(Path(step["source"]), Path(step["outputs"][0]))
        else:
            stdout_path = step.get("stdout")
            if stdout_path:
                with Path(stdout_path).open("wb") as handle:
                    result = subprocess.run(step["command"], stdout=handle, check=False)
            else:
                result = subprocess.run(step["command"], check=False)
            if result.returncode:
                raise RuntimeError(f"{step['stage']} command failed with exit {result.returncode}")
        if not outputs_complete(step):
            raise RuntimeError(f"{step['stage']} did not produce its declared output")
        mark_complete(step)
        step["status"] = "completed"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("markers", type=Path, nargs="?")
    parser.add_argument("--references", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--tree-tool", choices=("iqtree3", "veryfasttree"), default="iqtree3")
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--normalize-only", type=Path)
    args = parser.parse_args()
    try:
        if args.normalize_only:
            normalize_tree(args.normalize_only, args.out)
            return 0
        if not args.markers or not args.references or args.seed <= 0:
            raise ValueError("markers, --references, and a positive --seed are required")
        markers = read_tsv(args.markers, MARKER_FIELDS)
        references = read_tsv(args.references, REFERENCE_FIELDS)
        resolve_inputs(markers, args.markers, "fasta")
        resolve_inputs(references, args.references, "path")
        for row in markers:
            if row["sequence_type"] not in {"protein", "nucleotide"}:
                raise ValueError(f"invalid sequence_type for {row['marker_id']}")
        for row in references:
            actual = checksum(Path(row["path"]))
            if actual != row["sha256"]:
                raise ValueError(f"reference checksum mismatch for {row['accession']}: expected {row['sha256']}, got {actual}")
        args.out.mkdir(parents=True, exist_ok=True)
        plan = build_plan(markers, args.out.resolve(), args.tree_tool, args.seed)
        if args.execute:
            execute(plan)
        (args.out / "run_manifest.json").write_text(json.dumps({"schema_version": "1.0", "seed": args.seed, "tree_tool": args.tree_tool, "markers": markers, "references": references, "steps": plan}, indent=2) + "\n")
    except (OSError, ValueError, RuntimeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
