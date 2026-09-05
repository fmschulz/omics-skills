import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "bio-annotation"
SCRIPT = SKILL / "scripts" / "build_annotation_artifacts.py"


def run_driver(out):
    return subprocess.run(["uv", "run", "--script", str(SCRIPT), str(SKILL / "fixtures" / "annotations.tsv"), "--genomes", str(SKILL / "fixtures" / "genomes.tsv"), "--markers", str(SKILL / "fixtures" / "markers.tsv"), "--out", str(out)], text=True, capture_output=True)


def test_normalized_artifact_bundle_has_explicit_absence_and_discovery(tmp_path):
    out = tmp_path / "out"
    result = run_driver(out)
    assert result.returncode == 0, result.stderr
    expected = {"annotations.parquet", "taxonomy.parquet", "feature_inventory.parquet", "marker_census.tsv", "family_copy_number_matrix.parquet", "domain_routing.tsv", "family_expansion_candidates.tsv", "discovery_candidates.tsv", "run_manifest.json"}
    assert expected <= {path.name for path in out.iterdir()}
    census = (out / "marker_census.tsv").read_text()
    assert "query\tstructural\tPF002\tcapsid protein\t0\texplicit_absence" in census
    candidates = (out / "discovery_candidates.tsv").read_text()
    assert "PF003\t2\t0\tinf\tquery_specific" in candidates
    manifest = json.loads((out / "run_manifest.json").read_text())
    assert len(manifest["artifacts"]) == 8
    assert {item["path"] for item in manifest["artifacts"]} == expected - {"run_manifest.json"}


def test_nonempty_output_directory_is_refused(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    (out / "keep").write_text("user data")
    result = run_driver(out)
    assert result.returncode != 0
    assert "output directory is not empty" in result.stderr


def test_multi_domain_protein_with_two_family_hits_is_accepted(tmp_path):
    """A protein carrying two Pfam domains is the normal case; rejecting it on
    protein_id uniqueness alone made the driver unusable on real annotations."""
    fixture = SKILL / "fixtures"
    work = tmp_path / "fixtures"
    work.mkdir()
    for name in ("genomes.tsv", "markers.tsv"):
        (work / name).write_text((fixture / name).read_text(), encoding="utf-8")
    rows = (fixture / "annotations.tsv").read_text().rstrip("\n").splitlines()
    rows.append("query\tq2\tPF009\tsecond domain\tunknown\t1e-9\t\tBacteria\t0.70")
    (work / "annotations.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")

    out = tmp_path / "out"
    result = subprocess.run(
        ["uv", "run", "--script", str(SCRIPT), str(work / "annotations.tsv"),
         "--genomes", str(work / "genomes.tsv"), "--markers", str(work / "markers.tsv"),
         "--out", str(out)],
        text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stderr


def test_repeated_protein_family_pair_is_still_rejected(tmp_path):
    fixture = SKILL / "fixtures"
    work = tmp_path / "fixtures"
    work.mkdir()
    for name in ("genomes.tsv", "markers.tsv"):
        (work / name).write_text((fixture / name).read_text(), encoding="utf-8")
    rows = (fixture / "annotations.tsv").read_text().rstrip("\n").splitlines()
    rows.append(rows[-1])
    (work / "annotations.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")

    out = tmp_path / "out"
    result = subprocess.run(
        ["uv", "run", "--script", str(SCRIPT), str(work / "annotations.tsv"),
         "--genomes", str(work / "genomes.tsv"), "--markers", str(work / "markers.tsv"),
         "--out", str(out)],
        text=True, capture_output=True,
    )
    assert result.returncode != 0
    assert "duplicate protein_id/family_id rows" in result.stderr
