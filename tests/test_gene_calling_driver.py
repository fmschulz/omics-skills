import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "bio-gene-calling"
SCRIPT = SKILL / "scripts" / "run_gene_calling.py"


def test_domain_routes_and_per_assembly_outputs(tmp_path):
    out = tmp_path / "out"
    result = subprocess.run([sys.executable, str(SCRIPT), str(SKILL / "fixtures" / "assemblies.tsv"), "--tool-manifest", str(SKILL / "fixtures" / "tool-manifest.json"), "--out", str(out)], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    manifest = json.loads((out / "run_manifest.json").read_text())
    callers = {step["assembly_id"]: step["caller"] for step in manifest["steps"] if step["stage"] == "gene_calling"}
    assert callers == {"bacterium": "pyrodigal", "virus": "pyrodigal-gv", "eukaryote": "braker4"}
    assert all(f"/{step['assembly_id']}/" in step["outputs"][0] for step in manifest["steps"] if step["stage"] == "gene_calling")
    census = (out / "ncRNA_census.tsv").read_text()
    assert "RF00177\tdefault" in census and "RF00177\trelaxed" in census
    braker = next(step for step in manifest["steps"] if step.get("caller") == "braker4")
    assert braker["command"][0] == "snakemake"
    assert "$BIO_DB_ROOT" not in json.dumps(manifest)
    assert (out / "eukaryote" / "braker4" / "samples.csv").is_file()
    assert (out / "eukaryote" / "braker4" / "config.ini").is_file()


def test_unpinned_braker_revision_is_rejected(tmp_path):
    tools = json.loads((SKILL / "fixtures" / "tool-manifest.json").read_text())
    tools["braker4"]["repository_revision"] = "main"
    manifest = tmp_path / "tools.json"
    manifest.write_text(json.dumps(tools))
    result = subprocess.run([sys.executable, str(SCRIPT), str(SKILL / "fixtures" / "assemblies.tsv"), "--tool-manifest", str(manifest), "--out", str(tmp_path / "out")], text=True, capture_output=True)
    assert result.returncode != 0
    assert "40-character Git commit" in result.stderr


def test_plan_is_idempotent_and_execute_reuses_complete_outputs(tmp_path):
    out = tmp_path / "out"
    args = [sys.executable, str(SCRIPT), str(SKILL / "fixtures" / "assemblies.tsv"), "--tool-manifest", str(SKILL / "fixtures" / "tool-manifest.json"), "--out", str(out)]
    first = subprocess.run(args, text=True, capture_output=True)
    assert first.returncode == 0, first.stderr
    second = subprocess.run(args, text=True, capture_output=True)
    assert second.returncode == 0, second.stderr
    manifest = json.loads((out / "run_manifest.json").read_text())
    for step in manifest["steps"]:
        for output in step["outputs"]:
            path = Path(output)
            path.parent.mkdir(parents=True, exist_ok=True)
            if step["stage"] == "trna":
                path.write_text("Sequence tRNA # Begin End Type Codon IntronBegin IntronEnd Score\nseq 1 1 70 Ala TGC 0 0 55.0\n")
            elif step["stage"] == "rrna":
                path.write_text(
                    "# cmsearch tblout\n"
                    "seq - SSU RF00177 cm 1 10 1 10 + no 1 0.5 0.0 42.0 1e-10 ! hit\n"
                    "seq - SSU RF00177 cm 1 10 30 40 + no 1 0.5 0.0 9.0 2.1 ? weak\n"
                )
            else:
                path.write_text("fixture output\n")
    executed = subprocess.run([*args, "--execute"], text=True, capture_output=True)
    assert executed.returncode == 0, executed.stderr
    rerun = json.loads((out / "run_manifest.json").read_text())
    assert {step["status"] for step in rerun["steps"]} == {"reused"}
    census = (out / "ncRNA_census.tsv").read_text()
    assert "bacterium\trRNA\tInfernal\tRF00177\trelaxed\t1\tcompleted" in census


def test_trnascan_mode_and_viral_rrna_row_follow_domain(tmp_path):
    out = tmp_path / "out"
    args = [
        sys.executable,
        str(SCRIPT),
        str(SKILL / "fixtures" / "assemblies.tsv"),
        "--tool-manifest",
        str(SKILL / "fixtures" / "tool-manifest.json"),
        "--out",
        str(out),
        "--threads",
        "2",
    ]

    result = subprocess.run(args, text=True, capture_output=True, check=False)

    assert result.returncode == 0, result.stderr
    steps = json.loads((out / "run_manifest.json").read_text())["steps"]
    trna_flags = {
        step["assembly_id"]: step["command"][1]
        for step in steps
        if step["stage"] == "trna"
    }
    assert trna_flags == {"bacterium": "-B", "virus": "-G", "eukaryote": "-E"}
    assert (
        "virus\trRNA\tInfernal\tnone\tNA\tNA\tnot screened"
        in (out / "ncRNA_census.tsv").read_text()
    )


def test_unknown_mode_is_rejected(tmp_path):
    manifest = tmp_path / "assemblies.tsv"
    fasta = (SKILL / "fixtures" / "bacterium.fna").resolve()
    manifest.write_text(
        f"assembly_id\tdomain\tmode\tfasta\nbacterium\tbacteria\tmeta\t{fasta}\n"
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(manifest),
            "--tool-manifest",
            str(SKILL / "fixtures" / "tool-manifest.json"),
            "--out",
            str(tmp_path / "out"),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "mode for bacterium" in result.stderr


FAKE_TRNASCAN = """#!/bin/sh
out=""
while [ $# -gt 0 ]; do [ "$1" = -o ] && out=$2; shift; done
: > "$out"
echo run >> "$FAKE_LOG"
exit "$FAKE_STATUS"
"""


def test_failed_empty_trna_output_is_rerun_not_reused(tmp_path: Path) -> None:
    """A failed tRNAscan-SE run that leaves an empty table must rerun on retry."""
    out = tmp_path / "out"
    args = [
        sys.executable,
        str(SCRIPT),
        str(SKILL / "fixtures" / "assemblies.tsv"),
        "--tool-manifest",
        str(SKILL / "fixtures" / "tool-manifest.json"),
        "--out",
        str(out),
    ]
    planned = subprocess.run(args, text=True, capture_output=True, check=False)
    assert planned.returncode == 0, planned.stderr
    steps = json.loads((out / "run_manifest.json").read_text())["steps"]
    for step in steps:
        if step["stage"] == "trna":
            continue
        for output in step["outputs"]:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            Path(output).write_text("fixture output\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "tRNAscan-SE"
    fake.write_text(FAKE_TRNASCAN)
    fake.chmod(0o755)
    log = tmp_path / "trnascan.log"
    env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}
    env["FAKE_LOG"] = str(log)

    def run(status: int) -> subprocess.CompletedProcess[str]:
        env["FAKE_STATUS"] = str(status)
        return subprocess.run(
            [*args, "--execute"], text=True, capture_output=True, env=env, check=False
        )

    failed = run(1)
    assert failed.returncode == 2
    assert (out / "bacterium" / "trnascan.tsv").stat().st_size == 0

    retried = run(0)
    assert retried.returncode == 0, retried.stderr
    assert len(log.read_text().splitlines()) == 4
    trna = [
        s
        for s in json.loads((out / "run_manifest.json").read_text())["steps"]
        if s["stage"] == "trna"
    ]
    assert {step["status"] for step in trna} == {"completed"}
    census = (out / "ncRNA_census.tsv").read_text()
    assert "bacterium\ttRNA\ttRNAscan-SE\tall\tdefault\t0\tcompleted" in census

    reused = run(0)
    assert reused.returncode == 0, reused.stderr
    assert len(log.read_text().splitlines()) == 4
    trna = [
        s
        for s in json.loads((out / "run_manifest.json").read_text())["steps"]
        if s["stage"] == "trna"
    ]
    assert {step["status"] for step in trna} == {"reused"}
