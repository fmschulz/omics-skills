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
CALLERS = {"bacteria": "pyrodigal", "archaea": "pyrodigal", "virus": "pyrodigal-gv", "eukaryota": "braker4"}
RFAM = {
    "bacteria": ["RF00177", "RF02541", "RF00001"],
    "archaea": ["RF01959", "RF02540", "RF00001"],
    "virus": [],
    "eukaryota": ["RF01960", "RF02543", "RF00002", "RF00001"],
}
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
        fasta = Path(row["fasta"])
        fasta = fasta if fasta.is_absolute() else path.parent / fasta
        if not fasta.is_file() or fasta.stat().st_size == 0:
            raise ValueError(f"FASTA is missing or empty for {assembly}: {fasta}")
        row.update(assembly_id=assembly, domain=domain, fasta=str(fasta.resolve()), input_sha256=sha256(fasta))
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


def build_plan(rows: list[dict[str, str]], out: Path, tools: dict[str, object]) -> list[dict[str, object]]:
    plan: list[dict[str, object]] = []
    for row in rows:
        assembly, domain = row["assembly_id"], row["domain"]
        target = out / assembly
        caller = CALLERS[domain]
        if caller == "pyrodigal":
            common_outputs = [target / "genes.gff3", target / "proteins.faa", target / "cds.fna"]
            command = ["pyrodigal", "-i", row["fasta"], "-o", str(common_outputs[0]), "-a", str(common_outputs[1]), "-d", str(common_outputs[2])]
            if row["mode"] == "metagenome":
                command.extend(["-p", "meta"])
        elif caller == "pyrodigal-gv":
            common_outputs = [target / "genes.gff3", target / "proteins.faa", target / "cds.fna"]
            command = ["pyrodigal-gv", "-i", row["fasta"], "-o", str(common_outputs[0]), "-a", str(common_outputs[1]), "-d", str(common_outputs[2])]
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
                "snakemake", "--snakefile", braker["snakefile"], "--directory", str(work),
                "--cores", "8", "--use-singularity", "--singularity-prefix",
                str(work / ".singularity_cache"), "--latency-wait", "120", "--restart-times", "3",
            ]
        plan.append({"assembly_id": assembly, "stage": "gene_calling", "caller": caller, "command": command, "outputs": list(map(str, common_outputs))})
        plan.append({"assembly_id": assembly, "stage": "trna", "command": ["tRNAscan-SE", "-o", str(target / "trnascan.tsv"), row["fasta"]], "outputs": [str(target / "trnascan.tsv")]})
        for model in RFAM[domain]:
            for threshold in ("default", "relaxed"):
                command = ["cmsearch", "--rfam", "--nohmmonly", "--tblout", str(target / f"{model}.{threshold}.tbl")]
                if threshold == "default":
                    command.append("--cut_ga")
                command.extend([tools["rfam"]["models"][model]["path"], row["fasta"]])
                plan.append({"assembly_id": assembly, "stage": "rrna", "model": model, "threshold": threshold, "command": command, "outputs": [str(target / f"{model}.{threshold}.tbl")]})
    return plan


def complete(step: dict[str, object]) -> bool:
    return all(Path(path).is_file() and Path(path).stat().st_size > 0 for path in step["outputs"])


def execute(plan: list[dict[str, object]]) -> None:
    for step in plan:
        if complete(step):
            step["status"] = "reused"
            continue
        for output in step["outputs"]:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(step["command"], check=False)
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
    return sum(
        bool(line.strip()) and not line.startswith("#")
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
    )


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
            for model in RFAM[row["domain"]]:
                for threshold in ("default", "relaxed"):
                    rrna = steps[(row["assembly_id"], "rrna", model, threshold)]
                    count = count_cmsearch(Path(rrna["outputs"][0])) if executed else "NA"
                    handle.write(
                        f"{row['assembly_id']}\trRNA\tInfernal\t{model}\t{threshold}\t{count}\t{note}\n"
                    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("assemblies", type=Path)
    parser.add_argument("--tool-manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        rows = load_manifest(args.assemblies.resolve())
        tools = load_tools(args.tool_manifest.resolve())
        args.out.mkdir(parents=True, exist_ok=True)
        plan = build_plan(rows, args.out.resolve(), tools)
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
