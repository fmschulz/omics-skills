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


def split_stdout(result: subprocess.CompletedProcess[str]) -> tuple[dict, dict]:
    """Return the plan JSON (all lines before the last) and the last-line envelope."""
    *plan_lines, envelope_line = result.stdout.rstrip("\n").split("\n")
    plan = json.loads("\n".join(plan_lines)) if plan_lines else {}
    return plan, json.loads(envelope_line)


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
            command = split_stdout(result)[0]["commands"][0]["command"]
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
            step = split_stdout(result)[0]["commands"][0]
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

    def write_boltz(self, directory: str, protein_extra: str = "") -> Path:
        path = Path(directory) / "input.yaml"
        path.write_text(
            "version: 1\nsequences:\n  - protein:\n      id: A\n"
            f"      sequence: MKTAYIAKQRQISFVKSHFSRQ\n{protein_extra}",
            encoding="utf-8",
        )
        return path

    def test_boltz_protein_without_msa_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_plan(
                "--boltz-yaml", str(self.write_boltz(tmp)), "--out-dir", f"{tmp}/out"
            )
            self.assertEqual(result.returncode, 2, result.stdout)
            message = split_stdout(result)[1]["error"]["message"]
            self.assertIn("A", message)
            self.assertIn("msa: empty", message)
            self.assertIn("--use-msa-server", message)

    def test_boltz_protein_with_msa_value_is_planned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_boltz(tmp, "      msa: empty\n")
            result = self.run_plan("--boltz-yaml", str(path), "--out-dir", f"{tmp}/out")
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_boltz_msa_server_needs_no_msa_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_plan(
                "--boltz-yaml",
                str(self.write_boltz(tmp)),
                "--use-msa-server",
                "--approve-public-msa-upload",
                "--out-dir",
                f"{tmp}/out",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(
                "--use_msa_server", split_stdout(result)[0]["commands"][0]["command"]
            )

    def foldseek_args(self, tmp: str, *extra: str) -> list[str]:
        database = Path(tmp) / "targetDB"
        database.write_text("fixture", encoding="utf-8")
        query = SKILL_ROOT / "fixtures" / "query.faa"
        return ["--foldseek-query", str(query), "--foldseek-db", str(database), *extra]

    def test_foldseek_plan_passes_explicit_threads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            default = self.run_plan(*self.foldseek_args(tmp), "--out-dir", tmp)
            counted = self.run_plan(
                *self.foldseek_args(tmp, "--threads", "4"), "--out-dir", tmp
            )
            for result, expected in ((default, "1"), (counted, "4")):
                self.assertEqual(result.returncode, 0, result.stderr)
                command = split_stdout(result)[0]["commands"][0]["command"]
                index = command.index("--threads")
                self.assertEqual(command[index + 1], expected)

    def test_non_positive_threads_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_plan(
                *self.foldseek_args(tmp, "--threads", "0"), "--out-dir", tmp
            )
            self.assertEqual(result.returncode, 2, result.stdout)
            self.assertIn("--threads", split_stdout(result)[1]["error"]["message"])

    def test_success_envelope_is_last_stdout_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp).resolve() / "out"
            result = self.run_plan(
                "--boltz-yaml", str(BOLTZ), "--out-dir", str(out_dir)
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            plan, envelope = split_stdout(result)
            self.assertEqual(plan["out_dir"], str(out_dir))
            self.assertEqual(
                envelope,
                {
                    "ok": True,
                    "skill": "bio-structure-annotation",
                    "out": str(out_dir),
                    "warnings": [],
                },
            )

    def test_success_envelope_names_plan_file_as_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp).resolve() / "plan.json"
            result = self.run_plan(
                "--boltz-yaml",
                str(BOLTZ),
                "--out-dir",
                f"{tmp}/out",
                "--plan-out",
                str(plan_path),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(split_stdout(result)[1]["manifest"], str(plan_path))

    def test_failure_prints_error_envelope_and_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_plan("--out-dir", tmp)
            self.assertEqual(result.returncode, 2, result.stdout)
            envelope = json.loads(result.stdout.rstrip("\n").split("\n")[-1])
            self.assertEqual(envelope["ok"], False)
            self.assertEqual(envelope["skill"], "bio-structure-annotation")
            self.assertEqual(envelope["error"]["code"], "ValueError")
            self.assertIn("select at least one", envelope["error"]["message"])
            self.assertIn(envelope["error"]["message"], result.stderr)

    def test_failed_tool_command_prints_error_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fake_bin = Path(tmp) / "bin"
            fake_bin.mkdir()
            fake = fake_bin / "tmvec"
            fake.write_text("#!/bin/sh\nexit 3\n", encoding="utf-8")
            fake.chmod(0o755)
            database = Path(tmp) / "database.npz"
            database.write_bytes(b"fixture")
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "--script",
                    str(SCRIPT),
                    "--tmvec-query",
                    str(SKILL_ROOT / "fixtures" / "query.faa"),
                    "--tmvec-db",
                    str(database),
                    "--out-dir",
                    f"{tmp}/out",
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
            self.assertEqual(result.returncode, 2, result.stdout)
            envelope = json.loads(result.stdout.rstrip("\n").split("\n")[-1])
            self.assertEqual(envelope["error"]["code"], "CalledProcessError")

    def test_shebang_runs_the_script_through_uv(self) -> None:
        first_line = SCRIPT.read_text(encoding="utf-8").splitlines()[0]
        self.assertEqual(first_line, "#!/usr/bin/env -S uv run --script")


if __name__ == "__main__":
    unittest.main()
