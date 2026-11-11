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
ROLES = ("query", "reference")
CANDIDATE_FIELDS = (
    "genome",
    "family_id",
    "query_copy_number",
    "relative_median",
    "fold_change",
    "status",
    "recommended_validation",
)
SCHEMA = Path(__file__).resolve().parents[1] / "schemas" / "artifacts.schema.json"


def read_tsv(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != fields:
            raise ValueError(f"{path}: columns must be exactly {', '.join(fields)}")
        rows = []
        for number, row in enumerate(reader, start=1):
            if None in row or None in row.values():
                raise ValueError(
                    f"{path}: data row {number} must have exactly {len(fields)} fields"
                )
            rows.append(row)
    if not rows:
        raise ValueError(f"{path}: no data rows")
    return rows


def write_tsv(path: Path, fields: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(
    annotations: list[dict[str, str]], genomes: list[dict[str, str]]
) -> list[str]:
    """Check the annotation and genome tables against each other.

    Returns:
        The genome identifiers in manifest order.

    Raises:
        ValueError: On duplicate genomes, unknown genomes or roles, repeated
            protein and family pairs, a protein under two genomes, or a manifest
            without a query and a reference.
    """
    genome_ids = [row["genome"] for row in genomes]
    if len(genome_ids) != len(set(genome_ids)):
        raise ValueError("genome identifiers must be unique")
    for row in genomes:
        if row["role"] not in ROLES:
            raise ValueError(
                f"genome {row['genome']!r} has unsupported role {row['role']!r}; "
                f"use one of {', '.join(ROLES)}"
            )
    roles = {row["role"] for row in genomes}
    if roles != set(ROLES):
        raise ValueError(
            "genome manifest requires at least one query and one reference"
        )
    unknown = {row["genome"] for row in annotations} - set(genome_ids)
    if unknown:
        raise ValueError(
            f"annotations contain genomes absent from manifest: {sorted(unknown)}"
        )
    # One protein legitimately carries several family hits (multi-domain
    # proteins are the normal case), so uniqueness is per protein AND family.
    pairs = [(row["protein_id"], row["family_id"]) for row in annotations]
    if len(pairs) != len(set(pairs)):
        duplicated = sorted({pair for pair in pairs if pairs.count(pair) > 1})
        raise ValueError(f"duplicate protein_id/family_id rows: {duplicated}")
    # A protein identifier still belongs to exactly one genome; only the
    # family dimension is allowed to repeat.
    owners: dict[str, str] = {}
    for row in annotations:
        owner = owners.setdefault(row["protein_id"], row["genome"])
        if owner != row["genome"]:
            raise ValueError(
                f"protein_id {row['protein_id']!r} appears under both "
                f"{owner!r} and {row['genome']!r}"
            )
    return genome_ids


def normalize(annotations: list[dict[str, str]]) -> list[dict[str, object]]:
    """Convert the numeric columns of every annotation row to floats."""
    normalized = []
    for row in annotations:
        try:
            e_value, confidence = float(row["e_value"]), float(row["confidence"])
        except ValueError as error:
            raise ValueError(
                f"invalid numeric annotation for {row['protein_id']}"
            ) from error
        normalized.append({**row, "e_value": e_value, "confidence": confidence})
    return normalized


def build_marker_census(
    markers: list[dict[str, str]],
    normalized: list[dict[str, object]],
    genome_ids: list[str],
) -> list[dict[str, object]]:
    """Return one row per marker and genome, with explicit absence rows."""
    rows_by_family: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in normalized:
        rows_by_family[row["family_id"]].append(row)
    census: list[dict[str, object]] = []
    for marker in markers:
        evidence: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in rows_by_family[marker["family_id"]]:
            evidence[row["genome"]].append(row)
        for genome in genome_ids:
            hits = evidence[genome]
            census.append(
                {
                    "genome": genome,
                    "category": marker["category"],
                    "family_id": marker["family_id"],
                    "family_name": marker["family_name"],
                    "copy_number": len(hits),
                    "evidence_source": "normalized_annotation"
                    if hits
                    else "explicit_absence",
                    "e_value": min((hit["e_value"] for hit in hits), default=""),
                    "notes": "" if hits else "expected marker absent",
                }
            )
    return census


def build_candidates(
    family_ids: list[str],
    counts: Counter[tuple[str, str]],
    genomes: list[dict[str, str]],
) -> list[dict[str, object]]:
    """Compare each query genome's family copy number with the reference median."""
    references = [row["genome"] for row in genomes if row["role"] == "reference"]
    queries = [row["genome"] for row in genomes if row["role"] == "query"]
    candidates: list[dict[str, object]] = []
    for family in family_ids:
        reference_counts = [counts[(family, genome)] for genome in references]
        baseline = statistics.median(reference_counts)
        # A zero MEDIAN does not mean absent from every reference: with counts
        # [0, 0, 1] the family is present in a reference, so calling it
        # query-specific with an infinite fold change invents a discovery.
        absent_everywhere = max(reference_counts) == 0
        for query in queries:
            count = counts[(family, query)]
            if count and absent_everywhere:
                status, fold = "query_specific", "inf"
            elif count and baseline == 0:
                status, fold = "present_in_reference_minority", ""
            elif count == 0 and baseline > 0:
                status, fold = "missing_expected", 0
            elif baseline and count >= baseline * 2:
                status, fold = "expanded", count / baseline
            elif baseline and count * 2 <= baseline:
                status, fold = "contracted", count / baseline
            else:
                continue
            candidates.append(
                {
                    "genome": query,
                    "family_id": family,
                    "query_copy_number": count,
                    "relative_median": baseline,
                    "fold_change": fold,
                    "status": status,
                    "recommended_validation": (
                        "review family evidence and genomic context"
                    ),
                }
            )
    return candidates


def build_inventory(
    normalized: list[dict[str, object]], genome_ids: list[str]
) -> list[dict[str, object]]:
    """Count proteins per genome, not annotation rows.

    One protein with two family hits is still one protein, and is unannotated
    only if no hit annotates it.
    """
    by_protein: dict[str, dict[str, set[str]]] = {genome: {} for genome in genome_ids}
    for row in normalized:
        annotated = by_protein[row["genome"]].setdefault(row["protein_id"], set())
        if row["annotation"].strip():
            annotated.add(row["annotation"].strip())
    return [
        {
            "genome": genome,
            "protein_count": len(by_protein[genome]),
            "unannotated_count": sum(
                1 for hits in by_protein[genome].values() if not hits
            ),
        }
        for genome in genome_ids
    ]


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
        # All validation and all rows come first, so a failed run writes nothing.
        genome_ids = validate_inputs(annotations, genomes)
        normalized = normalize(annotations)
        counts = Counter((row["family_id"], row["genome"]) for row in normalized)
        family_ids = sorted({row["family_id"] for row in normalized} | {row["family_id"] for row in markers})
        matrix = [{"family_id": family, **{genome: counts[(family, genome)] for genome in genome_ids}} for family in family_ids]
        marker_rows = build_marker_census(markers, normalized, genome_ids)
        candidates = build_candidates(family_ids, counts, genomes)
        inventory = build_inventory(normalized, genome_ids)
        artifacts = [
            {"path": name, "record_key": record_key}
            for name, record_key in (
                ("annotations.parquet", "protein_id,family_id"),
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

        args.out.mkdir(parents=True, exist_ok=True)
        pl.DataFrame(normalized).write_parquet(args.out / "annotations.parquet")
        pl.DataFrame(
            [
                {"genome": row["genome"], "taxonomy": row["taxonomy"]}
                for row in normalized
            ]
        ).unique().write_parquet(args.out / "taxonomy.parquet")
        pl.DataFrame(matrix).write_parquet(
            args.out / "family_copy_number_matrix.parquet"
        )
        write_tsv(
            args.out / "marker_census.tsv",
            (
                "genome",
                "category",
                "family_id",
                "family_name",
                "copy_number",
                "evidence_source",
                "e_value",
                "notes",
            ),
            marker_rows,
        )
        write_tsv(
            args.out / "family_expansion_candidates.tsv", CANDIDATE_FIELDS, candidates
        )
        write_tsv(args.out / "discovery_candidates.tsv", CANDIDATE_FIELDS, candidates)
        write_tsv(args.out / "domain_routing.tsv", GENOME_FIELDS, genomes)
        pl.DataFrame(inventory).write_parquet(args.out / "feature_inventory.parquet")
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
