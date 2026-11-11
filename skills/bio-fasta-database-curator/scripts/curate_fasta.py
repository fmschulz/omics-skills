#!/usr/bin/env python3
"""Curate FASTA records with deterministic identifiers and audit reports."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FastaRecord:
    source: Path
    index: int
    raw_header: str
    sequence: str


def parse_fasta(path: Path) -> list[FastaRecord]:
    records: list[FastaRecord] = []
    header: str | None = None
    sequence_parts: list[str] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                records.append(
                    FastaRecord(path, len(records) + 1, header, "".join(sequence_parts))
                )
            header = line[1:]
            if not header:
                raise ValueError(f"{path}:{line_number}: empty FASTA header")
            sequence_parts = []
        else:
            if header is None:
                raise ValueError(f"{path}:{line_number}: sequence appears before a header")
            sequence_parts.append(re.sub(r"\s+", "", line).upper())
    if header is not None:
        records.append(FastaRecord(path, len(records) + 1, header, "".join(sequence_parts)))
    for record in records:
        if not record.sequence:
            raise ValueError(f"{path}: record {record.index} ({record.raw_header!r}) has no sequence")
    return records


def normalize_header(raw_header: str, prefix: str | None) -> str:
    normalized = re.sub(r"\s+", "_", raw_header.strip())
    normalized = re.sub(r"[^A-Za-z0-9_.|:-]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized:
        raise ValueError(f"header {raw_header!r} becomes empty after normalization")
    return f"{prefix}|{normalized}" if prefix else normalized


def sequence_digest(sequence: str) -> str:
    return hashlib.sha256(sequence.upper().encode("ascii")).hexdigest()


def output_paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    output = args.output.expanduser().resolve()
    mapping = (args.mapping or output.with_suffix(output.suffix + ".mapping.tsv")).expanduser().resolve()
    report = (args.report or output.with_suffix(output.suffix + ".report.json")).expanduser().resolve()
    if len({output, mapping, report}) != 3:
        raise ValueError("output, mapping, and report paths must be different")
    return output, mapping, report


def curate(args: argparse.Namespace) -> dict[str, object]:
    inputs = [path.expanduser().resolve() for path in args.inputs]
    for path in inputs:
        if not path.is_file():
            raise ValueError(f"input FASTA does not exist: {path}")
    records = [record for path in inputs for record in parse_fasta(path)]
    if not records:
        raise ValueError("input FASTA files contain no records")

    output, mapping_path, report_path = output_paths(args)
    for path in (output, mapping_path, report_path):
        if path.exists():
            raise ValueError(f"refusing to overwrite existing output: {path}")

    seen_ids: dict[str, str] = {}
    seen_sequences: dict[str, str] = {}
    retained: list[tuple[str, str]] = []
    mapping_rows: list[dict[str, object]] = []
    duplicate_counts = {"id": 0, "sequence": 0}

    for global_index, record in enumerate(records, 1):
        curated_id = normalize_header(record.raw_header, args.prefix)
        digest = sequence_digest(record.sequence)
        duplicate_reason = ""
        duplicate_of = ""
        if args.deduplicate in {"id", "both"} and curated_id in seen_ids:
            duplicate_reason = "duplicate_id"
            duplicate_of = seen_ids[curated_id]
            duplicate_counts["id"] += 1
        elif args.deduplicate in {"sequence", "both"} and digest in seen_sequences:
            duplicate_reason = "duplicate_sequence"
            duplicate_of = seen_sequences[digest]
            duplicate_counts["sequence"] += 1

        status = "removed" if duplicate_reason else "retained"
        if not duplicate_reason:
            if curated_id in seen_ids:
                curated_id = f"{curated_id}|record_{global_index}"
            seen_ids[curated_id] = curated_id
            seen_sequences[digest] = curated_id
            retained.append((curated_id, record.sequence))
        mapping_rows.append(
            {
                "source": str(record.source),
                "source_record": record.index,
                "raw_header": record.raw_header,
                "curated_id": curated_id,
                "sequence_sha256": digest,
                "status": status,
                "duplicate_reason": duplicate_reason,
                "duplicate_of": duplicate_of,
            }
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fasta-curator-", dir=output.parent) as tmp_dir:
        tmp_root = Path(tmp_dir)
        staged_fasta = tmp_root / "curated.fasta"
        staged_mapping = tmp_root / "mapping.tsv"
        staged_report = tmp_root / "report.json"
        staged_fasta.write_text(
            "".join(f">{identifier}\n{sequence}\n" for identifier, sequence in retained),
            encoding="utf-8",
        )
        with staged_mapping.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(mapping_rows[0]), delimiter="\t")
            writer.writeheader()
            writer.writerows(mapping_rows)
        report = {
            "inputs": [str(path) for path in inputs],
            "deduplicate": args.deduplicate,
            "input_records": len(records),
            "retained_records": len(retained),
            "removed_records": len(records) - len(retained),
            "duplicates_by_reason": duplicate_counts,
            "total_residues": sum(len(sequence) for _, sequence in retained),
            "output": str(output),
            "mapping": str(mapping_path),
        }
        staged_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        staged_fasta.replace(output)
        staged_mapping.replace(mapping_path)
        staged_report.replace(report_path)
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mapping", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--prefix", help="Optional prefix prepended as PREFIX|header")
    parser.add_argument(
        "--deduplicate",
        choices=("none", "id", "sequence", "both"),
        default="both",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        report = curate(parse_args(argv))
    except (OSError, UnicodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
