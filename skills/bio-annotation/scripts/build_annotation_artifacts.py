#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema==4.25.1", "polars==1.37.1"]
# ///
"""Normalize annotation records and build marker, family, routing, and discovery artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

import polars as pl
from jsonschema import ValidationError, validate

ANNOTATION_FIELDS = ("genome", "protein_id", "family_id", "family_name", "category", "e_value", "annotation", "taxonomy", "confidence")
GENOME_FIELDS = ("genome", "role", "domain", "route")
MARKER_FIELDS = ("category", "family_id", "family_name", "expected")
SCHEMA = Path(__file__).resolve().parents[1] / "schemas" / "artifacts.schema.json"


def read_tsv(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != fields:
            raise ValueError(f"{path}: columns must be exactly {', '.join(fields)}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path}: no data rows")
    return rows


def write_tsv(path: Path, fields: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("annotations", type=Path)
    parser.add_argument("--genomes", type=Path, required=True)
    parser.add_argument("--markers", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        annotations = read_tsv(args.annotations, ANNOTATION_FIELDS)
        genomes = read_tsv(args.genomes, GENOME_FIELDS)
        markers = read_tsv(args.markers, MARKER_FIELDS)
        if args.out.exists() and any(args.out.iterdir()):
            raise ValueError(f"output directory is not empty: {args.out}")
        args.out.mkdir(parents=True, exist_ok=True)
        genome_ids = [row["genome"] for row in genomes]
        if len(genome_ids) != len(set(genome_ids)):
            raise ValueError("genome identifiers must be unique")
        unknown = {row["genome"] for row in annotations} - set(genome_ids)
        if unknown:
            raise ValueError(f"annotations contain genomes absent from manifest: {sorted(unknown)}")
        proteins = [row["protein_id"] for row in annotations]
        if len(proteins) != len(set(proteins)):
            raise ValueError("protein_id values must be globally unique")

        normalized = []
        for row in annotations:
            try:
                e_value, confidence = float(row["e_value"]), float(row["confidence"])
            except ValueError as error:
                raise ValueError(f"invalid numeric annotation for {row['protein_id']}") from error
            normalized.append({**row, "e_value": e_value, "confidence": confidence})
        pl.DataFrame(normalized).write_parquet(args.out / "annotations.parquet")
        pl.DataFrame([{"genome": row["genome"], "taxonomy": row["taxonomy"]} for row in normalized]).unique().write_parquet(args.out / "taxonomy.parquet")

        counts = Counter((row["family_id"], row["genome"]) for row in normalized)
        family_ids = sorted({row["family_id"] for row in normalized} | {row["family_id"] for row in markers})
        matrix = [{"family_id": family, **{genome: counts[(family, genome)] for genome in genome_ids}} for family in family_ids]
        pl.DataFrame(matrix).write_parquet(args.out / "family_copy_number_matrix.parquet")

        marker_rows: list[dict[str, object]] = []
        for marker in markers:
            evidence = defaultdict(list)
            for row in normalized:
                if row["family_id"] == marker["family_id"]:
                    evidence[row["genome"]].append(row)
            for genome in genome_ids:
                hits = evidence[genome]
                marker_rows.append({"genome": genome, "category": marker["category"], "family_id": marker["family_id"], "family_name": marker["family_name"], "copy_number": len(hits), "evidence_source": "normalized_annotation" if hits else "explicit_absence", "e_value": min((hit["e_value"] for hit in hits), default=""), "notes": "" if hits else "expected marker absent"})
        write_tsv(args.out / "marker_census.tsv", ("genome", "category", "family_id", "family_name", "copy_number", "evidence_source", "e_value", "notes"), marker_rows)

        roles = {row["genome"]: row["role"] for row in genomes}
        references = [genome for genome in genome_ids if roles[genome] == "reference"]
        queries = [genome for genome in genome_ids if roles[genome] == "query"]
        if not references or not queries:
            raise ValueError("genome manifest requires at least one query and one reference")
        candidates: list[dict[str, object]] = []
        for family in family_ids:
            baseline = statistics.median(counts[(family, genome)] for genome in references)
            for query in queries:
                count = counts[(family, query)]
                if count and baseline == 0:
                    status, fold = "query_specific", "inf"
                elif count == 0 and baseline > 0:
                    status, fold = "missing_expected", 0
                elif baseline and count >= baseline * 2:
                    status, fold = "expanded", count / baseline
                elif baseline and count * 2 <= baseline:
                    status, fold = "contracted", count / baseline
                else:
                    continue
                candidates.append({"genome": query, "family_id": family, "query_copy_number": count, "relative_median": baseline, "fold_change": fold, "status": status, "recommended_validation": "review family evidence and genomic context"})
        write_tsv(args.out / "family_expansion_candidates.tsv", ("genome", "family_id", "query_copy_number", "relative_median", "fold_change", "status", "recommended_validation"), candidates)
        write_tsv(args.out / "discovery_candidates.tsv", ("genome", "family_id", "query_copy_number", "relative_median", "fold_change", "status", "recommended_validation"), candidates)
        write_tsv(args.out / "domain_routing.tsv", GENOME_FIELDS, genomes)
        inventory = [{"genome": genome, "protein_count": sum(1 for row in normalized if row["genome"] == genome), "unannotated_count": sum(1 for row in normalized if row["genome"] == genome and not row["annotation"].strip())} for genome in genome_ids]
        pl.DataFrame(inventory).write_parquet(args.out / "feature_inventory.parquet")
        artifacts = [
            {"path": name, "record_key": record_key}
            for name, record_key in (
                ("annotations.parquet", "protein_id"),
                ("taxonomy.parquet", "genome"),
                ("feature_inventory.parquet", "genome"),
                ("marker_census.tsv", "genome,family_id"),
                ("family_copy_number_matrix.parquet", "family_id"),
                ("domain_routing.tsv", "genome"),
                ("family_expansion_candidates.tsv", "genome,family_id"),
                ("discovery_candidates.tsv", "genome,family_id"),
            )
        ]
        manifest = {
            "schema_version": "1.0",
            "genomes": len(genomes),
            "annotations": len(normalized),
            "families": len(family_ids),
            "artifacts": artifacts,
        }
        validate(manifest, json.loads(SCHEMA.read_text(encoding="utf-8")))
        (args.out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        out = args.out.resolve()
        print(json.dumps({"ok": True, "skill": "bio-annotation", "out": str(out), "manifest": str(out / "run_manifest.json"), "warnings": []}))
    except (OSError, ValueError, ValidationError) as error:
        print(json.dumps({"ok": False, "skill": "bio-annotation", "error": {"code": type(error).__name__, "message": str(error)}}))
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
