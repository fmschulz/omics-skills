#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["polars==1.37.1"]
# ///
"""Build comparison matrices, marker/ncRNA censuses, and simple conserved neighborhoods."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

import polars as pl

GENOME_FIELDS = ("genome", "role", "genome_size", "contig_count", "n50", "gene_count", "coding_density", "gc")
ORTHO_FIELDS = ("orthogroup", "protein_id", "genome", "contig", "order", "start", "end")
MARKER_CATALOG_FIELDS = ("category", "family_id", "family_name")
MARKER_HIT_FIELDS = ("genome", "family_id", "protein_id", "e_value")
NCRNA_FIELDS = ("assembly", "class", "tool", "model", "threshold", "count", "notes")


def read(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != fields:
            raise ValueError(f"{path}: columns must be exactly {', '.join(fields)}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path}: no rows")
    return rows


def write(path: Path, fields: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def adjacency(rows: list[dict[str, str]]) -> dict[str, dict[tuple[str, str], tuple[int, str]]]:
    by_genome_contig: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_genome_contig[(row["genome"], row["contig"])].append(row)
    result: dict[str, dict[tuple[str, str], tuple[int, str]]] = defaultdict(dict)
    for (genome, contig), genes in by_genome_contig.items():
        genes.sort(key=lambda item: int(item["order"]))
        for left, right in zip(genes, genes[1:]):
            pair = (left["orthogroup"], right["orthogroup"])
            result[genome][pair] = (int(right["start"]) - int(left["end"]) - 1, contig)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("orthogroups", type=Path)
    parser.add_argument("--genomes", type=Path, required=True)
    parser.add_argument("--marker-catalog", type=Path, required=True)
    parser.add_argument("--marker-hits", type=Path, required=True)
    parser.add_argument("--ncrna", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        orthos = read(args.orthogroups, ORTHO_FIELDS)
        genomes = read(args.genomes, GENOME_FIELDS)
        catalog = read(args.marker_catalog, MARKER_CATALOG_FIELDS)
        hits = read(args.marker_hits, MARKER_HIT_FIELDS)
        ncrna = read(args.ncrna, NCRNA_FIELDS)
        if args.out.exists() and any(args.out.iterdir()):
            raise ValueError(f"output directory is not empty: {args.out}")
        args.out.mkdir(parents=True, exist_ok=True)
        genome_ids = [row["genome"] for row in genomes]
        if len(genome_ids) != len(set(genome_ids)):
            raise ValueError("genome identifiers must be unique")
        if {row["genome"] for row in orthos} != set(genome_ids):
            raise ValueError("orthogroups must cover every and only declared genome")
        proteins = [row["protein_id"] for row in orthos]
        if len(proteins) != len(set(proteins)):
            raise ValueError("protein identifiers must be globally unique")

        counts = Counter((row["orthogroup"], row["genome"]) for row in orthos)
        families = sorted({row["orthogroup"] for row in orthos})
        copy_rows = [{"orthogroup": family, **{genome: counts[(family, genome)] for genome in genome_ids}} for family in families]
        pl.DataFrame(copy_rows).write_parquet(args.out / "copy_number_matrix.parquet")
        pl.DataFrame([{"orthogroup": row["orthogroup"], **{genome: int(row[genome] > 0) for genome in genome_ids}} for row in copy_rows]).write_parquet(args.out / "presence_absence.parquet")

        roles = {row["genome"]: row["role"] for row in genomes}
        queries = [genome for genome in genome_ids if roles[genome] == "query"]
        refs = [genome for genome in genome_ids if roles[genome] == "reference"]
        if not queries or len(refs) < 2:
            raise ValueError("fixture/analysis requires at least one query and two references")
        comparisons = []
        for family in families:
            baseline = statistics.median(counts[(family, genome)] for genome in refs)
            for query in queries:
                count = counts[(family, query)]
                fold = "inf" if baseline == 0 and count else (count / baseline if baseline else 0)
                status = "query_specific" if baseline == 0 and count else "missing_expected" if count == 0 and baseline else "expanded" if baseline and count >= 2 * baseline else "contracted" if baseline and count * 2 <= baseline else "conserved"
                comparisons.append({"family_id": family, "query": query, "query_copy_number": count, "relative_median": f"{baseline:g}", "fold_change": f"{fold:g}" if isinstance(fold, float) else fold, "status": status})
        write(args.out / "family_copy_number_comparison.tsv", ("family_id", "query", "query_copy_number", "relative_median", "fold_change", "status"), comparisons)

        hit_map: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
        for hit in hits:
            hit_map[(hit["genome"], hit["family_id"])].append(hit)
        marker_rows = []
        for genome in genome_ids:
            for marker in catalog:
                found = hit_map[(genome, marker["family_id"])]
                marker_rows.append({"genome": genome, "category": marker["category"], "family_id": marker["family_id"], "family_name": marker["family_name"], "copy_number": len(found), "evidence_source": "marker_hits" if found else "explicit_absence", "e_value": min((float(hit["e_value"]) for hit in found), default=""), "notes": "" if found else "expected marker absent"})
        write(args.out / "marker_census.tsv", ("genome", "category", "family_id", "family_name", "copy_number", "evidence_source", "e_value", "notes"), marker_rows)
        write(args.out / "ncRNA_census.tsv", NCRNA_FIELDS, ncrna)

        adjacent = adjacency(orthos)
        neighborhoods = []
        for query in queries:
            for relative in refs:
                for pair in sorted(set(adjacent[query]) & set(adjacent[relative])):
                    query_spacing, query_contig = adjacent[query][pair]
                    relative_spacing, relative_contig = adjacent[relative][pair]
                    ratio = "inf" if relative_spacing == 0 and query_spacing else (query_spacing / relative_spacing if relative_spacing else 1)
                    neighborhoods.append({"query_block_id": f"{query_contig}:{pair[0]}-{pair[1]}", "relative": relative, "relative_block_id": f"{relative_contig}:{pair[0]}-{pair[1]}", "members": ",".join(pair), "intergenic_spacing_query": query_spacing, "intergenic_spacing_relative": relative_spacing, "spacing_ratio": ratio, "notes": "conserved_pair"})
        write(args.out / "conserved_neighborhoods.tsv", ("query_block_id", "relative", "relative_block_id", "members", "intergenic_spacing_query", "intergenic_spacing_relative", "spacing_ratio", "notes"), neighborhoods)
        metrics = [{**row, "relative_distribution": "query" if row["role"] == "query" else "baseline", "literature_range_reference": "required before biological interpretation"} for row in genomes]
        write(args.out / "relative_genome_metrics.tsv", (*GENOME_FIELDS, "relative_distribution", "literature_range_reference"), metrics)
        print(json.dumps({"ok": True, "skill": "bio-protein-clustering-pangenome", "out": str(args.out.resolve()), "warnings": []}))
    except (OSError, ValueError) as error:
        print(json.dumps({"ok": False, "skill": "bio-protein-clustering-pangenome", "error": {"code": type(error).__name__, "message": str(error)}}))
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
