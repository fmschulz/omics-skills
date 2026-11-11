import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
SKILLS = ROOT / "skills"
UV = ("uv", "run", "--script")

DRIVERS = {
    "bio-annotation": (UV, "build_annotation_artifacts.py", lambda f: [f / "annotations.tsv", "--genomes", f / "genomes.tsv", "--markers", f / "markers.tsv"]),
    "bio-interdomain-hgt": (UV, "run_hgt_evidence.py", lambda f: [f / "forward_hits.tsv", "--arbiter-hits", f / "arbiter_hits.tsv", "--reciprocal", f / "reciprocal.tsv", "--context", f / "context.tsv", "--trees", f / "trees.tsv", "--sampling-depth", f / "sampling_depth.tsv", "--databases", f / "databases.json", "--hypotheses", f / "hypotheses.tsv", "--reflections", f / "reflections.tsv", "--query-domain", "ncldv"]),
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
    assert Path(payload["manifest"]).is_file()


def test_failure_envelope(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    (out / "keep").write_text("user data")
    inputs = DRIVERS["bio-annotation"][2](SKILLS / "bio-annotation" / "fixtures")
    result = run("bio-annotation", inputs, out)
    assert result.returncode == 2
    payload = envelope(result)
    assert payload["ok"] is False
    assert payload["skill"] == "bio-annotation"
    assert payload["error"]["code"] and payload["error"]["message"]
    assert "output directory is not empty" in payload["error"]["message"]
    assert payload["error"]["message"] in result.stderr
