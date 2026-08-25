#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema==4.25.1"]
# ///
"""Apply HGT evidence gates to versioned homology, context, and tree records."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from jsonschema import ValidationError, validate

FORWARD_FIELDS = ("query_protein", "recipient_locus", "recipient_lineage", "recipient_domain", "identity", "query_coverage", "subject_coverage", "e_value", "bitscore")
ARBITER_FIELDS = ("entity_id", "entity_type", "hit_domain", "hit_lineage", "bitscore", "rank")
RECIPROCAL_FIELDS = ("query_protein", "recipient_locus", "forward_rank", "reverse_rank")
CONTEXT_FIELDS = ("recipient_locus", "recipient_contig", "recipient_domain_fraction", "donor_domain_fraction", "method")
TREE_FIELDS = ("candidate_id", "expected_clade", "nesting_clade", "support", "tree_path")
DEPTH_FIELDS = ("lineage", "genomes_sampled")
HYPOTHESIS_FIELDS = ("hypothesis_id", "hypothesis", "type", "status", "evidence", "revision_stage")
REFLECTION_FIELDS = ("gate", "observed", "qc_status", "hypotheses_gained", "hypotheses_lost", "alternatives", "next_check", "literature_id")
REQUIRED_DOMAINS = {"eukaryota", "bacteria", "archaea", "ncldv", "phage", "organelle"}
SCHEMA = Path(__file__).resolve().parents[1] / "schemas" / "hgt-evidence.schema.json"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


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


def load_databases(path: Path) -> dict[str, object]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "1.0" or set(manifest.get("arbiter_domains", [])) != REQUIRED_DOMAINS:
        raise ValueError("database manifest must use schema 1.0 and cover all required arbiter domains")
    for item in manifest.get("databases", []):
        target = Path(item.get("path", ""))
        target = target if target.is_absolute() else path.parent / target
        if not item.get("name") or not item.get("version") or not item.get("sha256"):
            raise ValueError("every database requires name, version, path, and sha256")
        if not target.is_file() or target.stat().st_size == 0 or digest(target) != item["sha256"]:
            raise ValueError(f"database missing, empty, or checksum-mismatched: {item.get('name')}")
        item["path"] = str(target.resolve())
    if len(manifest.get("databases", [])) < 3:
        raise ValueError("arbiter, lineage labels, and comparison database records are required")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("forward_hits", type=Path)
    parser.add_argument("--arbiter-hits", type=Path, required=True)
    parser.add_argument("--reciprocal", type=Path, required=True)
    parser.add_argument("--context", type=Path, required=True)
    parser.add_argument("--trees", type=Path, required=True)
    parser.add_argument("--sampling-depth", type=Path, required=True)
    parser.add_argument("--databases", type=Path, required=True)
    parser.add_argument("--hypotheses", type=Path, required=True)
    parser.add_argument("--reflections", type=Path, required=True)
    parser.add_argument("--query-domain", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        forward = read(args.forward_hits, FORWARD_FIELDS)
        arbiter = read(args.arbiter_hits, ARBITER_FIELDS)
        reciprocal = read(args.reciprocal, RECIPROCAL_FIELDS)
        contexts = read(args.context, CONTEXT_FIELDS)
        trees = read(args.trees, TREE_FIELDS)
        depths = read(args.sampling_depth, DEPTH_FIELDS)
        hypotheses = read(args.hypotheses, HYPOTHESIS_FIELDS)
        reflections = read(args.reflections, REFLECTION_FIELDS)
        databases = load_databases(args.databases)
        if len({row["hypothesis_id"] for row in hypotheses}) < 5 or not any(row["type"] in {"technical", "null"} for row in hypotheses):
            raise ValueError("at least five hypotheses including a technical/null explanation are required")
        required_gates = ["database", "forward", "reciprocal", "context", "phylogeny", "final"]
        if [row["gate"] for row in reflections] != required_gates:
            raise ValueError(f"reflections must cover gates in order: {', '.join(required_gates)}")
        if args.out.exists() and any(args.out.iterdir()):
            raise ValueError(f"output directory is not empty: {args.out}")
        args.out.mkdir(parents=True, exist_ok=True)

        best: dict[str, dict[str, str]] = {}
        for row in arbiter:
            if int(row["rank"]) == 1:
                if row["entity_id"] in best:
                    raise ValueError(f"multiple rank-1 arbiter hits for {row['entity_id']}")
                best[row["entity_id"]] = row
        rbh = {(row["query_protein"], row["recipient_locus"]): int(row["forward_rank"]) == 1 and int(row["reverse_rank"]) == 1 for row in reciprocal}
        context = {row["recipient_locus"]: row for row in contexts}
        tree = {row["candidate_id"]: row for row in trees}
        candidates: list[dict[str, object]] = []
        for hit in forward:
            query_id, locus = hit["query_protein"], hit["recipient_locus"]
            if query_id not in best or locus not in best or locus not in context or query_id not in tree:
                raise ValueError(f"candidate lacks arbiter, context, or tree evidence: {query_id}/{locus}")
            q_domain, r_domain = best[query_id]["hit_domain"], best[locus]["hit_domain"]
            recipient_domain = hit["recipient_domain"]
            if q_domain == recipient_domain:
                direction = "recipient_to_query"
            elif r_domain == args.query_domain:
                direction = "query_to_recipient"
            else:
                direction = "ambiguous"
            ctx = context[locus]
            frame_aware = recipient_domain != "eukaryota" or ctx["method"] == "diamond_blastx"
            context_pass = float(ctx["recipient_domain_fraction"]) >= 0.6 and frame_aware
            phy = tree[query_id]
            phylogeny_pass = phy["expected_clade"] == phy["nesting_clade"] and float(phy["support"]) >= 0.9
            homology_pass = float(hit["query_coverage"]) >= 0.5 and float(hit["subject_coverage"]) >= 0.5 and float(hit["e_value"]) <= 1e-5
            reciprocal_pass = rbh.get((query_id, locus), False)
            status = "confirmed" if all((homology_pass, reciprocal_pass, context_pass, phylogeny_pass)) and direction != "ambiguous" else "candidate" if homology_pass else "rejected"
            candidates.append({**hit, "query_best_domain": q_domain, "recipient_best_domain": r_domain, "reciprocal_best_hit": str(reciprocal_pass).lower(), "direction": direction, "context_pass": str(context_pass).lower(), "frame_aware_context": str(frame_aware).lower(), "phylogeny_support": phy["support"], "phylogeny_pass": str(phylogeny_pass).lower(), "status": status})
        candidate_fields = (*FORWARD_FIELDS, "query_best_domain", "recipient_best_domain", "reciprocal_best_hit", "direction", "context_pass", "frame_aware_context", "phylogeny_support", "phylogeny_pass", "status")
        write(args.out / "hgt_candidates.tsv", candidate_fields, candidates)
        origin_rows = [{"query_protein": row["query_protein"], "best_domain": best[row["query_protein"]]["hit_domain"], "best_lineage": best[row["query_protein"]]["hit_lineage"], "origin_class": "query_core" if best[row["query_protein"]]["hit_domain"] == args.query_domain else "donor_derived"} for row in forward]
        write(args.out / "query_protein_origin.tsv", ("query_protein", "best_domain", "best_lineage", "origin_class"), origin_rows)

        confirmed = Counter(row["recipient_lineage"] for row in candidates if row["status"] == "confirmed")
        depth_map = {row["lineage"]: int(row["genomes_sampled"]) for row in depths}
        normalization = []
        for lineage in sorted(set(depth_map) | set(confirmed)):
            depth = depth_map.get(lineage, 0)
            if depth <= 0:
                raise ValueError(f"missing positive sampling depth for lineage: {lineage}")
            normalization.append({"lineage": lineage, "confirmed_candidates": confirmed[lineage], "genomes_sampled": depth, "candidates_per_100_genomes": f"{100 * confirmed[lineage] / depth:.6f}"})
        write(args.out / "lineage_sampling_normalization.tsv", ("lineage", "confirmed_candidates", "genomes_sampled", "candidates_per_100_genomes"), normalization)
        write(args.out / "phylogeny_evidence.tsv", TREE_FIELDS, trees)
        write(args.out / "hypothesis_register.tsv", HYPOTHESIS_FIELDS, hypotheses)
        write(args.out / "gate_reflections.tsv", REFLECTION_FIELDS, reflections)
        manifest = {"schema_version": "1.0", "query_domain": args.query_domain, "databases": databases, "candidate_count": len(candidates), "confirmed_count": sum(row["status"] == "confirmed" for row in candidates), "gates": required_gates}
        validate(manifest, json.loads(SCHEMA.read_text(encoding="utf-8")))
        (args.out / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        out = args.out.resolve()
        print(json.dumps({"ok": True, "skill": "bio-interdomain-hgt", "out": str(out), "manifest": str(out / "run_manifest.json"), "warnings": []}))
    except (OSError, ValueError, json.JSONDecodeError, ValidationError) as error:
        print(json.dumps({"ok": False, "skill": "bio-interdomain-hgt", "error": {"code": type(error).__name__, "message": str(error)}}))
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
