from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "bio-workflow-methods-docwriter"
VALIDATOR = SKILL_ROOT / "scripts" / "validate_run_manifest.py"
EXTRACTOR = SKILL_ROOT / "scripts" / "extract_nextflow_run.py"
SNAKEMAKE_EXTRACTOR = SKILL_ROOT / "scripts" / "extract_snakemake_run.py"
CWL_EXTRACTOR = SKILL_ROOT / "scripts" / "extract_cwl_run.py"
EXAMPLE = SKILL_ROOT / "examples" / "run_manifest.example.yaml"
SCHEMA = SKILL_ROOT / "schemas" / "run-manifest.schema.json"
SCRIPTS = SKILL_ROOT / "scripts"
CWL_FIXTURE = SKILL_ROOT / "fixtures" / "cwl"
REDACTION = SCRIPTS / "command_redaction.py"


def load_redaction():
    spec = importlib.util.spec_from_file_location("command_redaction", REDACTION)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class WorkflowMethodsDocwriterTests(unittest.TestCase):
    def run_validator(self, manifest: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["uv", "run", str(VALIDATOR), str(manifest)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_complete_example_passes_schema_and_semantic_checks(self) -> None:
        result = self.run_validator(EXAMPLE)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Manifest validation passed", result.stdout)

    def test_required_placeholder_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "incomplete.yaml"
            manifest.write_text(
                EXAMPLE.read_text(encoding="utf-8").replace(
                    "engine_version: 25.10.3",
                    "engine_version: NOT CAPTURED",
                    1,
                ),
                encoding="utf-8",
            )
            result = self.run_validator(manifest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("workflow.engine_version is incomplete", result.stdout)

    def test_step_schema_requires_reproducibility_fields(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        required = set(schema["properties"]["steps"]["items"]["required"])
        self.assertTrue(
            {"tool", "tool_version", "command", "inputs", "outputs"} <= required
        )

    def test_placeholder_values_are_rejected_anywhere_in_the_manifest(self) -> None:
        manifest = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
        manifest["inputs"][0]["checksum"] = "NOT CAPTURED"
        manifest["software"]["tools"][0]["version"] = "TBD"
        manifest["software"]["containers"][0]["digest"] = " unknown "
        manifest["limitations"] = "TBD"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "placeholders.yaml"
            path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
            result = self.run_validator(path)
        self.assertNotEqual(result.returncode, 0)
        for location in (
            "inputs[0].checksum",
            "software.tools[0].version",
            "software.containers[0].digest",
            "limitations",
        ):
            self.assertIn(f"{location} is incomplete", result.stdout)

    def test_extractor_redacts_common_credentials(self) -> None:
        redacted = load_redaction().redact_command(
            'export API_KEY="sensitive"\nexport DREMIO_PAT=another-secret\n'
            'curl -H "Authorization: Bearer token-value" url'
        )
        self.assertNotIn("sensitive", redacted)
        self.assertNotIn("another-secret", redacted)
        self.assertNotIn("token-value", redacted)
        self.assertGreaterEqual(redacted.count("$REDACTED"), 3)

    def test_redaction_covers_secret_flags_urls_and_headers(self) -> None:
        redact = load_redaction().redact_command
        cases = {
            "tool --password hunter2 --out x": "tool --password $REDACTED --out x",
            "tool --api-key sk-abc123 in.fa": "tool --api-key $REDACTED in.fa",
            "tool --access-key=AKIAFAKE1 in.fa": "tool --access-key=$REDACTED in.fa",
            "wget https://user:pw@host/f": "wget https://user:$REDACTED@host/f",
            "curl -H 'Authorization: Bearer abc' u": (
                "curl -H 'Authorization: Bearer $REDACTED' u"
            ),
            'curl -H "Authorization: Basic dXNl" u': (
                'curl -H "Authorization: Basic $REDACTED" u'
            ),
            "DB_PASSWORD=hunter2 run.sh": "DB_PASSWORD=$REDACTED run.sh",
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                self.assertEqual(redact(command), expected)

    def test_redaction_keeps_commands_that_hold_no_secret(self) -> None:
        redact = load_redaction().redact_command
        for command in (
            "sort --key=2 in.tsv",
            "sort --key 2 in.tsv",
            "tool --password --verbose",
            "wget https://user@host/f",
            "tool --keyfile ref.key",
        ):
            with self.subTest(command=command):
                self.assertEqual(redact(command), command)

    def test_redaction_stops_at_a_shell_separator(self) -> None:
        redact = load_redaction().redact_command
        cases = {
            "export DB_PASSWORD=hunter2; t x": "export DB_PASSWORD=$REDACTED; t x",
            "tool --token hunter2 | sort": "tool --token $REDACTED | sort",
            "(API_KEY=hunter2 tool)&& next": "(API_KEY=$REDACTED tool)&& next",
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                self.assertEqual(redact(command), expected)

    def test_redaction_covers_a_whole_shell_word(self) -> None:
        redact = load_redaction().redact_command
        commands = (
            ('API_KEY=prefix"FAKE_SUFFIX" tool', "FAKE_SUFFIX"),
            ("API_KEY=\"FAKE_A\"'FAKE_B'bare tool", "FAKE_"),
            ('tool --password "a\\"FAKE_TAIL" next', "FAKE_TAIL"),
            ("tool --password \\\n  FAKE_NEXT_LINE next", "FAKE_NEXT_LINE"),
            ("tool --token=pre'FAKE_Q'post next", "FAKE_Q"),
        )
        for command, fake in commands:
            with self.subTest(command=command):
                redacted = redact(command)
                self.assertNotIn(fake, redacted)
                self.assertIn("$REDACTED", redacted)
                self.assertTrue(redacted.endswith(("tool", "next")))

    def test_redaction_keeps_the_quote_that_closes_an_enclosing_string(self) -> None:
        redact = load_redaction().redact_command
        self.assertEqual(
            redact('bash -c "tool --password hunter2"'),
            'bash -c "tool --password $REDACTED"',
        )
        self.assertEqual(
            redact("curl -H 'Authorization: Bearer abc' url"),
            "curl -H 'Authorization: Bearer $REDACTED' url",
        )

    def test_redaction_matches_whole_flag_name_segments(self) -> None:
        redact = load_redaction().redact_command
        for flag in (
            "--token",
            "--auth-token",
            "--api-key",
            "--api_key",
            "--apikey",
            "--access-key",
            "--client-secret",
            "--db-password",
        ):
            with self.subTest(flag=flag):
                self.assertEqual(
                    redact(f"tool {flag} FAKE_VALUE"), f"tool {flag} $REDACTED"
                )
        for flag in (
            "--tokenizer",
            "--max-tokens",
            "--key",
            "--keyfile",
            "--secretary",
        ):
            with self.subTest(flag=flag):
                command = f"tool {flag} model.json"
                self.assertEqual(redact(command), command)

    def test_redaction_runs_in_linear_time_on_a_long_word(self) -> None:
        redact = load_redaction().redact_command
        start = time.perf_counter()
        redact("tool " + "A" * 200_000)
        self.assertLess(time.perf_counter() - start, 2.0)
        self.assertEqual(
            redact("wget https://user:FAKEPW@host/f"),
            "wget https://user:$REDACTED@host/f",
        )

    def run_extractor(self, script: Path, args: list, out: Path) -> str:
        result = subprocess.run(
            ["uv", "run", "--script", script, *args, "--out", out],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return out.read_text()

    def test_cwl_extractor_redacts_the_launch_command(self) -> None:
        record = json.loads((CWL_FIXTURE / "provenance.json").read_text())
        record["launch_command"] = "cwltool --api-key FAKE_LAUNCH_SECRET workflow.cwl"
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            (tmp / "provenance.json").write_text(json.dumps(record))
            text = self.run_extractor(
                CWL_EXTRACTOR,
                ["--provenance", tmp / "provenance.json"],
                tmp / "cwl.yaml",
            )
        self.assertNotIn("FAKE_LAUNCH_SECRET", text)
        self.assertIn("--api-key $REDACTED", text)

    def test_snakemake_extractor_redacts_the_launch_command(self) -> None:
        fixture = SKILL_ROOT / "fixtures" / "snakemake"
        args = [
            "--jobs", fixture / "jobs.jsonl",
            "--outputs-manifest", fixture / "outputs.txt",
            "--run-id", "r", "--pipeline-name", "p", "--pipeline-version", "1",
            "--commit-sha", "abc", "--engine-version", "9",
            "--launch-command", "snakemake --api-key FAKE_LAUNCH_SECRET",
        ]  # fmt: skip
        with tempfile.TemporaryDirectory() as tmp_dir:
            text = self.run_extractor(
                SNAKEMAKE_EXTRACTOR, args, Path(tmp_dir) / "smk.yaml"
            )
        self.assertNotIn("FAKE_LAUNCH_SECRET", text)
        self.assertIn("--api-key $REDACTED", text)

    def test_nextflow_extractor_redacts_the_launch_command(self) -> None:
        fixture = SKILL_ROOT / "fixtures" / "nextflow"
        args = [
            "--trace", fixture / "trace.txt", "--workdir", fixture / "work",
            "--run-id", "r", "--pipeline-name", "p", "--pipeline-version", "1",
            "--commit-sha", "abc", "--engine-version", "9",
            "--launch-command", "nextflow run main.nf --api-key FAKE_LAUNCH_SECRET",
            "--tool-versions", fixture / "tool-versions.json",
            "--outputs-manifest", fixture / "outputs.txt",
        ]  # fmt: skip
        with tempfile.TemporaryDirectory() as tmp_dir:
            text = self.run_extractor(EXTRACTOR, args, Path(tmp_dir) / "nf.yaml")
        self.assertNotIn("FAKE_LAUNCH_SECRET", text)
        self.assertIn("--api-key $REDACTED", text)

    def test_snakemake_and_cwl_extractors_redact_credentials(self) -> None:
        command = "fetch --password hunter2 https://user:pw@host/f"
        job = {
            "rule": "fetch",
            "status": "completed",
            "tool": "fetch",
            "version": "1.0",
            "command": command,
            "inputs": ["a"],
            "outputs": ["b"],
        }
        record = json.loads((CWL_FIXTURE / "provenance.json").read_text())
        record["steps"][0]["command"] = command
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            (tmp / "jobs.jsonl").write_text(json.dumps(job) + "\n")
            (tmp / "outputs.txt").write_text("b\n")
            (tmp / "provenance.json").write_text(json.dumps(record))
            snakemake_args = [
                "--jobs",
                tmp / "jobs.jsonl",
                "--outputs-manifest",
                tmp / "outputs.txt",
            ]
            snakemake_args += [
                "--run-id",
                "r",
                "--pipeline-name",
                "p",
                "--pipeline-version",
                "1",
            ]
            snakemake_args += [
                "--commit-sha",
                "abc",
                "--engine-version",
                "9",
                "--launch-command",
                "s",
            ]
            runs = {
                "snakemake.yaml": (SNAKEMAKE_EXTRACTOR, snakemake_args),
                "cwl.yaml": (CWL_EXTRACTOR, ["--provenance", tmp / "provenance.json"]),
            }
            for name, (script, args) in runs.items():
                out = tmp / name
                result = subprocess.run(
                    ["uv", "run", "--script", script, *args, "--out", out],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                text = out.read_text()
                self.assertNotIn("hunter2", text, name)
                self.assertNotIn(":pw@", text, name)
                self.assertIn("--password $REDACTED", text, name)

    def test_realistic_nextflow_trace_reaches_complete_manifest(self) -> None:
        fixture = SKILL_ROOT / "fixtures" / "nextflow"
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "nextflow.yaml"
            extracted = subprocess.run([
                "uv", "run", str(EXTRACTOR), "--trace", str(fixture / "trace.txt"),
                "--workdir", str(fixture / "work"), "--out", str(manifest),
                "--run-id", "nf-fixture-1", "--pipeline-name", "qc-workflow",
                "--pipeline-version", "1.0.0", "--commit-sha", "0123456789abcdef0123456789abcdef01234567",
                "--engine-version", "25.10.3", "--launch-command", "nextflow run main.nf",
                "--tool-versions", str(fixture / "tool-versions.json"),
                "--outputs-manifest", str(fixture / "outputs.txt"),
            ], text=True, capture_output=True)
            self.assertEqual(extracted.returncode, 0, extracted.stderr)
            validated = self.run_validator(manifest)
            self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)

    def test_snakemake_and_cwl_extractors_reach_complete_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            snakemake_fixture = SKILL_ROOT / "fixtures" / "snakemake"
            snakemake = tmp / "snakemake.yaml"
            result = subprocess.run([
                "uv", "run", "--script", str(SNAKEMAKE_EXTRACTOR), "--jobs", str(snakemake_fixture / "jobs.jsonl"),
                "--outputs-manifest", str(snakemake_fixture / "outputs.txt"), "--out", str(snakemake),
                "--run-id", "smk-fixture-1", "--pipeline-name", "qc-workflow", "--pipeline-version", "1.0.0",
                "--commit-sha", "0123456789abcdef0123456789abcdef01234567", "--engine-version", "9.8.1",
                "--launch-command", "snakemake --cores 1",
            ], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.run_validator(snakemake).returncode, 0)

            cwl = tmp / "cwl.yaml"
            result = subprocess.run(["uv", "run", "--script", str(CWL_EXTRACTOR), "--provenance", str(SKILL_ROOT / "fixtures" / "cwl" / "provenance.json"), "--out", str(cwl)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.run_validator(cwl).returncode, 0)


if __name__ == "__main__":
    unittest.main()
