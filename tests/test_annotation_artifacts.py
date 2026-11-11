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


def run_with_genomes(tmp_path, genomes_text, out):
    """Run the driver on fixture inputs with a replaced genomes table."""
    fixture = SKILL / "fixtures"
    genomes = tmp_path / "genomes.tsv"
    genomes.write_text(genomes_text, encoding="utf-8")
    return subprocess.run(
        [
            "uv",
            "run",
            "--script",
            str(SCRIPT),
            str(fixture / "annotations.tsv"),
            "--genomes",
            str(genomes),
            "--markers",
            str(fixture / "markers.tsv"),
            "--out",
            str(out),
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def test_failed_role_check_leaves_no_partial_output_and_rerun_succeeds(tmp_path):
    """The role check used to run after the Parquet tables were written, so a failed
    run left files behind and the corrected rerun hit "output directory is not
    empty"."""
    out = tmp_path / "out"
    fixture_genomes = (SKILL / "fixtures" / "genomes.tsv").read_text()
    only_queries = fixture_genomes.replace("\treference\t", "\tquery\t")
    failed = run_with_genomes(tmp_path, only_queries, out)
    assert failed.returncode == 2
    payload = json.loads(failed.stdout.strip().splitlines()[-1])
    assert payload["ok"] is False
    assert "at least one query and one reference" in payload["error"]["message"]
    assert not out.exists() or not any(out.iterdir())

    rerun = run_with_genomes(tmp_path, fixture_genomes, out)
    assert rerun.returncode == 0, rerun.stderr


def test_unknown_genome_role_is_an_input_error(tmp_path):
    """A typo such as `refrence` silently dropped that genome from the baseline."""
    fixture_genomes = (SKILL / "fixtures" / "genomes.tsv").read_text()
    typo = fixture_genomes.replace("\treference\t", "\trefrence\t")
    out = tmp_path / "out"
    result = run_with_genomes(tmp_path, typo, out)
    assert result.returncode == 2
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["ok"] is False
    assert "refrence" in payload["error"]["message"]
    assert not out.exists() or not any(out.iterdir())


def test_row_with_the_wrong_field_count_is_rejected_before_any_output(tmp_path):
    """A surplus field gives csv.DictReader a None key; the DictWriter failed on it
    only after other artifacts were written."""
    lines = (SKILL / "fixtures" / "genomes.tsv").read_text().splitlines()
    bad_rows = {"extra": lines[1] + "\textra", "short": lines[1].rsplit("\t", 1)[0]}
    for name, row in bad_rows.items():
        work = tmp_path / name
        work.mkdir()
        out = work / "out"
        text = "\n".join([lines[0], row, *lines[2:]]) + "\n"
        result = run_with_genomes(work, text, out)
        assert result.returncode == 2, result.stdout + result.stderr
        payload = json.loads(result.stdout.strip().splitlines()[-1])
        assert payload["ok"] is False
        assert "genomes.tsv" in payload["error"]["message"]
        assert "data row 1" in payload["error"]["message"]
        assert not out.exists() or not any(out.iterdir())
