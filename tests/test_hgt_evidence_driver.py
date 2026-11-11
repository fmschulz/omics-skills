import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "bio-interdomain-hgt"
SCRIPT = SKILL / "scripts" / "run_hgt_evidence.py"


def command(out, context=None, fixtures=None, query_domain="ncldv"):
    f = fixtures or SKILL / "fixtures"
    return [
        "uv",
        "run",
        "--script",
        str(SCRIPT),
        str(f / "forward_hits.tsv"),
        "--arbiter-hits",
        str(f / "arbiter_hits.tsv"),
        "--reciprocal",
        str(f / "reciprocal.tsv"),
        "--context",
        str(context or f / "context.tsv"),
        "--trees",
        str(f / "trees.tsv"),
        "--sampling-depth",
        str(f / "sampling_depth.tsv"),
        "--databases",
        str(f / "databases.json"),
        "--hypotheses",
        str(f / "hypotheses.tsv"),
        "--reflections",
        str(f / "reflections.tsv"),
        "--query-domain",
        query_domain,
        "--out",
        str(out),
    ]


def test_fixture_confirms_direction_with_all_gates_and_normalization(tmp_path):
    out = tmp_path / "out"
    result = subprocess.run(command(out), text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    candidates = (out / "hgt_candidates.tsv").read_text()
    assert "recipient_to_query\ttrue\ttrue\t0.97\ttrue\tconfirmed" in candidates
    assert "EukFixture\t1\t20\t5.000000" in (out / "lineage_sampling_normalization.tsv").read_text()
    manifest = json.loads((out / "run_manifest.json").read_text())
    assert manifest["confirmed_count"] == 1
    assert manifest["gates"] == ["database", "forward", "reciprocal", "context", "phylogeny", "final"]


def test_eukaryotic_context_must_be_frame_aware(tmp_path):
    source = SKILL / "fixtures" / "context.tsv"
    context = tmp_path / "context.tsv"
    context.write_text(source.read_text().replace("diamond_blastx", "pyrodigal"))
    out = tmp_path / "out"
    result = subprocess.run(command(out, context), text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert "recipient_to_query\tfalse\tfalse\t0.97\ttrue\tcandidate" in (out / "hgt_candidates.tsv").read_text()


def edited_fixtures(tmp_path, name, old, new):
    """Copy the fixture directory and replace one string in one file."""
    work = tmp_path / "fixtures"
    shutil.copytree(SKILL / "fixtures", work)
    target = work / name
    assert old in target.read_text()
    target.write_text(target.read_text().replace(old, new))
    return work


def run_failing(args):
    result = subprocess.run(args, text=True, capture_output=True, check=False)
    assert result.returncode == 2, result.stdout + result.stderr
    envelope = json.loads(result.stdout.strip().splitlines()[-1])
    assert envelope["ok"] is False
    return envelope["error"]["message"]


def test_percent_scale_support_is_an_input_error(tmp_path):
    work = edited_fixtures(tmp_path, "trees.tsv", "0.97", "50")
    message = run_failing(command(tmp_path / "out", fixtures=work))
    assert "virus_gene" in message
    assert "support" in message


def test_unknown_query_domain_is_an_input_error(tmp_path):
    message = run_failing(command(tmp_path / "out", query_domain="bogus"))
    assert "bogus" in message


def test_unknown_arbiter_hit_domain_is_an_input_error(tmp_path):
    work = edited_fixtures(tmp_path, "arbiter_hits.tsv", "\tncldv\t", "\tviruses\t")
    assert "viruses" in run_failing(command(tmp_path / "out", fixtures=work))


def test_unknown_recipient_domain_is_an_input_error(tmp_path):
    work = edited_fixtures(tmp_path, "forward_hits.tsv", "\teukaryota\t", "\tfungi\t")
    assert "fungi" in run_failing(command(tmp_path / "out", fixtures=work))


def test_failed_run_leaves_no_output_and_the_rerun_succeeds(tmp_path):
    bad = edited_fixtures(
        tmp_path, "sampling_depth.tsv", "EukFixture\t20", "EukFixture\t0"
    )
    out = tmp_path / "out"
    assert "positive sampling depth" in run_failing(command(out, fixtures=bad))
    assert not out.exists() or not any(out.iterdir())
    result = subprocess.run(command(out), text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr


def test_row_with_the_wrong_field_count_leaves_no_output(tmp_path):
    lines = (SKILL / "fixtures" / "forward_hits.tsv").read_text().splitlines()
    bad_rows = {"extra": lines[1] + "\textra", "short": lines[1].rsplit("\t", 1)[0]}
    for name, row in bad_rows.items():
        work = tmp_path / name
        shutil.copytree(SKILL / "fixtures", work / "fixtures")
        text = "\n".join([lines[0], row, *lines[2:]]) + "\n"
        (work / "fixtures" / "forward_hits.tsv").write_text(text)
        out = work / "out"
        message = run_failing(command(out, fixtures=work / "fixtures"))
        assert "forward_hits.tsv" in message
        assert "data row 1" in message
        assert not out.exists() or not any(out.iterdir())
