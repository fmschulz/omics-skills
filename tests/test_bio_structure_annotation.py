from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "bio-structure-annotation"
SCRIPT = SKILL_ROOT / "scripts" / "run_structure_annotation.py"
BOLTZ = SKILL_ROOT / "fixtures" / "boltz-complex.yaml"
# Stand-in for `tmvec search` at valentynbez/tmvec 6bdf11a: it accepts only the
# pinned CLI's options and, like the real tool, writes results.tsv in --output.
FAKE_TMVEC = """#!/bin/sh
[ "$1" = search ] || exit 2
shift
while [ $# -gt 0 ]; do
  case "$1" in
    --input-fasta|--database) [ -f "$2" ] || exit 2 ;;
    --output) output="$2" ;;
    *) echo "unexpected option: $1" >&2; exit 2 ;;
  esac
  shift 2
done
mkdir -p "$output" && printf 'query\\ttarget\\t0.9\\n' > "$output/results.tsv"
"""


class BioStructureAnnotationTests(unittest.TestCase):
    def run_plan(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["uv", "run", "--script", str(SCRIPT), *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_boltz_fixture_uses_current_nested_yaml_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_plan("--boltz-yaml", str(BOLTZ), "--out-dir", tmp)
            self.assertEqual(result.returncode, 0, result.stderr)
            command = json.loads(result.stdout)["commands"][0]["command"]
            self.assertIn("--out_dir", command)

    def test_public_msa_upload_requires_explicit_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_plan(
                "--boltz-yaml",
                str(BOLTZ),
                "--use-msa-server",
                "--out-dir",
                tmp,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("approve-public-msa-upload", result.stderr)

    def test_gpu_foldseek_requires_padded_database_option(self) -> None:
        query = SKILL_ROOT / "fixtures" / "query.faa"
        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / "targetDB"
            database.write_text("fixture", encoding="utf-8")
            result = self.run_plan(
                "--foldseek-query",
                str(query),
                "--foldseek-db",
                str(database),
                "--gpu",
                "--out-dir",
                tmp,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--foldseek-padded-db", result.stderr)

    def test_tmvec_plan_matches_pinned_fork_cli(self) -> None:
        query = (SKILL_ROOT / "fixtures" / "query.faa").resolve()
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp).resolve()
            database = out_dir / "database.npz"
            database.write_bytes(b"fixture")
            result = self.run_plan(
                "--tmvec-query",
                str(query),
                "--tmvec-db",
                str(database),
                "--out-dir",
                str(out_dir),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            step = json.loads(result.stdout)["commands"][0]
            self.assertEqual(
                step["command"],
                [
                    "tmvec",
                    "search",
                    "--input-fasta",
                    str(query),
                    "--database",
                    str(database),
                    "--output",
                    str(out_dir / "tmvec"),
                ],
            )
            self.assertEqual(step["expected"], str(out_dir / "tmvec" / "results.tsv"))

    def test_tmvec_execute_finds_results_in_output_folder(self) -> None:
        query = SKILL_ROOT / "fixtures" / "query.faa"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            database = tmp_path / "database.npz"
            database.write_bytes(b"fixture")
            fake_bin = tmp_path / "bin"
            fake_bin.mkdir()
            fake_tmvec = fake_bin / "tmvec"
            fake_tmvec.write_text(FAKE_TMVEC, encoding="utf-8")
            fake_tmvec.chmod(0o755)
            out_dir = tmp_path / "out"
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "--script",
                    str(SCRIPT),
                    "--tmvec-query",
                    str(query),
                    "--tmvec-db",
                    str(database),
                    "--out-dir",
                    str(out_dir),
                    "--execute",
                ],
                cwd=REPO_ROOT,
                env={
                    **os.environ,
                    "PATH": f"{fake_bin}{os.pathsep}{os.environ['PATH']}",
                },
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((out_dir / "tmvec" / "results.tsv").is_file())


if __name__ == "__main__":
    unittest.main()
