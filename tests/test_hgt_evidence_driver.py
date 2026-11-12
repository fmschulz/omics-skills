import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILL = ROOT / "skills" / "bio-interdomain-hgt"
SCRIPT = SKILL / "scripts" / "run_hgt_evidence.py"


def command(out, context=None, fixtures=None, query_domain="ncldv", extra=()):
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
        *extra,
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


def candidate_rows(out):
    lines = (out / "hgt_candidates.tsv").read_text().splitlines()
    header = lines[0].split("\t")
    return [dict(zip(header, line.split("\t"), strict=True)) for line in lines[1:]]


def test_min_identity_is_off_by_default_and_recorded_in_the_manifest(tmp_path):
    out = tmp_path / "out"
    result = subprocess.run(command(out), text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr
    assert json.loads((out / "run_manifest.json").read_text())["min_identity"] is None
    assert candidate_rows(out)[0]["ambiguity_reason"] == ""


def test_identity_below_min_identity_makes_the_direction_ambiguous(tmp_path):
    out = tmp_path / "out"
    result = subprocess.run(
        command(out, extra=["--min-identity", "90"]),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    row = candidate_rows(out)[0]
    assert row["direction"] == "ambiguous"
    assert row["status"] == "candidate"
    assert "82" in row["ambiguity_reason"]
    assert "90" in row["ambiguity_reason"]
    manifest = json.loads((out / "run_manifest.json").read_text())
    assert manifest["min_identity"] == 90
    assert manifest["confirmed_count"] == 0


def test_identity_at_or_above_min_identity_keeps_the_call(tmp_path):
    out = tmp_path / "out"
    result = subprocess.run(
        command(out, extra=["--min-identity", "82"]),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    row = candidate_rows(out)[0]
    assert row["status"] == "confirmed"
    assert row["ambiguity_reason"] == ""


def test_min_identity_above_100_is_an_input_error(tmp_path):
    message = run_failing(command(tmp_path / "out", extra=["--min-identity", "120"]))
    assert "min-identity" in message


def test_non_finite_or_out_of_range_identity_fails_the_min_identity_gate(tmp_path):
    for value in ("nan", "inf", "-1", "101"):
        work = edited_fixtures(
            tmp_path / value, "forward_hits.tsv", "\t82\t", f"\t{value}\t"
        )
        message = run_failing(
            command(
                tmp_path / value / "out", fixtures=work, extra=["--min-identity", "90"]
            )
        )
        assert "identity" in message
        assert "virus_gene" in message


def test_identity_is_not_checked_when_the_gate_is_off(tmp_path):
    work = edited_fixtures(tmp_path, "forward_hits.tsv", "\t82\t", "\tnan\t")
    out = tmp_path / "out"
    result = subprocess.run(
        command(out, fixtures=work), text=True, capture_output=True, check=False
    )
    assert result.returncode == 0, result.stderr


def test_non_finite_min_identity_is_an_input_error(tmp_path):
    for value in ("nan", "inf"):
        message = run_failing(
            command(tmp_path / value, extra=[f"--min-identity={value}"])
        )
        assert "min-identity" in message


def test_every_ambiguous_direction_carries_a_reason(tmp_path):
    work = edited_fixtures(
        tmp_path, "forward_hits.tsv", "\teukaryota\t", "\tbacteria\t"
    )
    out = tmp_path / "arbiter"
    result = subprocess.run(
        command(out, fixtures=work, query_domain="phage"),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    row = candidate_rows(out)[0]
    assert row["direction"] == "ambiguous"
    assert row["status"] == "candidate"
    for text in ("eukaryota", "bacteria", "ncldv", "phage"):
        assert text in row["ambiguity_reason"]

    both = tmp_path / "both"
    result = subprocess.run(
        command(
            both, fixtures=work, query_domain="phage", extra=["--min-identity", "90"]
        ),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    reason = candidate_rows(both)[0]["ambiguity_reason"]
    assert "phage" in reason
    assert "--min-identity 90" in reason
