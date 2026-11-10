# Numbered layout for multi-track projects

When one repository contains shared data plus multiple analyses, manuscripts,
or reusable preprocessing stages, prefer a numbered root layout. This keeps
shared inputs above project-specific tracks and prevents generated outputs from
accumulating at the root:

```
project_name/
|-- README.md
|-- SUMMARY.md
|-- pixi.toml
|-- pixi.lock
|-- tasks/
|   |-- METHODS.md
|   |-- todo.md
|   `-- hypotheses.md
|
|-- 00_data/
|   |-- 00_raw/
|   |-- 01_metadata/
|   `-- README.md
|-- 01_shared_preprocessing/
|   |-- 00_manifests/
|   |-- 01_mapping_or_qc/
|   `-- 02_project_duckdb/
|-- 02_analyses/
|   |-- 00_analysis-track-a/
|   |   |-- 00_stage-name/
|   |   |-- 01_stage-name/
|   |   `-- README.md
|   `-- 01_analysis-track-b/
|       |-- 00_stage-name/
|       |-- 01_stage-name/
|       `-- README.md
|-- 03_publication_outputs/
|   |-- 00_analysis-track-a/
|   `-- 01_analysis-track-b/
|-- 04_code/
|   |-- 00_shared/
|   |-- 01_analysis-track-a/
|   `-- 02_analysis-track-b/
|-- 05_tests/
|-- 90_logs/
`-- 99_scratch/
```

Use numbered directories for ordering, not as a substitute for names. Each
numbered directory still needs a short descriptive suffix. Put cross-track
inputs, sample manifests, read mappings, shared QC, and shared DuckDB databases
under `01_shared_preprocessing/`. Put project-specific batch outputs and final
tables under the appropriate `02_analyses/<track>/` stage. Put manuscript
drafts, final figures, reports, and review packets under
`03_publication_outputs/`. Put SLURM stdout/stderr and temporary failed-tool
work directories under `90_logs/` or `99_scratch/`, not beside final evidence.

For already-messy projects, do not one-shot move large output directories until
you have a path map. First inventory hard-coded paths, create the target
scaffold and README files, move data with temporary compatibility symlinks,
update scripts, then validate DuckDB builders, notebooks, and driver scripts
before removing old paths.
