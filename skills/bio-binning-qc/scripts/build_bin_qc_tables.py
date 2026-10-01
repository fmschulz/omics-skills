#!/usr/bin/env python3
"""Join routed CheckM2, GUNC, EukCC, and GTDB-Tk outputs into stable tables.

Expected inputs are the tools' native tables: CheckM2 `quality_report.tsv`
(`Name`), GUNC `GUNC.*.maxCSS_level.tsv` (`genome`), EukCC folder-mode
`eukcc.csv` (tab-separated, `bin` with its FASTA suffix), and GTDB-Tk
`gtdbtk.*.summary.tsv` (`user_genome`).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


METRIC_FIELDS = (
    "bin_id",
    "domain_route",
    "completeness",
    "contamination",
    "qc_tool",
    "gunc_pass",
    "gunc_css",
    "taxonomy",
    "taxonomy_tool",
    "review_flag",
)
FASTA_SUFFIXES = (".fasta", ".fna", ".fa")


def read_table(path: Path, delimiter: str = "\t") -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=delimiter))
    if not rows:
        raise ValueError(f"table has no rows: {path}")
    return rows


def keyed(rows: list[dict[str, str]], key: str, label: str) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        value = bin_name(row.get(key, ""))
        if not value:
            raise ValueError(f"{label} row is missing {key}")
        if value in result:
            raise ValueError(f"{label} has duplicate identifier {value}")
        result[value] = row
    return result


def bin_name(value: str) -> str:
    """Return a bin identifier without a trailing FASTA suffix.

    Args:
        value: Identifier as written by a QC tool.

    Returns:
        The stripped identifier; EukCC keeps the suffix that the other tools drop.
    """
    name = value.strip()
    for suffix in FASTA_SUFFIXES:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def build(args: argparse.Namespace) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    routes = keyed(read_table(args.routing), "query_id", "domain routing")
    checkm2 = keyed(read_table(args.checkm2), "Name", "CheckM2") if args.checkm2 else {}
    gunc = keyed(read_table(args.gunc), "genome", "GUNC") if args.gunc else {}
    eukcc = keyed(read_table(args.eukcc), "bin", "EukCC") if args.eukcc else {}
    gtdbtk = keyed(read_table(args.gtdbtk), "user_genome", "GTDB-Tk") if args.gtdbtk else {}

    for bin_id in gunc:
        route = routes.get(bin_id, {}).get("route")
        if route != "prokaryote":
            raise ValueError(f"GUNC result {bin_id} has non-prokaryotic route {route!r}")

    metrics: list[dict[str, str]] = []
    taxonomy_rows: list[dict[str, str]] = []
    for bin_id, route_row in routes.items():
        route = route_row["route"]
        metric = {field: "" for field in METRIC_FIELDS}
        metric.update(
            {
                "bin_id": bin_id,
                "domain_route": route,
                "review_flag": route_row.get("review_flag", ""),
            }
        )
        if route == "prokaryote":
            if bin_id not in checkm2 or bin_id not in gtdbtk:
                raise ValueError(f"prokaryotic bin {bin_id} lacks CheckM2 or GTDB-Tk output")
            qc = checkm2[bin_id]
            metric.update(
                {
                    "completeness": qc.get("Completeness", ""),
                    "contamination": qc.get("Contamination", ""),
                    "qc_tool": "checkm2",
                    "taxonomy": gtdbtk[bin_id].get("classification", ""),
                    "taxonomy_tool": "gtdbtk",
                }
            )
            if bin_id in gunc:
                metric["gunc_pass"] = gunc[bin_id].get("pass.GUNC", "")
                metric["gunc_css"] = gunc[bin_id].get("clade_separation_score", "")
            taxonomy_rows.append(
                {"bin_id": bin_id, "classification": metric["taxonomy"], "tool": "gtdbtk"}
            )
        elif route == "eukaryote":
            if bin_id not in eukcc:
                raise ValueError(f"eukaryotic bin {bin_id} lacks EukCC output")
            qc = eukcc[bin_id]
            metric.update(
                {
                    "completeness": qc.get("completeness", ""),
                    "contamination": qc.get("contamination", ""),
                    "qc_tool": "eukcc",
                    "taxonomy": qc.get("ncbi_lng", ""),
                    "taxonomy_tool": "eukcc",
                }
            )
        elif route not in {"prokaryotic_virus", "giant_virus", "manual_review"}:
            raise ValueError(f"unsupported domain route {route!r} for {bin_id}")
        metrics.append(metric)
    return metrics, taxonomy_rows


def write_tsv(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--routing", type=Path, required=True)
    parser.add_argument("--checkm2", type=Path)
    parser.add_argument("--gunc", type=Path)
    parser.add_argument("--eukcc", type=Path)
    parser.add_argument("--gtdbtk", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    metrics_path = args.out_dir / "bin_metrics.tsv"
    taxonomy_path = args.out_dir / "gtdbtk_taxonomy.tsv"
    report_path = args.out_dir / "bin_qc_report.json"
    if any(path.exists() for path in (metrics_path, taxonomy_path, report_path)):
        print("ERROR: refusing to overwrite existing normalized outputs", file=sys.stderr)
        return 1
    try:
        metrics, taxonomy = build(args)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        write_tsv(metrics_path, METRIC_FIELDS, metrics)
        write_tsv(taxonomy_path, ("bin_id", "classification", "tool"), taxonomy)
        report_path.write_text(
            json.dumps(
                {
                    "ok": True,
                    "routed_bins": len(metrics),
                    "prokaryotic_bins": sum(row["domain_route"] == "prokaryote" for row in metrics),
                    "eukaryotic_bins": sum(row["domain_route"] == "eukaryote" for row in metrics),
                    "viral_or_review_bins": sum(
                        row["domain_route"] not in {"prokaryote", "eukaryote"} for row in metrics
                    ),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
