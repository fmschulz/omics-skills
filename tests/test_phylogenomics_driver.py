import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "bio-phylogenomics"
SCRIPT = SKILL / "scripts" / "run_phylogenomics.py"


def test_plan_is_seeded_and_checksummed(tmp_path):
    out = tmp_path / "out"
    result = subprocess.run([sys.executable, str(SCRIPT), str(SKILL / "fixtures" / "markers.tsv"), "--references", str(SKILL / "fixtures" / "references.tsv"), "--out", str(out), "--seed", "41"], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    plan = json.loads((out / "run_manifest.json").read_text())
    assert plan["seed"] == 41
    assert [step["stage"] for step in plan["steps"]] == ["alignment", "trimming", "tree", "normalize_support"]
    assert "41" in plan["steps"][2]["command"]


def test_execute_reuses_complete_outputs_without_calling_tools(tmp_path):
    out = tmp_path / "out"
    args = [sys.executable, str(SCRIPT), str(SKILL / "fixtures" / "markers.tsv"), "--references", str(SKILL / "fixtures" / "references.tsv"), "--out", str(out), "--seed", "41"]
    first = subprocess.run(args, text=True, capture_output=True)
    assert first.returncode == 0, first.stderr
    manifest = json.loads((out / "run_manifest.json").read_text())
    for step in manifest["steps"]:
        for output in step["outputs"]:
            path = Path(output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("(a:1,b:1)95;\n" if step["stage"] == "tree" else "fixture output\n")
        (Path(step["outputs"][0]).parent / f"{step['stage']}.done").write_text("complete\n")
    second = subprocess.run([*args, "--execute"], text=True, capture_output=True)
    assert second.returncode == 0, second.stderr
    rerun = json.loads((out / "run_manifest.json").read_text())
    assert {step["status"] for step in rerun["steps"]} == {"reused"}


def test_execute_does_not_reuse_unmarked_partial_outputs(tmp_path):
    out = tmp_path / "out"
    args = [
        sys.executable,
        str(SCRIPT),
        str(SKILL / "fixtures" / "markers.tsv"),
        "--references",
        str(SKILL / "fixtures" / "references.tsv"),
        "--out",
        str(out),
        "--seed",
        "41",
    ]
    first = subprocess.run(args, text=True, capture_output=True)
    assert first.returncode == 0, first.stderr
    manifest = json.loads((out / "run_manifest.json").read_text())
    for step in manifest["steps"]:
        for output in step["outputs"]:
            path = Path(output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("partial output\n")

    tool_dir = tmp_path / "bin"
    tool_dir.mkdir()
    mafft = tool_dir / "mafft"
    mafft.write_text("#!/bin/sh\nexit 42\n")
    mafft.chmod(0o755)
    env = {**os.environ, "PATH": f"{tool_dir}:{os.environ['PATH']}"}
    rerun = subprocess.run([*args, "--execute"], text=True, capture_output=True, env=env)
    assert rerun.returncode != 0
    assert "alignment command failed with exit 42" in rerun.stderr


def test_supports_are_normalized_to_zero_one(tmp_path):
    out = tmp_path / "support.tsv"
    result = subprocess.run([sys.executable, str(SCRIPT), "--normalize-only", str(SKILL / "fixtures" / "tree.nwk"), "--out", str(out)], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert "95\t0.950000" in out.read_text()


def test_iqtree_dual_support_labels_are_normalized_separately(tmp_path):
    tree = tmp_path / "iqtree.treefile"
    tree.write_text("((a:1,b:1)98.7/100:1,c:1)91/75;\n")
    out = tmp_path / "support.tsv"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--normalize-only", str(tree), "--out", str(out)],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    rows = out.read_text().splitlines()
    assert "1\tsh_alrt\t98.7\t0.987000" in rows
    assert "1\tufboot\t100\t1.000000" in rows
    assert "2\tsh_alrt\t91\t0.910000" in rows
    assert "2\tufboot\t75\t0.750000" in rows


def test_reference_checksum_mismatch_is_rejected(tmp_path):
    refs = tmp_path / "references.tsv"
    refs.write_text(f"accession\tpath\tsha256\nrelative\t{SKILL / 'fixtures' / 'reference.faa'}\tdeadbeef\n")
    result = subprocess.run([sys.executable, str(SCRIPT), str(SKILL / "fixtures" / "markers.tsv"), "--references", str(refs), "--out", str(tmp_path / "out")], text=True, capture_output=True)
    assert result.returncode != 0
    assert "checksum mismatch" in result.stderr
