#!/usr/bin/env python3
"""Build a pinned, per-assembly gene-calling and ncRNA execution plan."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

FIELDS = ("assembly_id", "domain", "mode", "fasta")
DOMAINS = {"bacteria", "archaea", "virus", "eukaryota"}
MODES = {"single", "metagenome"}
CALLERS = {"bacteria": "pyrodigal", "archaea": "pyrodigal", "virus": "pyrodigal-gv", "eukaryota": "braker4"}
RFAM = {
    "bacteria": ["RF00177", "RF02541", "RF00001"],
    "archaea": ["RF01959", "RF02540", "RF00001"],
    "virus": [],
    "eukaryota": ["RF01960", "RF02543", "RF00002", "RF00001"],
}
# tRNAscan-SE defaults to eukaryotic models, so every domain passes its own flag.
# Viruses use the general model because they carry host-derived tRNA genes.
TRNASCAN_MODE = {"bacteria": "-B", "archaea": "-A", "virus": "-G", "eukaryota": "-E"}
BRAKER4_SAMPLE_FIELDS = (
    "sample_name", "genome", "genome_masked", "protein_fasta", "bam_files",
    "fastq_r1", "fastq_r2", "sra_ids", "varus_genus", "varus_species",
    "isoseq_bam", "isoseq_fastq", "busco_lineage", "reference_gtf",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_if_same(path: Path, content: str) -> None:
    if path.exists():
        if path.read_text(encoding="utf-8") != content:
            raise ValueError(f"existing generated configuration differs: {path}")
        return
    path.write_text(content, encoding="utf-8")


def load_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError(f"assembly manifest columns must be exactly: {', '.join(FIELDS)}")
        rows = list(reader)
    if not rows:
        raise ValueError("assembly manifest has no rows")
    seen: set[str] = set()
    for row in rows:
        assembly, domain = row["assembly_id"].strip(), row["domain"].strip().lower()
        if not assembly or assembly in seen:
            raise ValueError(f"assembly_id must be non-empty and unique: {assembly!r}")
        if domain not in DOMAINS:
            raise ValueError(f"unsupported domain for {assembly}: {domain}")
        mode = row["mode"].strip().lower()
        if mode not in MODES:
            raise ValueError(
                f"mode for {assembly} must be one of {sorted(MODES)}, got {mode!r}"
            )
        fasta = Path(row["fasta"])
        fasta = fasta if fasta.is_absolute() else path.parent / fasta
        if not fasta.is_file() or fasta.stat().st_size == 0:
            raise ValueError(f"FASTA is missing or empty for {assembly}: {fasta}")
        row.update(
            assembly_id=assembly,
            domain=domain,
            mode=mode,
            fasta=str(fasta.resolve()),
            input_sha256=sha256(fasta),
        )
        seen.add(assembly)
    return rows


def load_tools(path: Path) -> dict[str, object]:
    tools = json.loads(path.read_text(encoding="utf-8"))
    required = {"schema_version", "pyrodigal", "pyrodigal-gv", "braker4", "trnascan-se", "infernal", "rfam"}
    if set(tools) != required:
        raise ValueError(f"tool manifest keys must be exactly: {', '.join(sorted(required))}")
    for name in required - {"schema_version", "rfam"}:
        if not tools[name].get("version"):
            raise ValueError(f"tool manifest is missing {name}.version")
    braker = tools["braker4"]
    if not re.fullmatch(r"[0-9a-f]{40}", braker.get("repository_revision", "")):
        raise ValueError("braker4.repository_revision must be a 40-character Git commit")
    for field in ("snakefile", "container_lock"):
        target = Path(braker.get(field, ""))
        target = target if target.is_absolute() else path.parent / target
        expected = braker.get(f"{field}_sha256", "")
        if not target.is_file() or target.stat().st_size == 0 or sha256(target) != expected:
            raise ValueError(f"braker4 {field} is missing, empty, or checksum-mismatched")
        braker[field] = str(target.resolve())
    rfam = tools["rfam"]
    required_models = set().union(*RFAM.values())
    if not rfam.get("version") or set(rfam.get("models", {})) != required_models:
        raise ValueError("rfam version and checksummed records for every required model are required")
    for model, item in rfam["models"].items():
        target = Path(item.get("path", ""))
        target = target if target.is_absolute() else path.parent / target
        if not target.is_file() or target.stat().st_size == 0 or sha256(target) != item.get("sha256"):
            raise ValueError(f"Rfam model is missing, empty, or checksum-mismatched: {model}")
        item["path"] = str(target.resolve())
    return tools


def build_plan(
    rows: list[dict[str, str]], out: Path, tools: dict[str, object], threads: int
) -> list[dict[str, object]]:
    """Return one gene-calling, tRNA, and rRNA step list per assembly."""
    plan: list[dict[str, object]] = []
    for row in rows:
        assembly, domain = row["assembly_id"], row["domain"]
        target = out / assembly
        caller = CALLERS[domain]
        if caller == "pyrodigal":
            common_outputs = [target / "genes.gff3", target / "proteins.faa", target / "cds.fna"]
            command = ["pyrodigal", "-i", row["fasta"], "-o", str(common_outputs[0]), "-a", str(common_outputs[1]), "-d", str(common_outputs[2])]
            mode = "meta" if row["mode"] == "metagenome" else "single"
            command.extend(["-f", "gff", "-p", mode, "-j", str(threads)])
        elif caller == "pyrodigal-gv":
            common_outputs = [target / "genes.gff3", target / "proteins.faa", target / "cds.fna"]
            command = ["pyrodigal-gv", "-i", row["fasta"], "-o", str(common_outputs[0]), "-a", str(common_outputs[1]), "-d", str(common_outputs[2])]
            # The viral models are used only in metagenomic mode.
            command.extend(["-f", "gff", "-p", "meta", "-j", str(threads)])
        else:
            work = target / "braker4"
            work.mkdir(parents=True, exist_ok=True)
            samples = work / "samples.csv"
            buffer = io.StringIO(newline="")
            writer = csv.DictWriter(buffer, fieldnames=BRAKER4_SAMPLE_FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerow({"sample_name": assembly, "genome": row["fasta"]})
            write_if_same(samples, buffer.getvalue())
            config = work / "config.ini"
            write_if_same(
                config,
                f"[paths]\nsamples_file = {samples}\naugustus_config_path = {work / 'augustus_config'}\n\n"
                "[parameters]\nrun_ncrna = 0\n",
            )
            results = work / "output" / assembly / "results"
            common_outputs = [results / "braker.gff3.gz", results / "braker.aa.gz", results / "braker.codingseq.gz"]
            braker = tools["braker4"]
            command = [
                "snakemake",
                "--snakefile",
                braker["snakefile"],
                "--directory",
                str(work),
                "--cores",
                str(threads),
                "--use-singularity",
                "--singularity-prefix",
                str(work / ".singularity_cache"),
                "--latency-wait",
                "120",
                "--restart-times",
                "3",
            ]
        plan.append({"assembly_id": assembly, "stage": "gene_calling", "caller": caller, "command": command, "outputs": list(map(str, common_outputs))})
        trna_table = target / "trnascan.tsv"
        trna_command = [
            "tRNAscan-SE",
            TRNASCAN_MODE[domain],
            "-Q",
            "--thread",
            str(threads),
            "-o",
            str(trna_table),
            row["fasta"],
        ]
        # A run that finds no tRNA genes can leave the table empty or absent.
        plan.append(
            {
                "assembly_id": assembly,
                "stage": "trna",
                "command": trna_command,
                "outputs": [str(trna_table)],
                "allow_empty": True,
            }
        )
        for model in RFAM[domain]:
            for threshold in ("default", "relaxed"):
                command = [
                    "cmsearch",
                    "--rfam",
                    "--nohmmonly",
                    "--cpu",
                    str(threads),
                    "-o",
                    str(target / f"{model}.{threshold}.cmsearch.txt"),
                    "--tblout",
                    str(target / f"{model}.{threshold}.tbl"),
                ]
                if threshold == "default":
                    command.append("--cut_ga")
                command.extend([tools["rfam"]["models"][model]["path"], row["fasta"]])
                plan.append({"assembly_id": assembly, "stage": "rrna", "model": model, "threshold": threshold, "command": command, "outputs": [str(target / f"{model}.{threshold}.tbl")]})
    return plan


def done_marker(output: str) -> Path:
    """Return the marker that records a zero exit for an output allowed to be empty."""
    return Path(f"{output}.done")


def complete(step: dict[str, object]) -> bool:
    """Report whether every declared output exists and is non-empty.

    An empty output counts only for steps that allow it and only when its done
    marker shows that the run that wrote it exited 0.
    """
    allow_empty = bool(step.get("allow_empty"))
    return all(
        Path(path).is_file()
        and (
            Path(path).stat().st_size > 0
            or (allow_empty and done_marker(path).is_file())
        )
        for path in step["outputs"]
    )


def execute(plan: list[dict[str, object]]) -> None:
    for step in plan:
        if complete(step):
            step["status"] = "reused"
            continue
        for output in step["outputs"]:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            done_marker(output).unlink(missing_ok=True)
        result = subprocess.run(step["command"], check=False)
        if result.returncode == 0 and step.get("allow_empty"):
            for output in step["outputs"]:
                Path(output).touch()
                done_marker(output).touch()
        if result.returncode or not complete(step):
            raise RuntimeError(
                f"{step['stage']} failed or produced an empty output: {shlex.join(step['command'])}"
            )
        step["status"] = "completed"


def count_trnascan(path: Path) -> int:
    count = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        fields = line.split()
        if len(fields) >= 9 and fields[1].isdigit():
            count += 1
    return count


def count_cmsearch(path: Path) -> int:
    """Count hits that pass the inclusion threshold (`!` in the tblout inc column).

    With `--cut_ga` every reported hit passes. Without it, cmsearch also reports
    hits up to E = 10 marked `?`, which are not counted.
    """
    count = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        fields = line.split()
        if not line.startswith("#") and len(fields) > 16 and fields[16] == "!":
            count += 1
    return count


def write_census(path: Path, rows: list[dict[str, str]], plan: list[dict[str, object]], executed: bool) -> None:
    steps = {(step["assembly_id"], step["stage"], step.get("model"), step.get("threshold")): step for step in plan}
    with path.open("w", encoding="utf-8") as handle:
        handle.write("assembly\tclass\ttool\tmodel\tthreshold\tcount\tnotes\n")
        for row in rows:
            trna = steps[(row["assembly_id"], "trna", None, None)]
            trna_count = count_trnascan(Path(trna["outputs"][0])) if executed else "NA"
            note = "completed" if executed else "pending execution"
            handle.write(
                f"{row['assembly_id']}\ttRNA\ttRNAscan-SE\tall\tdefault\t{trna_count}\t{note}\n"
            )
            if not RFAM[row["domain"]]:
                handle.write(
                    f"{row['assembly_id']}\trRNA\tInfernal\tnone\tNA\tNA\t"
                    "not screened: no domain-specific Rfam rRNA set for viruses\n"
                )
            for model in RFAM[row["domain"]]:
                for threshold in ("default", "relaxed"):
                    rrna = steps[(row["assembly_id"], "rrna", model, threshold)]
                    count = count_cmsearch(Path(rrna["outputs"][0])) if executed else "NA"
                    handle.write(
                        f"{row['assembly_id']}\trRNA\tInfernal\t{model}\t{threshold}\t{count}\t{note}\n"
                    )


def positive_int(value: str) -> int:
    """Parse a thread count for argparse."""
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError(f"must be at least 1, got {number}")
    return number


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("assemblies", type=Path)
    parser.add_argument("--tool-manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--threads",
        type=positive_int,
        default=8,
        help="threads for each tool (pyrodigal -j, tRNAscan-SE, cmsearch, BRAKER4)",
    )
    args = parser.parse_args()
    try:
        rows = load_manifest(args.assemblies.resolve())
        tools = load_tools(args.tool_manifest.resolve())
        args.out.mkdir(parents=True, exist_ok=True)
        plan = build_plan(rows, args.out.resolve(), tools, args.threads)
        if args.execute:
            execute(plan)
        payload = {"schema_version": "1.0", "tools": tools, "assemblies": rows, "steps": plan}
        (args.out / "run_manifest.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        write_census(args.out / "ncRNA_census.tsv", rows, plan, args.execute)
        out = args.out.resolve()
        print(json.dumps({"ok": True, "skill": "bio-gene-calling", "out": str(out), "manifest": str(out / "run_manifest.json"), "warnings": []}))
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "skill": "bio-gene-calling", "error": {"code": type(error).__name__, "message": str(error)}}))
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
