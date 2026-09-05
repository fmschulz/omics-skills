import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "bio-protein-clustering-pangenome"
SCRIPT = SKILL / "scripts" / "build_pangenome_artifacts.py"


def test_small_multigenome_fixture_persists_all_comparison_axes(tmp_path):
    fixture = SKILL / "fixtures"
    out = tmp_path / "out"
    result = subprocess.run(["uv", "run", "--script", str(SCRIPT), str(fixture / "orthogroups.tsv"), "--genomes", str(fixture / "genomes.tsv"), "--marker-catalog", str(fixture / "marker_catalog.tsv"), "--marker-hits", str(fixture / "marker_hits.tsv"), "--ncrna", str(fixture / "ncRNA_census.tsv"), "--out", str(out)], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    expected = {"presence_absence.parquet", "copy_number_matrix.parquet", "relative_genome_metrics.tsv", "family_copy_number_comparison.tsv", "conserved_neighborhoods.tsv", "marker_census.tsv", "ncRNA_census.tsv"}
    assert expected <= {path.name for path in out.iterdir()}
    assert "query\tstructural\tOG4\tstructural protein\t0\texplicit_absence" in (out / "marker_census.tsv").read_text()
    assert "qctg:OG1-OG2\trelative_a\tactg:OG1-OG2" in (out / "conserved_neighborhoods.tsv").read_text()
    assert "OG3\tquery\t1\t0\tinf\tquery_specific" in (out / "family_copy_number_comparison.tsv").read_text()


def test_family_present_in_one_reference_is_not_called_query_specific(tmp_path):
    """A zero reference MEDIAN is not absence. With reference counts [0, 1] the
    family exists in a reference, so claiming query_specific with an infinite
    fold change would fabricate a discovery."""
    fixture = SKILL / "fixtures"
    work = tmp_path / "fixtures"
    work.mkdir()
    for name in ("marker_catalog.tsv", "marker_hits.tsv", "ncRNA_census.tsv"):
        (work / name).write_text((fixture / name).read_text(), encoding="utf-8")

    # Three references, one of which carries OG3: counts are [0, 0, 1], so the
    # median is 0 while the family is demonstrably present in a reference.
    genomes = (fixture / "genomes.tsv").read_text().rstrip("\n").splitlines()
    genomes.append("relative_c\treference\t1000\t1\t1000\t3\t0.80\t0.50")
    (work / "genomes.tsv").write_text("\n".join(genomes) + "\n", encoding="utf-8")

    orthogroups = (fixture / "orthogroups.tsv").read_text().rstrip("\n").splitlines()
    orthogroups += [
        "OG1\tc1\trelative_c\tcctg\t1\t1\t100",
        "OG2\tc2\trelative_c\tcctg\t2\t116\t215",
        "OG3\tc3\trelative_c\tcctg\t3\t236\t335",
    ]
    (work / "orthogroups.tsv").write_text("\n".join(orthogroups) + "\n", encoding="utf-8")

    out = tmp_path / "out"
    result = subprocess.run(
        ["uv", "run", "--script", str(SCRIPT), str(work / "orthogroups.tsv"),
         "--genomes", str(work / "genomes.tsv"),
         "--marker-catalog", str(work / "marker_catalog.tsv"),
         "--marker-hits", str(work / "marker_hits.tsv"),
         "--ncrna", str(work / "ncRNA_census.tsv"),
         "--out", str(out)],
        text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    comparison = (out / "family_copy_number_comparison.tsv").read_text()
    og3 = [line for line in comparison.splitlines() if line.startswith("OG3\tquery\t")]
    assert len(og3) == 1, comparison
    assert "query_specific" not in og3[0], og3[0]
    assert "inf" not in og3[0], og3[0]
    assert "present_in_reference_minority" in og3[0], og3[0]
