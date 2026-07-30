---
name: bioinformatics-project
description: Structure reproducible bioinformatics projects with canonical layouts, restartable drivers, pinned environments, provenance, and lab notebooks. Use when starting or reorganizing a genomics project or making a sequencing analysis rerunnable.
metadata:
  short-description: Organize and reproducibly structure bioinformatics projects
---

# Bioinformatics Project Organization

Set up a computational-biology project so a stranger can understand what was done and why, and so every analysis can be rerun end-to-end from a script. Apply this when creating, restructuring, or reproducibility-hardening any genomics, metagenomics, sequencing, or computational-biology project — and when running any single analysis command that should be reproducible.

Two assumptions drive every rule below (Noble 2009): a stranger must be able to reconstruct the analysis from the files alone, and everything will be rerun — with new data, new parameters, or a fixed bug — so build each experiment to re-execute from a script, never from memory.

## Instructions

### New project startup workflow

Before creating directories or running the first command, turn the project into
a small written contract:

1. Name the project with a durable, specific directory name.
2. Write the objective, analysis tracks, expected deliverables, input data
   types, compute environment, and known reference databases in `README.md`.
3. Create `tasks/METHODS.md` immediately and record every setup command, software
   version, database path, option, seed, and SLURM job ID as work proceeds.
4. Create `SUMMARY.md` for current status and high-level counts.
5. Create `tasks/todo.md` for active work and `tasks/lessons.md` for corrections
   and prevention rules. When memd is available, initialize its project scope and
   let `memd memory-md` maintain the root `memory.md`; do not hand-edit that file.
6. Initialize dependency management before analysis: use `pixi.toml` for
   bioinformatics stacks, `uv` only for Python-only projects, and never rely on
   system Python or ad hoc conda environments.
7. Check existing shared database locations before downloading references; if a
   new reference is needed, put it in a named database directory and document
   source URL, version, date, checksum, and command.
8. Put raw inputs and metadata in read-only data directories; never write
   cleaned, mapped, filtered, or derived outputs back into raw data.
9. Before exploratory analysis, create a hypothesis register with at least five
   biological, technical, null, sampling, and database explanations. Keep ruled-out
   hypotheses visible with the evidence that changed their status.
10. For each analysis stage, create a restartable driver script plus a README
   before launching compute, then update methods and summaries after the run.
11. Keep root-level directories intuitive from day one; do not let raw data,
    generated batch outputs, publication figures, logs, and scratch files become
    peers at the project root.

### Canonical project layout

Logical at the root, chronological at the experiment level, logical again inside each experiment (Noble 2009). Cleaned and generated files go in `results/`, never back into `data/` (Wilson 2017). For a simple single-track project, start here:

```
project_name/              # one self-contained, meaningfully named dir
├── data/                  # fixed inputs + metadata; treat as read-only
│   ├── raw/               # immutable original data (chmod 444); never edit in place
│   └── README.md          # provenance: source URL, version, download date, md5
├── results/               # all computed experiments (regenerable)
│   ├── lab_notebook.md    # dated, verbose decision log at the root of results/
│   └── 2024-03-12_binning/ # one dated experiment dir (YYYY-MM-DD[_topic])
│       ├── runall         # the driver script: reproduces this experiment alone
│       └── README.md      # what/why for this experiment
├── src/                   # your own analysis code (importable, tested)
├── bin/                   # third-party / compiled tools, project wrappers
├── doc/                   # one subdir per manuscript + notes + changelog
├── tasks/                 # todo, methods, lessons, and hypothesis register
├── pixi.toml / pixi.lock  # pinned bioinformatics tool stack (committed)
├── README.md  LICENSE  CITATION.cff
└── .gitignore             # excludes data blobs and all results/ outputs
```

Date every experiment dir `YYYY-MM-DD` (optionally `_topic`) so they sort in time order — never `final/` or `binning_v2_really_final/`. Full annotated tree, script categories, and the lab-notebook practice: `references/project-layout.md` (read when laying out or auditing a project). Concrete worked example: `examples/project-tree.txt`.

### Numbered layout for multi-track projects

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
|   |-- lessons.md
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

### Reproducibility rules (non-negotiable)

Harden every analysis against Sandve 2013's ten rules: record provenance, script all steps (no manual edits), pin and archive exact tool versions, version-control all custom code, persist standard-format intermediates per stage, fix and record random seeds, store the raw data behind every plot, emit hierarchical drill-down output, tie every claim to its result in a literate document, and provide public access (deposit reads, assemblies, derived tables; push the repo with its lockfile). Each rule has a bioinformatics how-to with concrete commands in `references/reproducibility-checklist.md` — read it when hardening an analysis for reproducibility.

### Driver-script discipline

Capture each experiment as one executable driver script, conventionally `runall`, so the whole analysis reproduces with one command (Noble 2009). Follow all six rules of thumb:

1. **Record every operation** — even `gunzip` and a one-off `seqkit stats` go in the script.
2. **Comment generously** — a reader understands the experiment from the comments alone.
3. **Never hand-edit intermediates** — transform with `sed`/`awk`/`grep`/`cut` so edits are recorded and repeatable.
4. **Store all file/dir names as variables at the top** — swapping a reference DB is a one-line change.
5. **Use relative paths** (`../../data/...`) so the project runs after checkout elsewhere.
6. **Make it restartable** — guard each step with "skip if output exists"; write outputs to a temp name then `mv` to the final name so a partial result is never mistaken for a complete one.

Pair `runall` with a `summarize` script (its final step) that produces a plot/table/HTML and can interpret a partially completed experiment. Abort on error (`set -euo pipefail`, check return codes, message to stderr, non-zero exit) and give every script a usage statement (Noble 2009). Runnable, idempotent template with version capture, fixed seed, and temp-then-rename: `examples/runall.sh` (copy and adapt when writing a pipeline).

### Environment pinning

House rule for this repo: bioinformatics tool stacks use **pixi** (conda-forge + bioconda); Python-only deps use **uv**; never use system Python or conda directly.

- Pin the stack in `pixi.toml` and commit `pixi.lock`; capture a container (Docker / Apptainer) for long-lived or shared analyses (Sandve 2013).
- Record exact versions into each experiment's provenance file at run time (`samtools --version`, `bwa 2>&1 | head`, `metabat2 2>&1 | head`) and into `tasks/METHODS.md`.
- Make dependencies machine-readable and explicit (Wilson 2017) — never rely on "whatever is on PATH".

Manifest example with lock-capture comment: `examples/environment.pixi.toml`. Full guidance on pixi, uv, conda export, and containers: `references/environments.md` (read when setting up or capturing an environment).

### Version control

- Put the project under Git for backup, history, and collaboration (Noble 2009); commit at least daily, keep changes small and focused (Wilson 2017).
- Track only hand-edited files — code, configs, `runall`, notebook, sample sheets. **Never** commit generated outputs or binaries (`*.bam`, `*.bai`, `*.fastq.gz`, `results/**` tables); regenerate them via `runall`.
- Use a `.gitignore` that ignores everything under `results/` (including `provenance.txt`, which `runall` regenerates) and allow-lists the hand-edited files that live there — the driver, its README, the lab notebook. Tested pattern: `examples/gitignore.example`.
- Branch for experimental work (`git checkout -b try-metabat2`); merge to main only when it works.
- Tag the commit behind each published figure or release; archive the release for a DOI (Zenodo) (Sandve 2013, Wilson 2017).

### Sharing & collaboration

Every project carries a `README.md` (study description, setup, how to reproduce), an explicit `LICENSE`, and a `CITATION.cff`; use tidy data (one variable per column, one observation per row) keyed by a stable unique ID (Wilson 2017). Detail: `references/good-enough-practices.md` (read for data management, software, collaboration, and manuscript practices).

## Quick Reference

| Need | Action |
|---|---|
| Start a simple project | Run `scripts/scaffold_project.py` with the default canonical layout, resolve `pixi.lock`, then replace the hypothesis placeholders. |
| Start a multi-track project | Add `--layout numbered`; use numbered, named roots for shared preprocessing, analyses, publication outputs, code, tests, logs, and scratch. |
| Add the first experiment | Add `--first-experiment YYYY-MM-DD_topic` to create a README and refusing `runall` template without overwriting project-owned files. |
| Add publication metadata | Opt in with `--license MIT --author "Name or organization" --copyright-year YYYY`; all three explicit values are required. |
| Repair a messy project | Inventory paths first, create the target scaffold, migrate with temporary compatibility links, and verify consumers before removing old paths. |
| Run an experiment | Copy `examples/runall.sh`, pin inputs and parameters, write atomically, and record versions and seeds. |
| Add structured metadata | Use `bio-foundation-housekeeping` as a separate follow-up only when schemas or a catalog are requested. |
| Prepare a release or deposition | Verify README, license, citation metadata, lockfiles, provenance, checksums, and regenerability. |

## Input Requirements

- A project objective and expected deliverables.
- Input data types, source locations, and available sample metadata.
- Target compute environment, including scheduler constraints when applicable.
- Known reference databases and their versions, or a plan to select and record them.
- Existing path consumers when reorganizing a project.

## Output

- A documented project layout with immutable raw inputs and regenerable outputs.
- `tasks/todo.md`, `tasks/METHODS.md`, `tasks/lessons.md`, and an exploratory hypothesis register.
- A pinned `pixi.toml` and `pixi.lock`, or a uv lock for a Python-only project.
- One restartable driver and README per analysis stage, with provenance, logs, and QC checks.
- README, license, citation metadata, and deposition-ready provenance where sharing is in scope.

## Quality Gates

- [ ] Every generated result maps to a version-controlled driver and recorded command.
- [ ] Raw inputs remain unchanged; derived data are written outside raw-data directories.
- [ ] Tool and database versions, parameters, checksums, seeds, and scheduler job IDs are recorded.
- [ ] Drivers fail on errors, write final outputs atomically, and resume without masking corrupt outputs.
- [ ] Exploratory work starts with at least five hypotheses and records a reflection after each major QC gate.
- [ ] A fresh checkout plus documented external inputs can reproduce the analysis.
- [ ] No secrets, credentials, large generated outputs, or private data are staged for Git.
- [ ] `scripts/scaffold_project.py <project> --objective "..." --check` passes, and a second identical scaffold run reports no created files.
- [ ] When `--first-experiment` is used, its ISO date is valid and the generated `runall` exits non-zero until adapted.
- [ ] Scaffolding never guesses a license or author; LICENSE/CITATION generation occurs only when license, author, and year are supplied together.

## Examples

Use the bundled templates instead of recreating them:

```bash
uv run --script ~/.agents/skills/bioinformatics-project/scripts/scaffold_project.py \
  ./coastal-metagenomes \
  --name "Coastal metagenomes" \
  --objective "Recover and compare metagenome-assembled genomes."

pixi install --manifest-path ./coastal-metagenomes/pixi.toml
uv run --script ~/.agents/skills/bioinformatics-project/scripts/scaffold_project.py \
  ./coastal-metagenomes \
  --name "Coastal metagenomes" \
  --objective "Recover and compare metagenome-assembled genomes." \
  --check
```

For a multi-track project with an initial experiment:

```bash
uv run --script ~/.agents/skills/bioinformatics-project/scripts/scaffold_project.py \
  ./coastal-metagenomes \
  --name "Coastal metagenomes" \
  --objective "Recover and compare metagenome-assembled genomes." \
  --layout numbered \
  --first-experiment 2026-07-11_read-qc
```

The bundled templates are annotated under "Example artifacts" below.

## Troubleshooting

**Existing paths are embedded in scripts or notebooks:** Inventory every consumer before moving data. Add temporary compatibility symlinks, update consumers, and remove the links only after end-to-end validation.

**A resume guard skips a corrupt output:** Validate more than existence. Check nonzero size, parseability, expected record counts, checksums, or tool-specific completion markers; rerun corrupt stages with an explicit force option.

**The environment cannot resolve:** Confirm channel order and platform support in `pixi.toml`. Record the failed solve, then constrain the conflicting package or use a pinned container for that stage.

**The repository needs schemas and a queryable catalog:** Use `bio-foundation-housekeeping` after this skill establishes the project structure.

**A scaffold file already contains different content:** The command exits before writing anything and lists the conflicting paths. Reconcile those files manually; the scaffold does not overwrite project-owned content.

**A first-experiment value is rejected:** Use a real ISO calendar date plus a lowercase topic, for example `2026-07-11_read-qc`. Slashes, `..`, uppercase topics, and impossible dates are rejected before the project directory is created.

## Reference files

Load progressively as the task narrows:

- `references/project-layout.md` — full annotated directory tree, dated `results/` dirs, lab-notebook practice, script categories (Noble 2009). Read when laying out or auditing structure.
- `references/reproducibility-checklist.md` — Sandve 2013's ten rules operationalized, each with a bioinformatics how-to. Read when making an analysis reproducible.
- `references/good-enough-practices.md` — Wilson 2017 data/software/collaboration/org/tracking/manuscript practices. Read for sharing, licensing, tidy data, deposition.
- `references/environments.md` — pinning and capturing environments with pixi, uv, conda, containers. Read when setting up or recording the software stack.

## Example artifacts

- `scripts/scaffold_project.py` — create or verify the minimal project scaffold without overwriting changed files.
- `examples/project-tree.txt` — concrete annotated tree for an arctic metagenome / MAG-recovery study.
- `examples/runall.sh` — runnable, restartable driver script (versions, seed, idempotency, temp-then-rename).
- `examples/lab-notebook-entry.md` — dated lab-notebook entry template.
- `examples/environment.pixi.toml` — pinned pixi manifest with lock-capture comment.
- `examples/gitignore.example` — `.gitignore` that tracks only hand-edited files (ignores `results/` outputs, allow-lists the driver/README/notebook).
- `examples/samples.tsv` — tidy sample sheet keyed by `sample_id` (one observation per row).

## Sources

Noble WS 2009 (PLOS Comput Biol, doi:10.1371/journal.pcbi.1000424); Sandve GK et al. 2013 (PLOS Comput Biol, doi:10.1371/journal.pcbi.1003285); Wilson G et al. 2017 (PLOS Comput Biol, doi:10.1371/journal.pcbi.1005510).
