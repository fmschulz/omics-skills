import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "manuscript-review-council"
SCRIPT = SKILL / "scripts" / "validate_review_bundle.py"


def test_fixture_has_deterministic_paths_and_machine_readable_issues():
    result = subprocess.run(["uv", "run", "--script", str(SCRIPT), str(SKILL / "fixtures" / "review-bundle.json")], text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_wrong_artifact_path_is_rejected(tmp_path):
    bundle = json.loads((SKILL / "fixtures" / "review-bundle.json").read_text())
    bundle["editor_path"] = "editor.json"
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(bundle))
    result = subprocess.run(["uv", "run", "--script", str(SCRIPT), str(path)], text=True, capture_output=True)
    assert result.returncode != 0
    assert "editor_path must be reviews/" in result.stderr


def _bundle() -> dict:
    return json.loads((SKILL / "fixtures" / "review-bundle.json").read_text())


def _run(tmp_path, bundle) -> subprocess.CompletedProcess:
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    return subprocess.run(
        ["uv", "run", "--script", str(SCRIPT), str(path)], text=True, capture_output=True
    )


def test_issue_cannot_cite_a_reviewer_that_never_reported(tmp_path):
    """A bundle could credit a finding to a reviewer absent from
    reviewer_reports, inventing the provenance of a review issue."""
    bundle = _bundle()
    bundle["issues"][0]["source_roles"] = ["nonexistent-reviewer"]
    result = _run(tmp_path, bundle)
    assert result.returncode != 0
    assert "cites reviewers absent from reviewer_reports" in result.stderr


def test_dropping_a_default_reviewer_needs_a_recorded_reason(tmp_path):
    bundle = _bundle()
    bundle["reviewer_reports"] = [r for r in bundle["reviewer_reports"] if r["role"] != "skeptic"]
    bundle["issues"][0]["source_roles"] = ["methods-statistics"]
    result = _run(tmp_path, bundle)
    assert result.returncode != 0
    assert "missing default reviewer" in result.stderr

    bundle["reduced_council_reason"] = "author-requested methods-only reassessment"
    assert _run(tmp_path, bundle).returncode == 0
