import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "bio-reads-qc-mapping"
SCRIPT = SKILL / "scripts" / "run_reads_qc_mapping.py"


def command(*args: object) -> list[str]:
    return ["uv", "run", "--script", str(SCRIPT), *map(str, args)]


def test_fixture_covers_paired_single_long_and_conditional_mapping(tmp_path):
    out = tmp_path / "out"
    result = subprocess.run(command(SKILL / "fixtures" / "sample_sheet.tsv", "--out", out), text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    manifest = json.loads((out / "run_manifest.json").read_text())
    assert {row["read_type"] for row in manifest["samples"]} == {"paired_short", "single_short", "long"}
    mapped = {step["sample_id"] for step in manifest["steps"] if step["stage"] == "mapping"}
    assert mapped == {"paired", "long"}
    assert "single\tnot_requested\t" in (out / "mapping_stats.tsv").read_text()


def test_invalid_sample_sheet_is_rejected(tmp_path):
    sheet = tmp_path / "bad.tsv"
    sheet.write_text("sample_id\tread_type\tread1\nfoo\tpaired_short\tnone\n")
    result = subprocess.run(command(sheet, "--out", tmp_path / "out"), text=True, capture_output=True)
    assert result.returncode != 0
    assert "columns must be exactly" in result.stderr


def test_execute_reuses_complete_outputs_without_calling_tools(tmp_path):
    out = tmp_path / "out"
    first = subprocess.run(command(SKILL / "fixtures" / "sample_sheet.tsv", "--out", out), text=True, capture_output=True)
    assert first.returncode == 0, first.stderr
    manifest = json.loads((out / "run_manifest.json").read_text())
    for step in manifest["steps"]:
        for output in step["outputs"]:
            path = Path(output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture output\n")
        (Path(step["outputs"][0]).parent / f"{step['stage']}.done").write_text("complete\n")
    second = subprocess.run(command(SKILL / "fixtures" / "sample_sheet.tsv", "--out", out, "--execute"), text=True, capture_output=True)
    assert second.returncode == 0, second.stderr
    rerun = json.loads((out / "run_manifest.json").read_text())
    assert {step["status"] for step in rerun["steps"]} == {"reused"}


def test_execute_does_not_reuse_unmarked_partial_outputs(tmp_path):
    out = tmp_path / "out"
    first = subprocess.run(
        command(SKILL / "fixtures" / "sample_sheet.tsv", "--out", out),
        text=True,
        capture_output=True,
    )
    assert first.returncode == 0, first.stderr
    manifest = json.loads((out / "run_manifest.json").read_text())
    for step in manifest["steps"]:
        for output in step["outputs"]:
            path = Path(output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("partial output\n")

    tool_dir = tmp_path / "bin"
    tool_dir.mkdir()
    fastp = tool_dir / "fastp"
    fastp.write_text("#!/bin/sh\nexit 42\n")
    fastp.chmod(0o755)
    env = {**os.environ, "PATH": f"{tool_dir}:{os.environ['PATH']}"}
    rerun = subprocess.run(
        command(SKILL / "fixtures" / "sample_sheet.tsv", "--out", out, "--execute"),
        text=True,
        capture_output=True,
        env=env,
    )
    assert rerun.returncode != 0
    assert "step failed" in rerun.stderr
