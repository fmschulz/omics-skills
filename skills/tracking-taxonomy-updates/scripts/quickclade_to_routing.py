#!/usr/bin/env python3
"""Normalize QuickClade `format=machine` output into domain_routing.tsv.

Reads the columns QuickClade 39.85 writes (`#QueryName`, `Q_Contigs`, `lineage`,
`Confidence`), keeps the best hit (the first row) of each query, and routes it
by the domain in the lineage. The domain-level confidence below
`--min-confidence` sends the contig to manual review.
"""

from __future__ import annotations

import argparse
import csv
import fcntl
import math
import os
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

DEFAULT_MIN_CONFIDENCE = 90.0
QUERY_COLUMN = "#QueryName"
REQUIRED_COLUMNS = (QUERY_COLUMN, "Q_Contigs", "lineage", "Confidence")
GIANT_VIRUS_PHYLUM = "p__Nucleocytoviricota"
OUTPUT_FIELDS = (
    "sample_id",
    "query_id",
    "contig_id",
    "quickclade_domain",
    "quickclade_taxonomy",
    "quickclade_confidence",
    "low_confidence",
    "route",
    "downstream_tool",
    "review_flag",
    "notes",
)


def domain_of(lineage: str) -> str:
    """Return the lineage domain; giant viruses return Nucleocytoviricota."""
    ranks = lineage.split(";")
    if GIANT_VIRUS_PHYLUM in ranks:
        return "Nucleocytoviricota"
    if not ranks[0].startswith("sk__"):
        raise ValueError(f"lineage does not start with sk__: {lineage!r}")
    return ranks[0].removeprefix("sk__")


def is_percent(value: float) -> bool:
    """Return whether `value` is a finite number from 0 to 100."""
    return math.isfinite(value) and 0.0 <= value <= 100.0


def domain_confidence(confidence: str) -> float:
    """Return the domain-level value (`d:`) of a QuickClade `Confidence` string.

    Raises:
        ValueError: There is no `d:` entry, or its value is not a finite number
            from 0 to 100.
    """
    for entry in confidence.split(";"):
        rank, _, value = entry.partition(":")
        if rank == "d":
            percent = float(value)
            if not is_percent(percent):
                raise ValueError(
                    f"domain confidence d:{value} is not a finite number "
                    f"from 0 to 100: {confidence!r}"
                )
            return percent
    raise ValueError(f"Confidence has no d: entry: {confidence!r}")


def route(domain: str) -> tuple[str, str, str, str]:
    """Map a domain to (route, downstream tool, review flag, notes)."""
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


def best_hits(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Keep the first row of each run of rows that share a query name."""
    hits: list[dict[str, str]] = []
    previous = None
    for row in rows:
        if row[QUERY_COLUMN] != previous:
            hits.append(row)
        previous = row[QUERY_COLUMN]
    return hits


def routing_row(
    hit: dict[str, str], sample_id: str, min_confidence: float
) -> dict[str, str]:
    """Build the routing row of one best hit."""
    query = hit[QUERY_COLUMN].strip()
    if hit["Q_Contigs"].strip() != "1":
        raise ValueError(
            f"query {query!r} spans {hit['Q_Contigs']} contigs; "
            "run QuickClade with percontig"
        )
    domain = domain_of(hit["lineage"])
    confidence = domain_confidence(hit["Confidence"])
    route_name, tool, review, notes = route(domain)
    low = confidence < min_confidence
    if low:
        route_name, tool, review = "manual_review", "", "true"
        notes = (
            f"domain confidence {confidence:g} "
            f"is below --min-confidence {min_confidence:g}"
        )
    return {
        "sample_id": sample_id,
        "query_id": query,
        "contig_id": query.split()[0],
        "quickclade_domain": domain,
        "quickclade_taxonomy": hit["lineage"].strip(),
        "quickclade_confidence": f"{confidence:g}",
        "low_confidence": str(low).lower(),
        "route": route_name,
        "downstream_tool": tool,
        "review_flag": review,
        "notes": notes,
    }


def read_rows(path: Path, *, expected: tuple[str, ...]) -> list[dict[str, str]]:
    """Read a TSV and fail when it lacks one of the expected columns."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        columns = reader.fieldnames or []
        missing = [name for name in expected if name not in columns]
        if missing:
            raise ValueError(f"{path} lacks the columns {missing}; found {columns}")
        return list(reader)


def read_routing_table(path: Path) -> list[dict[str, str]]:
    """Read an existing routing table whose header is exactly `OUTPUT_FIELDS`."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != OUTPUT_FIELDS:
            raise ValueError(
                f"cannot append to {path}: its header is {reader.fieldnames}, "
                f"expected exactly {list(OUTPUT_FIELDS)}"
            )
        return list(reader)


def convert(
    source: Path,
    output: Path,
    sample_id: str,
    *,
    min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    append: bool = False,
) -> int:
    """Write one routing row per query; `append` adds them to an existing table.

    One exclusive lock beside the output covers the existence check, the read,
    the duplicate check and the write, so concurrent runs cannot lose rows.
    """
    if not is_percent(min_confidence):
        raise ValueError(
            "--min-confidence must be a finite number from 0 to 100, "
            f"got {min_confidence}"
        )
    rows = read_rows(source, expected=REQUIRED_COLUMNS)
    if not rows:
        raise ValueError("QuickClade table has no data rows")
    new_rows = [routing_row(hit, sample_id, min_confidence) for hit in best_hits(rows)]
    with locked(output):
        if output.exists() and not append:
            raise ValueError(
                f"refusing to overwrite {output}; pass --append to add a sample"
            )
        existing = read_routing_table(output) if output.exists() else []
        known = {(row["sample_id"], row["contig_id"]) for row in existing}
        for row in new_rows:
            key = (row["sample_id"], row["contig_id"])
            if key in known:
                raise ValueError(
                    f"{output} already holds sample {key[0]!r} contig {key[1]!r}"
                )
            known.add(key)
        write_rows(output, existing + new_rows)
    return len(new_rows)


@contextmanager
def locked(output: Path) -> Iterator[None]:
    """Hold an exclusive `flock` on a lock file beside `output`."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.with_name(output.name + ".lock").open("a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        yield


def write_rows(output: Path, rows: list[dict[str, str]]) -> None:
    """Write the whole table to a temporary file, then replace `output` with it."""
    handle, temp_name = tempfile.mkstemp(
        dir=output.parent, prefix=f".{output.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="") as temp_file:
            writer = csv.DictWriter(temp_file, fieldnames=OUTPUT_FIELDS, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
        Path(temp_name).replace(output)
    except BaseException:
        Path(temp_name).unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("quickclade_tsv", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sample-id", required=True)
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=DEFAULT_MIN_CONFIDENCE,
        help="domain confidence (0-100) below which a contig goes to manual review",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="add a sample to an existing table; repeated sample and contig fail",
    )
    args = parser.parse_args(argv)
    try:
        count = convert(
            args.quickclade_tsv,
            args.output,
            args.sample_id,
            min_confidence=args.min_confidence,
            append=args.append,
        )
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {count} routing rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
