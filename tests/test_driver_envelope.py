import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
SKILLS = ROOT / "skills"
UV = ("uv", "run", "--script")
PY = (sys.executable,)

DRIVERS = {
    "bio-annotation": (UV, "build_annotation_artifacts.py", lambda f: [f / "annotations.tsv", "--genomes", f / "genomes.tsv", "--markers", f / "markers.tsv"]),
    "bio-assembly-qc": (PY, "run_assembly_qc.py", lambda f: [f / "assemblies.tsv"]),
    "bio-gene-calling": (PY, "run_gene_calling.py", lambda f: [f / "assemblies.tsv", "--tool-manifest", f / "tool-manifest.json"]),
    "bio-interdomain-hgt": (UV, "run_hgt_evidence.py", lambda f: [f / "forward_hits.tsv", "--arbiter-hits", f / "arbiter_hits.tsv", "--reciprocal", f / "reciprocal.tsv", "--context", f / "context.tsv", "--trees", f / "trees.tsv", "--sampling-depth", f / "sampling_depth.tsv", "--databases", f / "databases.json", "--hypotheses", f / "hypotheses.tsv", "--reflections", f / "reflections.tsv", "--query-domain", "ncldv"]),
    "bio-phylogenomics": (PY, "run_phylogenomics.py", lambda f: [f / "markers.tsv", "--references", f / "references.tsv", "--seed", "41"]),
    "bio-protein-clustering-pangenome": (UV, "build_pangenome_artifacts.py", lambda f: [f / "orthogroups.tsv", "--genomes", f / "genomes.tsv", "--marker-catalog", f / "marker_catalog.tsv", "--marker-hits", f / "marker_hits.tsv", "--ncrna", f / "ncRNA_census.tsv"]),
    "bio-reads-qc-mapping": (UV, "run_reads_qc_mapping.py", lambda f: [f / "sample_sheet.tsv"]),
    "bio-viromics": (UV, "build_viromics_evidence.py", lambda f: [f / "metrics.tsv", "--resources", f / "resources.json", "--hypotheses", f / "hypotheses.tsv", "--reflections", f / "reflections.tsv", "--comparative-dir", f / "comparative"]),
}


def run(skill, inputs, out):
    launcher, script, _ = DRIVERS[skill]
    return subprocess.run([*launcher, str(SKILLS / skill / "scripts" / script), *map(str, inputs), "--out", str(out)], text=True, capture_output=True)


def envelope(result):
    return json.loads([line for line in result.stdout.splitlines() if line.strip()][-1])


@pytest.mark.parametrize("skill", sorted(DRIVERS))
def test_success_envelope(skill, tmp_path):
    out = tmp_path / "out"
    result = run(skill, DRIVERS[skill][2](SKILLS / skill / "fixtures"), out)
    assert result.returncode == 0, result.stderr
    payload = envelope(result)
    assert payload["ok"] is True
    assert payload["skill"] == skill
    assert Path(payload["out"]).is_absolute() and Path(payload["out"]).is_dir()
    if skill == "bio-protein-clustering-pangenome":
        assert "manifest" not in payload
    else:
        assert Path(payload["manifest"]).is_file()


def annotation_failure(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    (out / "keep").write_text("user data")
    return DRIVERS["bio-annotation"][2](SKILLS / "bio-annotation" / "fixtures"), out


def assembly_failure(tmp_path):
    manifest = tmp_path / "assemblies.tsv"
    manifest.write_text("sample_id\tmode\tread1\tread2\tread_qc_status\nx\tlong_isolate\treads.fastq\t\tfailed\n")
    (tmp_path / "reads.fastq").write_text("@x\nAC\n+\nII\n")
    return [manifest], tmp_path / "out"


@pytest.mark.parametrize("skill, setup", [("bio-annotation", annotation_failure), ("bio-assembly-qc", assembly_failure)])
def test_failure_envelope(skill, setup, tmp_path):
    inputs, out = setup(tmp_path)
    result = run(skill, inputs, out)
    assert result.returncode == 2
    payload = envelope(result)
    assert payload["ok"] is False
    assert payload["skill"] == skill
    assert payload["error"]["code"] and payload["error"]["message"]
    assert payload["error"]["message"] in result.stderr
