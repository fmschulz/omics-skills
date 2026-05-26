---
name: bio-foundation-housekeeping
description: Initialize a bioinformatics project scaffold with reproducible environments, schemas, and data cataloging. Use for new projects or repo setup.
---

# Bio Foundation Housekeeping

Initialize a bioinformatics project scaffold with reproducible environments, schemas, and data cataloging. Use for new projects or repo setup.

## Instructions

1. Create standard directory layout (data/, results/, schemas/, workflows/, src/, notebooks/).
2. Initialize Pixi workspace and lockfile; define tasks.
3. Define LinkML schemas for sample, run, file, result, and provenance records.
4. Generate or hand-write Pydantic models from the LinkML schema and use them to parse/coerce incoming metadata before storage.
5. Validate raw records with LinkML/Pydantic, write normalized Parquet tables, then create the DuckDB catalog over validated Parquet only.

## Quick Reference

| Task | Action |
|------|--------|
| Run workflow | Follow the steps in this skill and capture outputs. |
| Validate inputs | Confirm required inputs and reference data exist. |
| Review outputs | Inspect reports and QC gates before proceeding. |
| Tool docs | See `docs/README.md`. |

## Input Requirements

Prerequisites:
- Tools available in the active environment (Pixi/conda/system). See `docs/README.md` for expected tools.
- Target project root is writable.
Inputs:
- project root (path)
- metadata schema requirements
- workflow engine preference (optional)

## Output

- pixi.toml
- pixi.lock
- schemas/
- data/catalog.duckdb
- data/*.parquet validated against schemas/
- results/bio-foundation-housekeeping/report.md
- results/bio-foundation-housekeeping/logs/

## Quality Gates

- [ ] Schema generation succeeds and models are importable.
- [ ] Raw metadata validates against LinkML and Pydantic before DuckDB ingestion.
- [ ] pixi.lock is created and consistent with pixi.toml.
- [ ] DuckDB catalog is readable and points at validated Parquet tables.
- [ ] On failure: retry with alternative parameters; if still failing, record in report and exit non-zero.
- [ ] Verify project root exists and is writable.
- [ ] Validate generated schemas against expected fields.

## Examples

### Example 1: Expected input layout

```text
project root (path)
metadata schema requirements
workflow engine preference (optional)
```

## Troubleshooting

**Issue**: Missing inputs or reference databases
**Solution**: Verify paths and permissions before running the workflow.

**Issue**: Low-quality results or failed QC gates
**Solution**: Review reports, adjust parameters, and re-run the affected step.
