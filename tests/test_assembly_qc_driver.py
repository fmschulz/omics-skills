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
    assert {
        "spades.py",
        "flye",
        "metaspades.py",
        "metaMDBG",
        "quast.py",
        "metaquast.py",
    } <= set(commands)
    assert all(step["outputs"] for step in plan["steps"])


def test_fixture_plans_the_expected_tool_for_every_mode(tmp_path):
    out = tmp_path / "out"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(SKILL / "fixtures" / "assemblies.tsv"),
            "--out",
            str(out),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    plan = json.loads((out / "run_manifest.json").read_text())
    modes = {row["sample_id"]: row["mode"] for row in plan["assemblies"]}
    assert set(modes.values()) == {
        "short_isolate",
        "long_isolate",
        "short_metagenome",
        "long_metagenome",
        "hifi_metagenome",
    }
    commands = {
        (step["sample_id"], step["stage"]): step["command"]
        for step in plan["steps"]
        if "command" in step
    }
    expected = {
        "short_isolate": ("spades.py", "quast.py"),
        "long_isolate": ("flye", "quast.py"),
        "short_metagenome": ("metaspades.py", "metaquast.py"),
        "long_metagenome": ("flye", "metaquast.py"),
        "hifi_metagenome": ("metaMDBG", "metaquast.py"),
    }
    for sample, mode in modes.items():
        assembler, qc_tool = expected[mode]
        assert commands[(sample, "assembly")][0] == assembler, mode
        assert commands[(sample, "qc")][0] == qc_tool, mode
    long_meta = next(
        sample for sample, mode in modes.items() if mode == "long_metagenome"
    )
    assert "--meta" in commands[(long_meta, "assembly")]
    hifi = next(sample for sample, mode in modes.items() if mode == "hifi_metagenome")
    assert "--in-hifi" in commands[(hifi, "assembly")]


def test_short_manifest_row_is_a_reported_error_not_a_traceback(tmp_path):
    manifest = tmp_path / "assemblies.tsv"
    manifest.write_text(
        "sample_id\tmode\tread1\tread2\tread_qc_status\tread_platform\nx\tshort_isolate\n"
    )
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(manifest), "--out", str(tmp_path / "out")],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2, result.stderr
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["ok"] is False
    assert "read_qc_status must be passed" in payload["error"]["message"]


def write_stub(tool_dir, name, body):
    tool_dir.mkdir(exist_ok=True)
    stub = tool_dir / name
    stub.write_text(f"#!{sys.executable}\nimport sys\nfrom pathlib import Path\n{body}")
    stub.chmod(0o755)


def test_failed_execute_still_writes_manifest_with_reached_statuses(tmp_path):
    out = tmp_path / "out"
    args = [
        sys.executable,
        str(SCRIPT),
        str(SKILL / "fixtures" / "assemblies.tsv"),
        "--out",
        str(out),
    ]
    dry = subprocess.run(args, text=True, capture_output=True, check=False)
    assert dry.returncode == 0, dry.stderr
    tool_dir = tmp_path / "bin"
    write_stub(
        tool_dir,
        "spades.py",
        "target = Path(sys.argv[sys.argv.index('-o') + 1])\n"
        "target.mkdir(parents=True, exist_ok=True)\n"
        "(target / 'scaffolds.fasta').write_text('>c\\nAC\\n')\n",
    )
    write_stub(tool_dir, "quast.py", "sys.exit(3)\n")
    env = {**os.environ, "PATH": f"{tool_dir}:{os.environ['PATH']}"}
    result = subprocess.run(
        [*args, "--execute"],
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    assert result.returncode == 2
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["ok"] is False
    assert "qc command failed with exit 3" in payload["error"]["message"]
    manifest = json.loads((out / "run_manifest.json").read_text())
    first_sample = [step for step in manifest["steps"] if step["sample_id"] == "short"]
    assert [step.get("status") for step in first_sample] == [
        "completed",
        "completed",
        "failed",
    ]


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
