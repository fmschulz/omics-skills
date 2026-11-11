import json
import os
import subprocess
import sys
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


def test_mapping_status_reflects_execution_not_intent(tmp_path):
    """mapping_stats.tsv used to report "planned" even after --execute, so the
    table claimed work that had already run."""
    out = tmp_path / "out"
    sheet = SKILL / "fixtures" / "sample_sheet.tsv"

    first = subprocess.run(command(sheet, "--out", out), text=True, capture_output=True)
    assert first.returncode == 0, first.stderr
    assert "\tplanned\t" in (out / "mapping_stats.tsv").read_text()

    manifest = json.loads((out / "run_manifest.json").read_text())
    for step in manifest["steps"]:
        for output in step["outputs"]:
            path = Path(output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture output\n")
        (Path(step["outputs"][0]).parent / f"{step['stage']}.done").write_text("complete\n")

    second = subprocess.run(command(sheet, "--out", out, "--execute"), text=True, capture_output=True)
    assert second.returncode == 0, second.stderr
    stats = (out / "mapping_stats.tsv").read_text()
    assert "\tplanned\t" not in stats, stats
    assert "\treused\t" in stats, stats
    assert "\tnot_requested\t" in stats, stats


def test_failed_execute_still_writes_manifest_and_mapping_table(tmp_path):
    """A failed --execute used to leave no manifest or a stale dry-run copy, though
    the finished stages were already on disk with their .done markers."""
    out = tmp_path / "out"
    sheet = SKILL / "fixtures" / "sample_sheet.tsv"
    dry = subprocess.run(
        command(sheet, "--out", out), text=True, capture_output=True, check=False
    )
    assert dry.returncode == 0, dry.stderr

    tool_dir = tmp_path / "bin"
    tool_dir.mkdir()
    fastp = tool_dir / "fastp"
    fastp.write_text(
        f"#!{sys.executable}\n"
        "import sys\n"
        "from pathlib import Path\n"
        "for flag in ('--out1', '--out2', '--json'):\n"
        "    if flag in sys.argv:\n"
        "        Path(sys.argv[sys.argv.index(flag) + 1]).write_text('x\\n')\n"
    )
    bwa = tool_dir / "bwa-mem2"
    bwa.write_text("#!/bin/sh\nexit 3\n")
    for stub in (fastp, bwa):
        stub.chmod(0o755)
    env = {**os.environ, "PATH": f"{tool_dir}:{os.environ['PATH']}"}
    result = subprocess.run(
        command(sheet, "--out", out, "--execute"),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["ok"] is False
    assert "bwa-mem2" in payload["error"]["message"]
    manifest = json.loads((out / "run_manifest.json").read_text())
    statuses = [
        (step["sample_id"], step["stage"], step.get("status"))
        for step in manifest["steps"]
    ]
    assert statuses[:2] == [
        ("paired", "qc", "completed"),
        ("paired", "mapping", "failed"),
    ]
    assert "paired\tfailed\t" in (out / "mapping_stats.tsv").read_text()
