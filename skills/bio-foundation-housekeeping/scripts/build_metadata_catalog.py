#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "duckdb==1.5.3",
#   "linkml==1.11.1",
#   "pydantic==2.13.4",
# ]
# ///
"""Generate models, validate linked metadata, and build Parquet plus DuckDB outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from importlib.metadata import version
from pathlib import Path
from typing import Any

import duckdb
from pydantic import ValidationError

from generate_models import generate_source, load_module

TABLE_NAMES = ("samples", "runs", "files", "results", "result_inputs", "provenance")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def issue(location: str, error_type: str, message: str) -> dict[str, str]:
    return {"location": location, "type": error_type, "message": message}


def write_rejection_report(
    project_root: Path,
    input_path: Path,
    rejected: list[dict[str, str]],
) -> None:
    result_dir = project_root / "results" / "bio-foundation-housekeeping"
    log_dir = result_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "rejected",
        "input_file": input_path.name,
        "errors": rejected,
    }
    (result_dir / "rejections.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    (result_dir / "report.md").write_text(
        "# Metadata validation report\n\n"
        "Status: rejected before schema, model, Parquet, or DuckDB publication.\n\n"
        f"Validation errors: {len(rejected)}.\n",
        encoding="utf-8",
    )
    (log_dir / "run.log").write_text(
        f"validation failed with {len(rejected)} error(s)\n", encoding="utf-8"
    )


def validate_bundle(input_path: Path, model_class: type[Any]) -> tuple[Any | None, list[dict[str, str]]]:
    try:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [issue("document", "json_invalid", exc.msg)]

    try:
        bundle = model_class.model_validate(payload)
    except ValidationError as exc:
        errors = [
            issue(
                ".".join(str(part) for part in item["loc"]),
                item["type"],
                item["msg"],
            )
            for item in exc.errors(include_input=False, include_url=False)
        ]
        return None, errors
    return bundle, []


def duplicate_issues(records: list[Any], field: str, collection: str) -> list[dict[str, str]]:
    seen: set[str] = set()
    duplicates: list[dict[str, str]] = []
    for index, record in enumerate(records):
        value = str(getattr(record, field))
        if value in seen:
            duplicates.append(
                issue(
                    f"{collection}.{index}.{field}",
                    f"duplicate_{field}",
                    f"{field} must be unique within {collection}",
                )
            )
        seen.add(value)
    return duplicates


def cross_record_issues(bundle: Any) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    for records, field, collection in (
        (bundle.samples, "sample_id", "samples"),
        (bundle.runs, "run_id", "runs"),
        (bundle.files, "file_id", "files"),
        (bundle.results, "result_id", "results"),
        (bundle.provenance, "provenance_id", "provenance"),
    ):
        errors.extend(duplicate_issues(records, field, collection))

    sample_ids = {record.sample_id for record in bundle.samples}
    run_ids = {record.run_id for record in bundle.runs}
    files = {record.file_id: record for record in bundle.files}
    result_ids = {record.result_id for record in bundle.results}

    for index, run in enumerate(bundle.runs):
        if run.sample_id not in sample_ids:
            errors.append(
                issue(
                    f"runs.{index}.sample_id",
                    "missing_sample_foreign_key",
                    "sample_id must reference samples.sample_id",
                )
            )

    for index, file_record in enumerate(bundle.files):
        if file_record.run_id not in run_ids:
            errors.append(
                issue(
                    f"files.{index}.run_id",
                    "missing_run_foreign_key",
                    "run_id must reference runs.run_id",
                )
            )

    output_file_ids: set[str] = set()
    for index, result in enumerate(bundle.results):
        if not result.input_file_ids:
            errors.append(
                issue(
                    f"results.{index}.input_file_ids",
                    "empty_result_inputs",
                    "at least one input file is required",
                )
            )
        if len(set(result.input_file_ids)) != len(result.input_file_ids):
            errors.append(
                issue(
                    f"results.{index}.input_file_ids",
                    "duplicate_result_input",
                    "input_file_ids must not contain duplicates",
                )
            )
        for input_index, file_id in enumerate(result.input_file_ids):
            if file_id not in files:
                errors.append(
                    issue(
                        f"results.{index}.input_file_ids.{input_index}",
                        "missing_input_file_foreign_key",
                        "input_file_id must reference files.file_id",
                    )
                )
        output = files.get(result.output_file_id)
        if output is None:
            errors.append(
                issue(
                    f"results.{index}.output_file_id",
                    "missing_output_file_foreign_key",
                    "output_file_id must reference files.file_id",
                )
            )
        elif output.role != "RESULT":
            errors.append(
                issue(
                    f"results.{index}.output_file_id",
                    "invalid_output_file_role",
                    "output_file_id must reference a file with role RESULT",
                )
            )
        if result.output_file_id in result.input_file_ids:
            errors.append(
                issue(
                    f"results.{index}.output_file_id",
                    "output_is_input",
                    "a result output cannot also be one of its inputs",
                )
            )
        if result.output_file_id in output_file_ids:
            errors.append(
                issue(
                    f"results.{index}.output_file_id",
                    "duplicate_result_output",
                    "one file cannot be the output of multiple results",
                )
            )
        output_file_ids.add(result.output_file_id)

    provenance_results: set[str] = set()
    for index, provenance in enumerate(bundle.provenance):
        if provenance.result_id not in result_ids:
            errors.append(
                issue(
                    f"provenance.{index}.result_id",
                    "missing_result_foreign_key",
                    "result_id must reference results.result_id",
                )
            )
        if provenance.result_id in provenance_results:
            errors.append(
                issue(
                    f"provenance.{index}.result_id",
                    "duplicate_result_provenance",
                    "each result must have exactly one provenance record",
                )
            )
        provenance_results.add(provenance.result_id)
    for index, result in enumerate(bundle.results):
        if result.result_id not in provenance_results:
            errors.append(
                issue(
                    f"results.{index}.result_id",
                    "missing_provenance",
                    "each result must have exactly one provenance record",
                )
            )
    return errors


def rows_from_bundle(bundle: Any) -> dict[str, list[tuple[Any, ...]]]:
    return {
        "samples": [
            (row.sample_id, row.organism, row.collection_date) for row in bundle.samples
        ],
        "runs": [
            (row.run_id, row.sample_id, row.platform, row.instrument) for row in bundle.runs
        ],
        "files": [
            (row.file_id, row.run_id, row.path, row.role, row.size_bytes, row.sha256)
            for row in bundle.files
        ],
        "results": [
            (row.result_id, row.result_type, row.output_file_id) for row in bundle.results
        ],
        "result_inputs": [
            (result.result_id, ordinal, file_id)
            for result in bundle.results
            for ordinal, file_id in enumerate(result.input_file_ids, start=1)
        ],
        "provenance": [
            (row.provenance_id, row.result_id, row.tool, row.tool_version, row.command)
            for row in bundle.provenance
        ],
    }


def create_catalog(catalog_path: Path, parquet_dir: Path, rows: dict[str, list[tuple[Any, ...]]]) -> None:
    connection = duckdb.connect(str(catalog_path))
    try:
        connection.execute(
            "CREATE TABLE samples (sample_id VARCHAR PRIMARY KEY, organism VARCHAR NOT NULL, collection_date DATE NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE runs (run_id VARCHAR PRIMARY KEY, sample_id VARCHAR NOT NULL REFERENCES samples(sample_id), platform VARCHAR NOT NULL, instrument VARCHAR NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE files (file_id VARCHAR PRIMARY KEY, run_id VARCHAR NOT NULL REFERENCES runs(run_id), path VARCHAR NOT NULL, role VARCHAR NOT NULL, size_bytes BIGINT NOT NULL CHECK (size_bytes > 0), sha256 VARCHAR NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE results (result_id VARCHAR PRIMARY KEY, result_type VARCHAR NOT NULL, output_file_id VARCHAR NOT NULL UNIQUE REFERENCES files(file_id))"
        )
        connection.execute(
            "CREATE TABLE result_inputs (result_id VARCHAR NOT NULL REFERENCES results(result_id), ordinal INTEGER NOT NULL, input_file_id VARCHAR NOT NULL REFERENCES files(file_id), PRIMARY KEY (result_id, ordinal), UNIQUE (result_id, input_file_id))"
        )
        connection.execute(
            "CREATE TABLE provenance (provenance_id VARCHAR PRIMARY KEY, result_id VARCHAR NOT NULL UNIQUE REFERENCES results(result_id), tool VARCHAR NOT NULL, tool_version VARCHAR NOT NULL, command VARCHAR NOT NULL)"
        )
        statements = {
            "samples": "INSERT INTO samples VALUES (?, ?, ?)",
            "runs": "INSERT INTO runs VALUES (?, ?, ?, ?)",
            "files": "INSERT INTO files VALUES (?, ?, ?, ?, ?, ?)",
            "results": "INSERT INTO results VALUES (?, ?, ?)",
            "result_inputs": "INSERT INTO result_inputs VALUES (?, ?, ?)",
            "provenance": "INSERT INTO provenance VALUES (?, ?, ?, ?, ?)",
        }
        for table_name in TABLE_NAMES:
            if rows[table_name]:
                connection.executemany(statements[table_name], rows[table_name])

        parquet_dir.mkdir(parents=True, exist_ok=True)
        for table_name in TABLE_NAMES:
            path = parquet_dir / f"{table_name}.parquet"
            connection.execute(
                f"COPY {table_name} TO ? (FORMAT PARQUET, COMPRESSION zstd)",
                [str(path)],
            )
            count = connection.execute(
                "SELECT COUNT(*) FROM read_parquet(?)", [str(path)]
            ).fetchone()[0]
            if count != len(rows[table_name]):
                raise RuntimeError(
                    f"Parquet row count mismatch for {table_name}: "
                    f"expected {len(rows[table_name])}, found {count}"
                )

        connection.execute(
            "CREATE TABLE catalog_sources (table_name VARCHAR PRIMARY KEY, parquet_path VARCHAR NOT NULL, sha256 VARCHAR NOT NULL, row_count BIGINT NOT NULL)"
        )
        connection.executemany(
            "INSERT INTO catalog_sources VALUES (?, ?, ?, ?)",
            [
                (
                    table_name,
                    f"data/normalized/{table_name}.parquet",
                    sha256(parquet_dir / f"{table_name}.parquet"),
                    len(rows[table_name]),
                )
                for table_name in TABLE_NAMES
            ],
        )
        source_count = connection.execute("SELECT COUNT(*) FROM catalog_sources").fetchone()[0]
        if source_count != len(TABLE_NAMES):
            raise RuntimeError("catalog_sources is incomplete")
    finally:
        connection.close()


def final_artifacts(project_root: Path) -> dict[str, Path]:
    artifacts = {
        "schema": project_root / "schemas" / "project-metadata.yaml",
        "model": project_root / "schemas" / "generated" / "project_metadata.py",
        "catalog": project_root / "data" / "catalog.duckdb",
    }
    artifacts.update(
        {
            table_name: project_root / "data" / "normalized" / f"{table_name}.parquet"
            for table_name in TABLE_NAMES
        }
    )
    return artifacts


def build_outputs(
    project_root: Path,
    schema_path: Path,
    input_path: Path,
    model_source: str,
    bundle: Any,
) -> dict[str, Path]:
    artifacts = final_artifacts(project_root)
    existing = [path for path in artifacts.values() if path.exists()]
    if existing:
        raise FileExistsError(
            "refusing to overwrite existing output(s): " + ", ".join(str(path) for path in existing)
        )

    project_root.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix="foundation-", dir=project_root))
    staged_schema = temporary / "schemas" / "project-metadata.yaml"
    staged_model = temporary / "schemas" / "generated" / "project_metadata.py"
    staged_parquet = temporary / "data" / "normalized"
    staged_catalog = temporary / "data" / "catalog.duckdb"
    staged_schema.parent.mkdir(parents=True, exist_ok=True)
    staged_model.parent.mkdir(parents=True, exist_ok=True)
    staged_catalog.parent.mkdir(parents=True, exist_ok=True)

    rows = rows_from_bundle(bundle)
    try:
        staged_schema.write_text(schema_path.read_text(encoding="utf-8"), encoding="utf-8")
        staged_model.write_text(model_source, encoding="utf-8")
        create_catalog(staged_catalog, staged_parquet, rows)

        staged = {
            "schema": staged_schema,
            "model": staged_model,
            "catalog": staged_catalog,
            **{
                table_name: staged_parquet / f"{table_name}.parquet"
                for table_name in TABLE_NAMES
            },
        }
        for name, source in staged.items():
            if not source.is_file() or source.stat().st_size == 0:
                raise RuntimeError(f"staged artifact is missing or empty: {name}")

        for target in artifacts.values():
            target.parent.mkdir(parents=True, exist_ok=True)
        published: list[Path] = []
        try:
            for name in ("schema", "model", *TABLE_NAMES, "catalog"):
                staged[name].replace(artifacts[name])
                published.append(artifacts[name])
        except OSError as exc:
            rollback_failures: list[Path] = []
            for path in reversed(published):
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    rollback_failures.append(path)
            if rollback_failures:
                failed = ", ".join(str(path) for path in rollback_failures)
                raise RuntimeError(f"publication failed and rollback could not remove: {failed}") from exc
            raise
    finally:
        shutil.rmtree(temporary, ignore_errors=True)

    result_dir = project_root / "results" / "bio-foundation-housekeeping"
    log_dir = result_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    report_lines = [
        "# Metadata validation report",
        "",
        "Status: passed.",
        "",
        f"Input: `{input_path.name}`.",
        "",
        f"LinkML schema SHA-256: `{sha256(artifacts['schema'])}`.",
        "",
        "Dependencies: "
        + ", ".join(
            f"{name} {version(name)}" for name in ("linkml", "pydantic", "duckdb")
        )
        + ".",
        "",
        "| Table | Rows | Parquet SHA-256 |",
        "|---|---:|---|",
    ]
    for table_name in TABLE_NAMES:
        report_lines.append(
            f"| {table_name} | {len(rows[table_name])} | `{sha256(artifacts[table_name])}` |"
        )
    (result_dir / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    (log_dir / "run.log").write_text(
        "generated LinkML/Pydantic models and ingested validated linked records\n",
        encoding="utf-8",
    )
    return artifacts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True, help="JSON metadata bundle")
    parser.add_argument("--project-root", type=Path, required=True)
    args = parser.parse_args(argv)

    schema_path = args.schema.expanduser().resolve()
    input_path = args.input.expanduser().resolve()
    project_root = args.project_root.expanduser().resolve()
    if not schema_path.is_file():
        parser.error(f"schema does not exist: {schema_path}")
    if not input_path.is_file():
        parser.error(f"input does not exist: {input_path}")

    try:
        model_source = generate_source(schema_path)
        with tempfile.TemporaryDirectory(prefix="foundation-model-") as tmpdir:
            model_path = Path(tmpdir) / "project_metadata.py"
            model_path.write_text(model_source, encoding="utf-8")
            module = load_module(model_path)
            model_class = getattr(module, "MetadataBundle")
    except Exception as exc:
        rejected = [
            issue(
                "schema",
                "schema_generation_failed",
                f"LinkML model generation failed with {type(exc).__name__}",
            )
        ]
        write_rejection_report(project_root, input_path, rejected)
        print("Rejected schema before artifact publication")
        return 2

    bundle, rejected = validate_bundle(input_path, model_class)
    if bundle is not None:
        rejected.extend(cross_record_issues(bundle))
    if rejected:
        write_rejection_report(project_root, input_path, rejected)
        print(f"Rejected {len(rejected)} validation error(s) before artifact publication")
        return 2
    if bundle is None:
        raise RuntimeError("validated metadata bundle is unexpectedly missing")

    try:
        artifacts = build_outputs(project_root, schema_path, input_path, model_source, bundle)
    except FileExistsError as exc:
        print(str(exc))
        return 2
    except (OSError, RuntimeError, duckdb.Error) as exc:
        write_rejection_report(
            project_root,
            input_path,
            [
                issue(
                    "publication",
                    "artifact_publication_failed",
                    f"artifact publication failed with {type(exc).__name__}",
                )
            ],
        )
        print("Artifact publication failed before the catalog completion marker")
        return 2
    print(
        f"Validated linked metadata and wrote {len(TABLE_NAMES)} Parquet tables: "
        f"{artifacts['catalog']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
