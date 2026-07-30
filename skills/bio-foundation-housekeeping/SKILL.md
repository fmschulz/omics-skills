---
name: bio-foundation-housekeeping
description: Add schema-backed metadata validation, normalized Parquet tables, and a DuckDB catalog to a bioinformatics project. Use when an analysis needs LinkML/Pydantic records or a queryable data catalog.
---

# Bio Foundation Housekeeping

Add validated metadata models and a queryable catalog to an existing bioinformatics project. This is an independent entry point when the layout already exists; if it does not, complete `bioinformatics-project` as a separate setup task.

## Instructions

1. Confirm `bioinformatics-project` has established input/output boundaries, project records, and a pinned environment. Do not create a competing project layout.
2. Adapt `schemas/project-metadata.yaml` for the sample, run, file, result, and provenance records the project needs. Keep identifiers stable and declare types, required fields, enumerations, and patterns in the schema.
3. Generate Pydantic models with `scripts/generate_models.py`. The command pins LinkML and Pydantic, rejects changed outputs, imports the generated module, and can assert that expected classes exist.
4. Validate the complete metadata bundle with the generated `MetadataBundle` model. Reject unexpected fields and malformed types before checking relationships.
5. Check unique identifiers and foreign keys across record collections before writing outputs. At minimum, verify run-to-sample, file-to-run, result-to-input/output-file, and provenance-to-result links.
6. Normalize validated records into one Parquet table per record class plus bridge tables for multivalued relationships. Register the tables and their relative paths, row counts, and SHA-256 values in DuckDB.
7. Exercise the full boundary with `scripts/build_metadata_catalog.py` and the bundled valid, model-invalid, and foreign-key-invalid fixtures. Use `scripts/build_sample_catalog.py` only for the smaller sample-only smoke path.
8. Before adopting a project-specific extension or migrating stored records, run `scripts/check_schema_compatibility.py`. Optional slots and new classes are compatible; required additions and constraint changes are reported as breaking. Keep a versioned input/expected migration fixture like `fixtures/schema-migration-v1-to-v1.1.json` for every supported transition.

## Quick Reference

| Task | Action |
|------|--------|
| Project structure is missing | Stop catalog work and run `bioinformatics-project` as a separate setup task. |
| Define records | Adapt `schemas/project-metadata.yaml` without changing identifier semantics silently. |
| Generate models | Run `scripts/generate_models.py` through `uv run --script`. |
| Normalize linked metadata | Run `scripts/build_metadata_catalog.py` with the schema and a JSON bundle. |
| Sample-only smoke test | Run `scripts/build_sample_catalog.py` with the JSONL fixtures. |
| Build catalog | Register validated Parquet only, then verify counts, hashes, and foreign keys. |
| Check an extension | Run `check_schema_compatibility.py` and review its machine-readable report before regenerating models. |
| Tool docs | See `docs/README.md`. |

## Input Requirements

Prerequisites:
- Tools declared in the project's pinned Pixi environment. See `docs/README.md` for expected tools.
- Target project root is writable.
Inputs:
- A project root already organized by `bioinformatics-project`.
- Representative valid, model-invalid, duplicate-ID, and broken-foreign-key metadata records.
- Required identifiers, fields, types, enumerations, and cross-record constraints.

## Output

- schemas/project-metadata.yaml
- schemas/generated/project_metadata.py
- data/catalog.duckdb
- data/normalized/{samples,runs,files,results,result_inputs,provenance}.parquet
- results/bio-foundation-housekeeping/report.md
- results/bio-foundation-housekeeping/logs/

## Quality Gates

- [ ] Schema generation succeeds and models are importable.
- [ ] Generated model source contains no build-machine absolute paths.
- [ ] Raw metadata validates against LinkML and Pydantic before DuckDB ingestion.
- [ ] Duplicate identifiers and broken foreign keys fail before artifact publication.
- [ ] The run manifest records exact schema/catalog dependency versions.
- [ ] DuckDB catalog is readable and points at validated Parquet tables.
- [ ] Invalid fixtures fail before Parquet or DuckDB ingestion.
- [ ] On failure: record the field location and validation error without copying rejected values, then exit non-zero.
- [ ] Verify project root exists and is writable.
- [ ] Validate generated schemas against expected fields.
- [ ] The valid fixture produces six verified Parquet tables and a non-empty DuckDB catalog; invalid fixtures exit non-zero without publishing schema, model, Parquet, or DuckDB artifacts.
- [ ] Project-specific schema extensions have a compatibility report, and each supported schema-version transition has an input/expected migration fixture.

## Examples

### Example 1: Generate and check Pydantic models

```bash
SKILL_ROOT=~/.agents/skills/bio-foundation-housekeeping

uv run --script "$SKILL_ROOT/scripts/generate_models.py" \
  --schema "$SKILL_ROOT/schemas/project-metadata.yaml" \
  --output ./coastal-metagenomes/schemas/generated/project_metadata.py \
  --expect-class MetadataBundle
```

Run the same command with `--check` in CI. The generator exits non-zero if the output is missing or differs from the schema-derived model.

### Example 2: Build the linked metadata catalog

```bash
uv run --script "$SKILL_ROOT/scripts/build_metadata_catalog.py" \
  --schema "$SKILL_ROOT/schemas/project-metadata.yaml" \
  --input "$SKILL_ROOT/fixtures/valid-project-metadata.json" \
  --project-root ./coastal-metagenomes
```

The bundled driver generates and imports the model in a temporary directory, validates every field and cross-record relationship, then publishes schema, model, Parquet, and DuckDB artifacts. Adapt the schema and fixtures together for project-specific records.

### Example 3: Exercise the sample-only boundary

```bash
SKILL_ROOT=~/.agents/skills/bio-foundation-housekeeping

uv run --script "$SKILL_ROOT/scripts/build_sample_catalog.py" \
  --input "$SKILL_ROOT/fixtures/valid-samples.jsonl" \
  --project-root ./coastal-metagenomes
```

The bundled invalid fixtures demonstrate that malformed types, unexpected keys, duplicate identifiers, and missing foreign keys fail before ingestion. Rejection reports record locations and error classes, not rejected values.

## Troubleshooting

**Issue**: Missing inputs or reference databases
**Solution**: Verify paths and permissions before running the workflow.

**Issue**: A Pydantic field validator cannot see another field
**Solution**: Pydantic validates fields in declaration order. Declare the dependency first or move the cross-field rule to `@model_validator(mode="after")`.

**Issue**: A constructed model is accepted without validation
**Solution**: Do not use `model_construct()` for external input. Parse raw records with `model_validate()`, or configure `revalidate_instances="always"` when existing model instances must be checked again.

**Issue**: LinkML generation passes but the bundle has missing references
**Solution**: Schema validation checks record shape, while foreign keys span collections. Run the cross-record checks before creating output directories or opening DuckDB.

**Issue**: A generated model already exists and differs from the schema
**Solution**: Review the schema and model diff. Remove or relocate the generated file only after confirming it is disposable; the generator does not overwrite changed files.

**Issue**: A killed process leaves some generated targets but no catalog
**Solution**: Treat `data/catalog.duckdb` as the completion marker. Compare the remaining target paths with the run log and remove only artifacts from the interrupted run after confirming they are not project-owned; the next run refuses partial targets instead of guessing.
