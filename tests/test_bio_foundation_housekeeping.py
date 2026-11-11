from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "bio-foundation-housekeeping"
SCRIPT = SKILL_ROOT / "scripts" / "build_sample_catalog.py"
MODEL_SCRIPT = SKILL_ROOT / "scripts" / "generate_models.py"
CATALOG_SCRIPT = SKILL_ROOT / "scripts" / "build_metadata_catalog.py"
SCHEMA = SKILL_ROOT / "schemas" / "project-metadata.yaml"


class BioFoundationHousekeepingTests(unittest.TestCase):
    def run_pipeline(self, fixture: str, project_root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "uv",
                "run",
                "--script",
                str(SCRIPT),
                "--input",
                str(SKILL_ROOT / "fixtures" / fixture),
                "--project-root",
                str(project_root),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_valid_fixture_writes_nonempty_parquet_and_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "project"
            result = self.run_pipeline("valid-samples.jsonl", project)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Validated 2 record(s)", result.stdout)
            self.assertGreater((project / "data" / "normalized" / "samples.parquet").stat().st_size, 0)
            self.assertGreater((project / "data" / "catalog.duckdb").stat().st_size, 0)
            report = project / "results" / "bio-foundation-housekeeping" / "report.md"
            self.assertIn("Status: passed", report.read_text(encoding="utf-8"))

    def test_invalid_fixture_stops_before_parquet_or_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "project"
            result = self.run_pipeline("invalid-samples.jsonl", project)

            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("before ingestion", result.stdout)
            self.assertFalse((project / "data" / "normalized" / "samples.parquet").exists())
            self.assertFalse((project / "data" / "catalog.duckdb").exists())
            rejections = project / "results" / "bio-foundation-housekeeping" / "rejections.json"
            rejection_text = rejections.read_text(encoding="utf-8")
            self.assertIn('"unexpected"', rejection_text)
            self.assertNotIn("must fail", rejection_text)

    def test_duplicate_identifier_stops_before_ingestion(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            fixture = tmp / "duplicates.jsonl"
            record = (
                '{"sample_id":"S001","organism":"Test organism",'
                '"collection_date":"2026-05-01","platform":"ILLUMINA",'
                '"read_count":100,"mean_coverage":1.0}\n'
            )
            fixture.write_text(record + record, encoding="utf-8")
            project = tmp / "project"
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "--script",
                    str(SCRIPT),
                    "--input",
                    str(fixture),
                    "--project-root",
                    str(project),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 2, result.stderr)
            rejections = project / "results" / "bio-foundation-housekeeping" / "rejections.json"
            self.assertIn("duplicate_sample_id", rejections.read_text(encoding="utf-8"))
            self.assertFalse((project / "data" / "catalog.duckdb").exists())

    def test_existing_outputs_are_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "project"
            first = self.run_pipeline("valid-samples.jsonl", project)
            self.assertEqual(first.returncode, 0, first.stderr)
            artifacts = [
                project / "data" / "normalized" / "samples.parquet",
                project / "data" / "catalog.duckdb",
            ]
            before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in artifacts]

            second = self.run_pipeline("valid-samples.jsonl", project)

            after = [hashlib.sha256(path.read_bytes()).hexdigest() for path in artifacts]
            self.assertEqual(second.returncode, 2, second.stderr)
            self.assertIn("refusing to overwrite", second.stdout)
            self.assertEqual(before, after)


class LinkedMetadataCatalogTests(unittest.TestCase):
    def run_pipeline(self, fixture: str, project_root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "uv",
                "run",
                "--script",
                str(CATALOG_SCRIPT),
                "--schema",
                str(SCHEMA),
                "--input",
                str(SKILL_ROOT / "fixtures" / fixture),
                "--project-root",
                str(project_root),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def rejection_types(self, project: Path) -> set[str]:
        payload = json.loads(
            (
                project
                / "results"
                / "bio-foundation-housekeeping"
                / "rejections.json"
            ).read_text(encoding="utf-8")
        )
        return {item["type"] for item in payload["errors"]}

    def test_linkml_generation_is_importable_idempotent_and_portable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "project_metadata.py"
            command = [
                "uv",
                "run",
                "--script",
                str(MODEL_SCRIPT),
                "--schema",
                str(SCHEMA),
                "--output",
                str(output),
                "--expect-class",
                "MetadataBundle",
                "--expect-class",
                "ProvenanceRecord",
            ]
            generated = subprocess.run(command, text=True, capture_output=True, check=False)
            checked = subprocess.run(
                [*command, "--check"], text=True, capture_output=True, check=False
            )

            self.assertEqual(generated.returncode, 0, generated.stderr)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            source = output.read_text(encoding="utf-8")
            self.assertIn("class MetadataBundle", source)
            self.assertIn("extra = \"forbid\"", source)
            self.assertNotIn(str(REPO_ROOT), source)

    def test_linkml_generation_refuses_to_replace_changed_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "project_metadata.py"
            output.write_text("user-owned content\n", encoding="utf-8")

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "--script",
                    str(MODEL_SCRIPT),
                    "--schema",
                    str(SCHEMA),
                    "--output",
                    str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("refusing to overwrite", result.stdout)
            self.assertEqual(output.read_text(encoding="utf-8"), "user-owned content\n")

    def test_invalid_linkml_schema_does_not_create_a_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            schema = tmp / "invalid.yaml"
            schema.write_text("name: incomplete\n", encoding="utf-8")
            output = tmp / "project_metadata.py"

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "--script",
                    str(MODEL_SCRIPT),
                    "--schema",
                    str(schema),
                    "--output",
                    str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertTrue(result.stdout.strip())
            self.assertFalse(output.exists())

    def test_valid_linked_fixture_writes_all_normalized_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "project"
            result = self.run_pipeline("valid-project-metadata.json", project)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("wrote 6 Parquet tables", result.stdout)
            for table_name in (
                "samples",
                "runs",
                "files",
                "results",
                "result_inputs",
                "provenance",
            ):
                parquet = project / "data" / "normalized" / f"{table_name}.parquet"
                self.assertGreater(parquet.stat().st_size, 0)
            self.assertGreater((project / "data" / "catalog.duckdb").stat().st_size, 0)
            self.assertGreater((project / "schemas" / "project-metadata.yaml").stat().st_size, 0)
            generated = project / "schemas" / "generated" / "project_metadata.py"
            self.assertIn("class MetadataBundle", generated.read_text(encoding="utf-8"))
            report = project / "results" / "bio-foundation-housekeeping" / "report.md"
            report_text = report.read_text(encoding="utf-8")
            self.assertIn("Status: passed", report_text)
            self.assertIn("| result_inputs | 2 |", report_text)

    def test_invalid_model_fixture_stops_before_artifact_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "project"
            result = self.run_pipeline("invalid-project-metadata.json", project)

            self.assertEqual(result.returncode, 2, result.stderr)
            rejection = project / "results" / "bio-foundation-housekeeping" / "rejections.json"
            rejection_text = rejection.read_text(encoding="utf-8")
            self.assertIn("extra_forbidden", rejection_text)
            self.assertNotIn("must not be copied", rejection_text)
            self.assertFalse((project / "schemas" / "project-metadata.yaml").exists())
            self.assertFalse((project / "data" / "normalized").exists())
            self.assertFalse((project / "data" / "catalog.duckdb").exists())

    def test_broken_foreign_keys_are_reported_together_before_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "project"
            result = self.run_pipeline("invalid-foreign-keys.json", project)

            self.assertEqual(result.returncode, 2, result.stderr)
            error_types = self.rejection_types(project)
            self.assertTrue(
                {
                    "missing_sample_foreign_key",
                    "missing_run_foreign_key",
                    "missing_input_file_foreign_key",
                    "missing_output_file_foreign_key",
                    "missing_result_foreign_key",
                }
                <= error_types
            )
            self.assertFalse((project / "schemas" / "generated").exists())
            self.assertFalse((project / "data" / "catalog.duckdb").exists())

    def test_invalid_result_relationships_are_reported_together(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "project"
            result = self.run_pipeline("invalid-result-relations.json", project)

            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertTrue(
                {
                    "empty_result_inputs",
                    "duplicate_result_input",
                    "invalid_output_file_role",
                    "output_is_input",
                    "duplicate_result_output",
                }
                <= self.rejection_types(project)
            )
            self.assertFalse((project / "data" / "catalog.duckdb").exists())

    def test_invalid_provenance_cardinality_is_reported_together(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "project"
            result = self.run_pipeline("invalid-provenance-cardinality.json", project)

            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertTrue(
                {"duplicate_result_provenance", "missing_provenance"}
                <= self.rejection_types(project)
            )
            self.assertFalse((project / "data" / "catalog.duckdb").exists())

    def test_duplicate_identifiers_stop_before_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            payload = json.loads(
                (SKILL_ROOT / "fixtures" / "valid-project-metadata.json").read_text(
                    encoding="utf-8"
                )
            )
            payload["samples"].append(payload["samples"][0])
            fixture = tmp / "duplicate-project-metadata.json"
            fixture.write_text(json.dumps(payload), encoding="utf-8")
            project = tmp / "project"

            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "--script",
                    str(CATALOG_SCRIPT),
                    "--schema",
                    str(SCHEMA),
                    "--input",
                    str(fixture),
                    "--project-root",
                    str(project),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 2, result.stderr)
            rejection = project / "results" / "bio-foundation-housekeeping" / "rejections.json"
            self.assertIn("duplicate_sample_id", rejection.read_text(encoding="utf-8"))
            self.assertFalse((project / "data" / "catalog.duckdb").exists())

    def test_every_record_identifier_rejects_duplicates(self) -> None:
        source = json.loads(
            (SKILL_ROOT / "fixtures" / "valid-project-metadata.json").read_text(
                encoding="utf-8"
            )
        )
        cases = (
            ("samples", "duplicate_sample_id"),
            ("runs", "duplicate_run_id"),
            ("files", "duplicate_file_id"),
            ("results", "duplicate_result_id"),
            ("provenance", "duplicate_provenance_id"),
        )
        for collection, expected_error in cases:
            with self.subTest(collection=collection), tempfile.TemporaryDirectory() as tmpdir:
                tmp = Path(tmpdir)
                payload = json.loads(json.dumps(source))
                payload[collection].append(payload[collection][0])
                fixture = tmp / "duplicate-project-metadata.json"
                fixture.write_text(json.dumps(payload), encoding="utf-8")
                project = tmp / "project"

                result = subprocess.run(
                    [
                        "uv",
                        "run",
                        "--script",
                        str(CATALOG_SCRIPT),
                        "--schema",
                        str(SCHEMA),
                        "--input",
                        str(fixture),
                        "--project-root",
                        str(project),
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )

                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(expected_error, self.rejection_types(project))
                self.assertFalse((project / "data" / "catalog.duckdb").exists())

    def test_existing_linked_outputs_are_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "project"
            first = self.run_pipeline("valid-project-metadata.json", project)
            self.assertEqual(first.returncode, 0, first.stderr)
            artifacts = [
                project / "schemas" / "project-metadata.yaml",
                project / "schemas" / "generated" / "project_metadata.py",
                project / "data" / "normalized" / "samples.parquet",
                project / "data" / "catalog.duckdb",
            ]
            before = [hashlib.sha256(path.read_bytes()).hexdigest() for path in artifacts]

            second = self.run_pipeline("valid-project-metadata.json", project)

            after = [hashlib.sha256(path.read_bytes()).hexdigest() for path in artifacts]
            self.assertEqual(second.returncode, 2, second.stderr)
            self.assertIn("refusing to overwrite", second.stdout)
            self.assertEqual(before, after)

    def run_generate_models(self, output: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "uv",
                "run",
                "--script",
                str(MODEL_SCRIPT),
                "--schema",
                str(SCHEMA),
                "--output",
                str(output),
                "--expect-class",
                "MetadataBundle",
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def run_build(
        self, schema: Path, project: Path
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "uv",
                "run",
                "--script",
                str(CATALOG_SCRIPT),
                "--schema",
                str(schema),
                "--input",
                str(SKILL_ROOT / "fixtures" / "valid-project-metadata.json"),
                "--project-root",
                str(project),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_documented_steps_run_in_order_without_collision(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            model = project / "schemas" / "generated" / "project_metadata.py"
            generated = self.run_generate_models(model)
            self.assertEqual(generated.returncode, 0, generated.stdout)
            before = model.read_bytes()

            built = self.run_build(SCHEMA, project)

            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            self.assertEqual(model.read_bytes(), before)
            self.assertGreater((project / "data" / "catalog.duckdb").stat().st_size, 0)

    def test_schema_adapted_in_place_can_be_the_build_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            schema = project / "schemas" / "project-metadata.yaml"
            schema.parent.mkdir(parents=True)
            schema.write_bytes(SCHEMA.read_bytes())

            built = self.run_build(schema, project)

            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            self.assertEqual(schema.read_bytes(), SCHEMA.read_bytes())
            self.assertGreater((project / "data" / "catalog.duckdb").stat().st_size, 0)

    def test_target_with_different_content_is_still_refused(self) -> None:
        for relative in (
            Path("schemas") / "generated" / "project_metadata.py",
            Path("schemas") / "project-metadata.yaml",
        ):
            with (
                self.subTest(target=str(relative)),
                tempfile.TemporaryDirectory() as tmpdir,
            ):
                project = Path(tmpdir)
                target = project / relative
                target.parent.mkdir(parents=True)
                target.write_text("# project-owned content\n", encoding="utf-8")

                built = self.run_build(SCHEMA, project)

                self.assertEqual(built.returncode, 2, built.stdout + built.stderr)
                self.assertIn("refusing to overwrite", built.stdout)
                self.assertIn(str(target), built.stdout)
                self.assertEqual(
                    target.read_text(encoding="utf-8"), "# project-owned content\n"
                )
                self.assertFalse((project / "data" / "catalog.duckdb").exists())

    def test_the_overwrite_check_does_not_read_an_existing_catalog(self) -> None:
        # Load only the preflight code: the script's own imports (duckdb,
        # linkml) are not needed to reach the refusal.
        wanted = {"build_outputs", "final_artifacts"}
        nodes = [
            node
            for node in ast.parse(CATALOG_SCRIPT.read_text(encoding="utf-8")).body
            if (isinstance(node, ast.FunctionDef) and node.name in wanted)
            or (
                isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "TABLE_NAMES"
                    for target in node.targets
                )
            )
        ]
        namespace: dict[str, Any] = {"Path": Path, "Any": Any}
        exec(  # noqa: S102  # runs the script's own preflight functions, no other code
            compile(
                ast.Module(body=nodes, type_ignores=[]), str(CATALOG_SCRIPT), "exec"
            ),
            namespace,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            catalog = project / "data" / "catalog.duckdb"
            catalog.parent.mkdir()
            catalog.write_bytes(b"project-owned database")
            original_read_bytes = Path.read_bytes
            read_paths: list[Path] = []

            def recording_read_bytes(path: Path) -> bytes:
                read_paths.append(path)
                return original_read_bytes(path)

            with (
                mock.patch.object(Path, "read_bytes", recording_read_bytes),
                self.assertRaises(FileExistsError),
            ):
                namespace["build_outputs"](
                    project, SCHEMA, project / "input.json", "", None
                )
            self.assertNotIn(catalog, read_paths)


if __name__ == "__main__":
    unittest.main()
