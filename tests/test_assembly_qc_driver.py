import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "bio-assembly-qc"
SCRIPT = SKILL / "scripts" / "run_assembly_qc.py"


def test_fixture_plans_short_long_and_metagenome_workflows(tmp_path):
    out = tmp_path / "out"
    result = subprocess.run([sys.executable, str(SCRIPT), str(SKILL / "fixtures" / "assemblies.tsv"), "--out", str(out)], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    plan = json.loads((out / "run_manifest.json").read_text())
    commands = [step.get("command", [""])[0] for step in plan["steps"]]
    assert {"spades.py", "flye", "metaspades.py", "quast.py", "metaquast.py"} <= set(commands)
    assert all(step["outputs"] for step in plan["steps"])


def test_failed_read_qc_blocks_assembly(tmp_path):
    manifest = tmp_path / "assemblies.tsv"
    manifest.write_text("sample_id\tmode\tread1\tread2\tread_qc_status\nx\tlong_isolate\treads.fastq\t\tfailed\n")
    (tmp_path / "reads.fastq").write_text("@x\nAC\n+\nII\n")
    result = subprocess.run([sys.executable, str(SCRIPT), str(manifest), "--out", str(tmp_path / "out")], text=True, capture_output=True)
    assert result.returncode != 0
    assert "read_qc_status must be passed" in result.stderr


def test_execute_reuses_complete_outputs_without_calling_tools(tmp_path):
    out = tmp_path / "out"
    args = [sys.executable, str(SCRIPT), str(SKILL / "fixtures" / "assemblies.tsv"), "--out", str(out)]
    first = subprocess.run(args, text=True, capture_output=True)
    assert first.returncode == 0, first.stderr
    manifest = json.loads((out / "run_manifest.json").read_text())
    for step in manifest["steps"]:
        for output in step["outputs"]:
            path = Path(output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture output\n")
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
        str(SKILL / "fixtures" / "assemblies.tsv"),
        "--out",
        str(out),
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
    spades = tool_dir / "spades.py"
    spades.write_text("#!/bin/sh\nexit 42\n")
    spades.chmod(0o755)
    env = {**os.environ, "PATH": f"{tool_dir}:{os.environ['PATH']}"}
    rerun = subprocess.run([*args, "--execute"], text=True, capture_output=True, env=env)
    assert rerun.returncode != 0
    assert "assembly command failed with exit 42" in rerun.stderr
