---
name: bioinformatics-project
description: Structure reproducible bioinformatics projects with a canonical layout, restartable drivers, pinned environments, provenance, and lab notebook. Use when starting or reorganizing a genomics project or making a sequencing analysis rerunnable.
metadata:
  short-description: Organize and reproducibly structure bioinformatics projects
---

# Bioinformatics Project Organization

Set up a computational-biology project so a stranger can understand what was done and why, and so every analysis can be rerun end-to-end from a script. Apply this when creating, restructuring, or reproducibility-hardening any genomics, metagenomics, sequencing, or computational-biology project. The omics stage skills (`omics-pipeline`) assume a project made this way.

Two assumptions drive every rule below (Noble 2009): a stranger must be able to reconstruct the analysis from the files alone, and everything will be rerun (with new data, new parameters, or a fixed bug), so build each experiment to re-execute from a script, never from memory.

## Instructions

### New project startup workflow

Turn the project into a small written contract before creating directories or running the first command:

1. Name the project with a durable, specific directory name.
2. Write the objective, analysis tracks, expected deliverables, input data types, compute environment, and known reference databases in `README.md`.
3. Create `tasks/METHODS.md` immediately and record every setup command, software version, database path, option, seed, and SLURM job ID as work proceeds. Create `SUMMARY.md` for current status and high-level counts, and `tasks/todo.md` for active work (records follow `session-records`).
4. Initialize dependency management before analysis: `pixi.toml` owns the project environment, Python libraries included; `uv run --script` runs self-contained helper scripts with inline (PEP 723) dependencies, such as `scripts/scaffold_project.py`.
5. Check existing shared database locations before downloading references. For a new reference, use a named database directory and document source URL, version, date, checksum, and command.
6. Put raw inputs and metadata in read-only data directories; never write cleaned, mapped, filtered, or derived outputs back into raw data.
7. Before exploratory analysis, create a hypothesis register with at least five biological, technical, null, sampling, and database explanations. Keep ruled-out hypotheses visible with the evidence that changed their status.
8. For each analysis stage, create a restartable driver script plus a README before launching compute, then update methods and summaries after the run.
9. Keep root-level directories intuitive from day one: raw data, generated batch outputs, publication figures, logs, and scratch files are not peers at the project root.

### Canonical project layout

Logical at the root, chronological at the experiment level, logical again inside each experiment (Noble 2009). Cleaned and generated files go in `results/`, never back into `data/` (Wilson 2017). For a simple single-track project, start here:

```
project_name/              # one self-contained, meaningfully named dir
├── data/                  # fixed inputs + metadata; treat as read-only
│   ├── raw/               # immutable original data (chmod 444); never edit in place
│   └── README.md          # provenance: source URL, version, download date, md5
├── results/               # all computed experiments (regenerable)
│   ├── lab_notebook.md    # dated, verbose decision log at the root of results/
│   └── 2024-03-12_binning/ # one dated run dir (YYYY-MM-DD[_topic])
│       ├── runall         # the driver script: reproduces this run alone
│       ├── README.md      # what/why for this run
│       └── qc/ assembly/ bins/  # one subdirectory per pipeline stage (generated)
├── src/                   # your own analysis code (importable, tested)
├── bin/                   # third-party / compiled tools, project wrappers
├── doc/                   # one subdir per manuscript + notes + changelog
├── tasks/                 # METHODS.md (committed); todo, hypotheses (local)
├── pixi.toml / pixi.lock  # bioinformatics tool stack and lock file (committed)
├── README.md  LICENSE  CITATION.cff
└── .gitignore             # excludes data blobs and all results/ outputs
```

This skill owns the results layout `results/<date>_<name>/<stage>/`: a run directory is dated (`YYYY-MM-DD`, optionally `_topic`, so runs sort in time order), and the pipeline stages (`qc/`, `assembly/`, `bins/`, ...) are subdirectories of it. Hand-written files (driver, README, workflow and config files) sit directly in the run directory; everything inside a stage subdirectory is generated. The one fixed shared path is `results/taxonomy/domain_routing.tsv`, written by the taxonomy stage. Never use names like `final/` or `binning_v2_really_final/`. Other skills and checklists point here instead of restating the layout. Full annotated tree, script categories, and the lab-notebook practice: [references/project-layout.md](references/project-layout.md). Worked example: [examples/project-tree.txt](examples/project-tree.txt).

For a repository with shared data plus several analyses or manuscripts, use the numbered root layout in [references/numbered-layout.md](references/numbered-layout.md). The same file explains how to migrate an already-messy project: build a path map first, never move large output directories in one step.

### Reproducibility rules

Harden every analysis against Sandve 2013's ten rules: record provenance, script all steps (no manual edits), pin and archive exact tool versions, version-control all custom code, persist standard-format intermediates per stage, fix and record random seeds, store the raw data behind every plot, emit hierarchical drill-down output, tie every claim to its result in a literate document, and, when sharing is in scope, provide public access (deposit reads, assemblies, derived tables; push the repo with its lockfile). Each rule has a how-to with concrete commands in [references/reproducibility-checklist.md](references/reproducibility-checklist.md).

### Driver-script discipline

Capture each experiment as one executable driver script, conventionally `runall`, so the whole analysis reproduces with one command (Noble 2009). Follow all six rules of thumb:

1. **Record every operation**: even `gunzip` and a one-off `seqkit stats` go in the script.
2. **Comment generously**: a reader understands the experiment from the comments alone.
3. **Never hand-edit intermediates**: transform with `sed`/`awk`/`grep`/`cut` so edits are recorded and repeatable.
4. **Store all file/dir names as variables at the top**: swapping a reference DB is a one-line change.
5. **Use relative paths** (`../../data/...`) from the experiment directory so the project runs after checkout elsewhere. Under Slurm, submit from the project root (`--chdir=PROJECT_ROOT`) and export the absolute `EXPERIMENT_DIR`; the spooled batch script's own path is not the experiment directory.
6. **Make it restartable**: guard each step with "skip if output exists"; write outputs to a temp name then `mv` to the final name so a partial result is never mistaken for a complete one.

Pass an explicit thread count to every tool; scheduler and login-node rules follow `hpc-slurm`. Pair `runall` with a `summarize` script (its final step) that produces a plot, table or HTML (style: `beautiful-data-viz`) and can interpret a partially completed experiment. Abort on error (`set -euo pipefail`, check return codes, message to stderr, non-zero exit) and give every script a usage statement (Noble 2009). Runnable, idempotent template with version capture, fixed seed, and temp-then-rename: [examples/runall.sh](examples/runall.sh).

### Environment pinning

- Pin the stack in `pixi.toml` and commit `pixi.lock`; capture a container (Docker / Apptainer) for long-lived or shared analyses (Sandve 2013). Version choice, locking and the database record follow `tool-versions`.
- Record exact versions into each experiment's provenance file at run time (`samtools --version`, `bwa 2>&1 | head`) and into `tasks/METHODS.md`.
- Make dependencies machine-readable and explicit (Wilson 2017); never rely on "whatever is on PATH".

Manifest example: [examples/environment.pixi.toml](examples/environment.pixi.toml). Guidance on pixi, uv, conda-file export, and containers: [references/environments.md](references/environments.md).

### Version control

- Track only hand-edited files: code, configs, `runall`, notebook, sample sheets, and `tasks/METHODS.md` as analysis provenance; the other `tasks/` notes stay local. Never commit generated outputs or binaries (`*.bam`, `*.bai`, `*.fastq.gz`, `results/**` tables); regenerate them via `runall`.
- Use a `.gitignore` that ignores the generated stage subdirectories of each run directory and `provenance.txt` (which `runall` regenerates), and tracks the hand-written files directly in the run directory (driver, README, `Snakefile`, `config.yaml`, `main.nf`, one-off scripts) and the lab notebook. Tested pattern: [examples/gitignore.example](examples/gitignore.example).
- Give each experiment its own dated `results/` directory and lab-notebook entry. Tag the commit behind each published figure or release; archive the release for a DOI (Zenodo) (Sandve 2013, Wilson 2017).

### Sharing and collaboration

Every project carries a `README.md` (study description, setup, how to reproduce), an explicit `LICENSE`, and a `CITATION.cff`; use tidy data (one variable per column, one observation per row) keyed by a stable unique ID (Wilson 2017). Detail: [references/good-enough-practices.md](references/good-enough-practices.md).

### Scaffold script

```bash
uv run --script ~/.agents/skills/bioinformatics-project/scripts/scaffold_project.py \
  ./coastal-metagenomes --name "Coastal metagenomes" \
  --objective "Recover and compare metagenome-assembled genomes."
```

| Need | Flags |
|---|---|
| Simple project | none (default canonical layout); resolve `pixi.lock`, then replace the hypothesis placeholders |
| Multi-track project | `--layout numbered` |
| First experiment | `--first-experiment YYYY-MM-DD_topic`: creates a README and a `runall` template that exits non-zero until adapted, without overwriting project-owned files |
| Publication metadata | `--license MIT --author "Name or organization" --copyright-year YYYY`; all three explicit values are required |
| Verify | `--check` (every scaffold file exists; edits to scaffolded files are allowed) |

The sample sheet `data/samples.tsv` (numbered layout: `00_data/01_metadata/samples.tsv`) starts with the required columns `sample_id`, `r1`, `r2` (leave `r2` empty for single-end or long reads); further columns are free metadata. Examples: [examples/samples.tsv](examples/samples.tsv), [examples/lab-notebook-entry.md](examples/lab-notebook-entry.md).

## Input Requirements

- A project objective and expected deliverables; input data types, source locations and sample metadata.
- The compute environment, including scheduler constraints; known reference databases and versions, or a plan to select them.
- Existing path consumers when reorganizing a project.

## Output

- A documented project layout with immutable raw inputs and regenerable outputs.
- `tasks/todo.md`, `tasks/METHODS.md`, and an exploratory hypothesis register.
- A `pixi.toml` with lower bounds and a committed `pixi.lock` that pins the exact builds.
- One restartable driver and README per analysis stage, with provenance, logs, and QC checks.
- README, license, citation metadata, and deposition-ready provenance where sharing is in scope.

## Quality Gates

- [ ] Every generated result maps to a version-controlled driver and recorded command.
- [ ] Raw inputs remain unchanged; derived data are written outside raw-data directories.
- [ ] Tool and database versions, parameters, checksums, seeds, and scheduler job IDs are recorded.
- [ ] Drivers fail on errors, write final outputs atomically, and resume without masking corrupt outputs.
- [ ] A fresh checkout plus documented external inputs reproduces the analysis.
- [ ] No secrets, credentials, large generated outputs, or private data are staged for Git.
- [ ] `scripts/scaffold_project.py <project> --objective "..." --check` passes, and a second identical scaffold run reports no created files.
- [ ] With `--first-experiment`, the ISO date is valid and the generated `runall` exits non-zero until adapted.
- [ ] Scaffolding never guesses a license or author; LICENSE and CITATION are generated only when license, author, and year are supplied together.

## Troubleshooting

**A resume guard skips a corrupt output:** Validate more than existence: nonzero size, parseability, expected record counts, checksums, or tool-specific completion markers. Rerun corrupt stages with an explicit force option.

**The environment cannot resolve:** Confirm channel order and platform support in `pixi.toml`. Record the failed solve, then constrain the conflicting package or use a pinned container for that stage.

**A scaffold file already contains different content:** The command exits before writing anything and lists the conflicting paths. Reconcile those files manually; the scaffold does not overwrite project-owned content.

**A first-experiment value is rejected:** Use a real ISO calendar date plus a lowercase topic, for example `2026-07-11_read-qc`. Slashes, `..`, uppercase topics, and impossible dates are rejected before the project directory is created.

## Sources

Noble WS 2009 (PLOS Comput Biol, doi:10.1371/journal.pcbi.1000424); Sandve GK et al. 2013 (PLOS Comput Biol, doi:10.1371/journal.pcbi.1003285); Wilson G et al. 2017 (PLOS Comput Biol, doi:10.1371/journal.pcbi.1005510).
