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
    manifest.write_text("sample_id\tmode\tread1\tread2\tread_qc_status\tread_platform\nx\tlong_isolate\treads.fastq\t\tfailed\tont\n")
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


def test_long_read_platform_selects_the_matching_flye_flag(tmp_path):
    """Flye needs the read chemistry. Running --nano-hq on PacBio CLR reads
    assembles them under the wrong error model."""
    reads = tmp_path / "reads.fastq"
    reads.write_text("@x\nAC\n+\nII\n")
    expected = {"ont": "--nano-hq", "pacbio-clr": "--pacbio-raw", "pacbio-hifi": "--pacbio-hifi"}
    for platform, flag in expected.items():
        manifest = tmp_path / f"{platform}.tsv"
        manifest.write_text(
            "sample_id\tmode\tread1\tread2\tread_qc_status\tread_platform\n"
            f"x\tlong_isolate\treads.fastq\t\tpassed\t{platform}\n"
        )
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(manifest), "--out", str(tmp_path / f"out-{platform}")],
            text=True, capture_output=True,
        )
        assert result.returncode == 0, result.stderr
        plan = (tmp_path / f"out-{platform}" / "run_manifest.json").read_text()
        assert flag in plan, (platform, plan)
        for other in set(expected.values()) - {flag}:
            assert other not in plan, (platform, other)


def test_unknown_long_read_platform_is_rejected(tmp_path):
    manifest = tmp_path / "assemblies.tsv"
    manifest.write_text(
        "sample_id\tmode\tread1\tread2\tread_qc_status\tread_platform\n"
        "x\tlong_isolate\treads.fastq\t\tpassed\tnanopore\n"
    )
    (tmp_path / "reads.fastq").write_text("@x\nAC\n+\nII\n")
    result = subprocess.run([sys.executable, str(SCRIPT), str(manifest), "--out", str(tmp_path / "out")], text=True, capture_output=True)
    assert result.returncode != 0
    assert "requires read_platform" in result.stderr


def test_long_read_mode_requires_declared_chemistry(tmp_path):
    manifest = tmp_path / "assemblies.tsv"
    manifest.write_text(
        "sample_id\tmode\tread1\tread2\tread_qc_status\tread_platform\n"
        "x\tlong_isolate\treads.fastq\t\tpassed\t\n"
    )
    (tmp_path / "reads.fastq").write_text("@x\nAC\n+\nII\n")
    result = subprocess.run([sys.executable, str(SCRIPT), str(manifest), "--out", str(tmp_path / "out")], text=True, capture_output=True)
    assert result.returncode != 0
    assert "requires read_platform" in result.stderr


def test_hifi_mode_rejects_contradictory_chemistry(tmp_path):
    manifest = tmp_path / "assemblies.tsv"
    manifest.write_text(
        "sample_id\tmode\tread1\tread2\tread_qc_status\tread_platform\n"
        "x\thifi_metagenome\treads.fastq\t\tpassed\tpacbio-clr\n"
    )
    (tmp_path / "reads.fastq").write_text("@x\nAC\n+\nII\n")
    result = subprocess.run([sys.executable, str(SCRIPT), str(manifest), "--out", str(tmp_path / "out")], text=True, capture_output=True)
    assert result.returncode != 0
    assert "cannot use read_platform" in result.stderr
