---
name: bio-foundation-housekeeping
description: Add LinkML/Pydantic metadata validation, Parquet tables, and a DuckDB catalog to a bioinformatics project. Use when records need schema checks or a queryable catalog.
disable-model-invocation: true
---

# Bio Foundation Housekeeping

Add validated metadata models and a queryable catalog to a project that `bioinformatics-project` already laid out. Without that layout, stop and run `bioinformatics-project` first; do not create a competing layout. Shared pipeline rules: read `~/.agents/skills/omics-pipeline/SKILL.md` first (in a plugin install, `../omics-pipeline/SKILL.md` from this file). Versions: [docs/README.md](docs/README.md).

## Instructions

1. Adapt `schemas/project-metadata.yaml` to the sample, run, file, result, and provenance records the project needs. Keep identifiers stable and declare types, required fields, enumerations, and patterns in the schema.
2. Generate the Pydantic models. The command pins LinkML and Pydantic, rejects changed outputs, imports the generated module, and can assert that expected classes exist. Run it with `--check` in CI:

   ```bash
   SKILL_ROOT=~/.agents/skills/bio-foundation-housekeeping
   uv run --script "$SKILL_ROOT/scripts/generate_models.py" \
     --schema "$SKILL_ROOT/schemas/project-metadata.yaml" \
     --output ./schemas/generated/project_metadata.py \
     --expect-class MetadataBundle
   ```

3. Build the linked metadata catalog. The driver generates and imports the model in a temporary directory, validates the whole bundle with `MetadataBundle` (unexpected fields and malformed types are rejected first), then checks unique identifiers and foreign keys (run-to-sample, file-to-run, result-to-input/output-file, provenance-to-result). Only then does it write one Parquet table per record class plus bridge tables for multivalued relationships, and register their relative paths, row counts, and SHA-256 values in DuckDB:

   ```bash
   SKILL_ROOT=~/.agents/skills/bio-foundation-housekeeping
   uv run --script "$SKILL_ROOT/scripts/build_metadata_catalog.py" \
     --schema "$SKILL_ROOT/schemas/project-metadata.yaml" \
     --input "$SKILL_ROOT/fixtures/valid-project-metadata.json" \
     --project-root .
   ```

   Adapt the schema and the fixtures together for project-specific records. `scripts/build_sample_catalog.py` (with `fixtures/valid-samples.jsonl`) is the smaller sample-only smoke path.
4. Before you adopt a project-specific extension or migrate stored records, run `scripts/check_schema_compatibility.py`. Optional slots and new classes are compatible; required additions and constraint changes are reported as breaking. Keep a versioned input/expected migration fixture like `fixtures/schema-migration-v1-to-v1.1.json` for every supported transition.

A killed run can leave some generated targets but no catalog. `data/catalog.duckdb` is the completion marker. Compare the remaining targets with the run log and remove only artifacts of the interrupted run after you confirm they are not project-owned; the next run refuses partial targets.

## Input Requirements

- A project root organized by `bioinformatics-project`, writable.
- Metadata records, plus the valid, model-invalid, duplicate-ID, and broken-foreign-key fixtures that exercise the boundary.

## Output

- schemas/project-metadata.yaml
- schemas/generated/project_metadata.py
- data/catalog.duckdb
- data/normalized/{samples,runs,files,results,result_inputs,provenance}.parquet
- results/bio-foundation-housekeeping/report.md (status, schema and Parquet SHA-256 values, row counts, and LinkML, Pydantic, and DuckDB versions)
- results/bio-foundation-housekeeping/rejections.json (failed runs only: field locations and error classes, never rejected values)
- results/bio-foundation-housekeeping/logs/

## Quality Gates

- [ ] The generated module imports, `--expect-class` finds every expected class, and the source contains no build-machine absolute paths.
- [ ] Duplicate identifiers and broken foreign keys fail before any artifact is published; invalid fixtures exit non-zero without publishing schema, model, Parquet, or DuckDB artifacts.
- [ ] The valid fixture produces six verified Parquet tables and a readable DuckDB catalog that points at them.
- [ ] Project-specific schema extensions have a compatibility report, and each supported schema-version transition has an input/expected migration fixture.
