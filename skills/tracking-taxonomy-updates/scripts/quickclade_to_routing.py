#!/usr/bin/env python3
"""Normalize QuickClade machine output into domain_routing.tsv."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


ALIASES = {
    "query_id": ("query_id", "query", "name", "filename", "input"),
    "contig_id": ("contig_id", "contig", "record", "sequence"),
    "domain": ("quickclade_domain", "domain", "Domain"),
    "taxonomy": ("quickclade_taxonomy", "taxonomy", "lineage", "tax_name"),
    "confidence": ("quickclade_confidence", "confidence", "score", "composite"),
}
OUTPUT_FIELDS = (
    "sample_id",
    "query_id",
    "contig_id",
    "quickclade_domain",
    "quickclade_taxonomy",
    "quickclade_confidence",
    "route",
    "downstream_tool",
    "review_flag",
    "notes",
)


def choose(columns: list[str], logical: str, required: bool = True) -> str | None:
    for candidate in ALIASES[logical]:
        if candidate in columns:
            return candidate
    if required:
        raise ValueError(f"QuickClade table lacks a recognized {logical} column: {ALIASES[logical]}")
    return None


def route(domain: str) -> tuple[str, str, str, str]:
    value = domain.strip().lower()
    if "nucleocyt" in value or "giant" in value or "ncldv" in value:
        return "giant_virus", "gvclass", "false", "validate with marker-gene phylogeny"
    if "viral" in value or "virus" in value or "phage" in value:
        return "prokaryotic_virus", "vcontact3", "false", "confirm lineage before clustering"
    if "bacter" in value or "archaea" in value:
        return "prokaryote", "gtdbtk", "false", ""
    if "euk" in value or "fung" in value:
        return "eukaryote", "eukcc", "false", ""
    return "manual_review", "", "true", "mixed, low-confidence, or unknown domain"


def convert(source: Path, output: Path, sample_id: str) -> int:
    if output.exists():
        raise ValueError(f"refusing to overwrite {output}")
    with source.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        columns = reader.fieldnames or []
        selected = {
            logical: choose(columns, logical, required=logical != "contig_id")
            for logical in ALIASES
        }
        rows = list(reader)
    if not rows:
        raise ValueError("QuickClade table has no data rows")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS, delimiter="\t")
        writer.writeheader()
        for row in rows:
            domain = row[selected["domain"]].strip()
            route_name, tool, review, notes = route(domain)
            query_id = row[selected["query_id"]].strip()
            contig_column = selected["contig_id"]
            writer.writerow(
                {
                    "sample_id": sample_id,
                    "query_id": query_id,
                    "contig_id": row[contig_column].strip() if contig_column else "",
                    "quickclade_domain": domain,
                    "quickclade_taxonomy": row[selected["taxonomy"]].strip(),
                    "quickclade_confidence": row[selected["confidence"]].strip(),
                    "route": route_name,
                    "downstream_tool": tool,
                    "review_flag": review,
                    "notes": notes,
                }
            )
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("quickclade_tsv", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sample-id", required=True)
    args = parser.parse_args(argv)
    try:
        count = convert(args.quickclade_tsv, args.output, args.sample_id)
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {count} routing rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
