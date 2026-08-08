from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[1]
VALIDATION = ROOT / "validation"
REGISTRY_SCRIPT = VALIDATION / "scripts" / "validate_registry.py"
RENDER_SCRIPT = VALIDATION / "scripts" / "render_slurm_job.py"
COLLECT_SCRIPT = VALIDATION / "scripts" / "collect_slurm_evidence.py"


def ready_job(workdir: Path) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "status": "ready",
        "validation_id": "test-phylogenomics-pilot",
        "driver": "bio-phylogenomics",
        "truth_set_id": "qfo-2025-04-reference-proteomes",
        "workdir": str(workdir),
        "logs_dir": "tasks/test-validation-run",
        "scheduler": {
            "cluster": "test-cluster",
            "account": "test-account",
            "partition": "test-partition",
            "qos": "test-qos",
            "cpus": 4,
            "memory_mb": 8192,
            "time_minutes": 30,
        },
        "environment": {
            "name": "test-lock",
            "version": "1",
            "kind": "file",
            "path": "pixi.lock",
            "sha256": "a" * 64,
        },
        "databases": [],
        "version_commands": [["iqtree3", "--version"]],
        "command": ["iqtree3", "-s", "alignment.fasta"],
        "expected_outputs": [{"path": "results/tree.nwk", "min_bytes": 5}],
    }


def test_registry_covers_exactly_eight_core_drivers() -> None:
    result = subprocess.run(
        ["uv", "run", "--script", str(REGISTRY_SCRIPT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "8 drivers, 8 truth sets, 0 ready" in result.stdout


def test_project_gate_runs_pytest_style_driver_tests() -> None:
    makefile = (ROOT / "Makefile").read_text()
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    assert "--with pytest" in makefile and "pytest" in makefile
    assert "--with pytest" in workflow and "pytest" in workflow
    assert "unittest discover -s tests" not in makefile
    assert "unittest discover -s tests" not in workflow
    assert "unittest discover -s tests" not in (ROOT / "README.md").read_text()
    assert "unittest discover -s tests" not in (ROOT / "docs" / "development.md").read_text()


def test_draft_scheduler_job_cannot_be_rendered(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            "uv",
            "run",
            "--script",
            str(RENDER_SCRIPT),
            str(VALIDATION / "jobs" / "phylogenomics-qfo-pilot.draft.json"),
            "--output",
            str(tmp_path / "job.sbatch"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "status must be ready" in result.stderr


def test_ready_scheduler_job_rejects_any_unresolved_placeholder(tmp_path: Path) -> None:
    job = ready_job(tmp_path)
    job["environment"]["version"] = "TBD"
    manifest = tmp_path / "job.json"
    manifest.write_text(json.dumps(job))
    result = subprocess.run(
        [
            "uv",
            "run",
            "--script",
            str(RENDER_SCRIPT),
            str(manifest),
            "--output",
            str(tmp_path / "job.sbatch"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "environment.version is unresolved" in result.stderr


def test_ready_scheduler_job_renders_checksums_versions_and_output_gates(tmp_path: Path) -> None:
    manifest = tmp_path / "job.json"
    manifest.write_text(json.dumps(ready_job(tmp_path)))
    output = tmp_path / "job.sbatch"
    result = subprocess.run(
        ["uv", "run", "--script", str(RENDER_SCRIPT), str(manifest), "--output", str(output)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    script = output.read_text()
    assert f"#SBATCH --output={tmp_path}/tasks/test-validation-run/slurm-%j.out" in script
    assert "# Validation cluster: test-cluster" in script
    assert "#SBATCH --account=test-account" in script
    assert "#SBATCH --partition=test-partition" in script
    assert "tree_sha256" in script
    assert "iqtree3 --version" in script
    assert "missing or undersized output: results/tree.nwk" in script
    syntax = subprocess.run(["bash", "-n", str(output)], text=True, capture_output=True)
    assert syntax.returncode == 0, syntax.stderr


def test_dry_run_then_submit_reuses_identical_rendered_job(tmp_path: Path) -> None:
    manifest = tmp_path / "job.json"
    manifest.write_text(json.dumps(ready_job(tmp_path)))
    output = tmp_path / "job.sbatch"
    wrapper = VALIDATION / "scripts" / "submit_slurm_job.sh"
    dry_run = subprocess.run(
        [str(wrapper), "--dry-run", str(manifest), str(output)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert dry_run.returncode == 0, dry_run.stderr
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    sbatch = fake_bin / "sbatch"
    sbatch.write_text('#!/usr/bin/env bash\nprintf "job:%s\\n" "${@: -1}"\n')
    sbatch.chmod(sbatch.stat().st_mode | stat.S_IXUSR)
    env = os.environ | {
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "OMICS_VALIDATION_SUBMIT_APPROVED": "1",
    }
    submitted = subprocess.run(
        [str(wrapper), "--submit", str(manifest), str(output)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
    )
    assert submitted.returncode == 0, submitted.stderr
    assert f"job:{output}" in submitted.stdout


def test_sacct_collection_records_peak_memory_and_output_checksum(tmp_path: Path) -> None:
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "tree.nwk").write_text("(a,b);\n")
    manifest = tmp_path / "job.json"
    manifest.write_text(json.dumps(ready_job(tmp_path)))
    evidence = tmp_path / "evidence.json"
    result = subprocess.run(
        [
            "uv",
            "run",
            "--script",
            str(COLLECT_SCRIPT),
            str(manifest),
            "--job-id",
            "12345",
            "--sacct-file",
            str(VALIDATION / "fixtures" / "sacct-completed.psv"),
            "--output",
            str(evidence),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    record = json.loads(evidence.read_text())
    assert record["scheduler"]["peak_rss_bytes"] == 512 * 1024**2
    assert record["scheduler"]["elapsed_seconds"] == 42
    assert record["outputs"][0]["passed"] is True
    assert len(record["outputs"][0]["sha256"]) == 64
    assert record["failure_modes"] == []
