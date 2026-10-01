# Evidence checklist (what to collect)

On an HPC login node, collect evidence only. Rerun or capture workflows through the scheduler (`sbatch`) with explicit thread limits. On Dori, submit with `-M perceus-00 -A grp-org-sc-mgs -p dori --qos=jgi_normal` and never to Lawrencium.

## Minimum viable evidence (any workflow system)
- Pipeline repository URL + **commit SHA** (or release tag)
- Exact launch command (copy/paste)
- All config/params files used (e.g., `nextflow.config`, `params.json`, `config.yaml`)
- Workflow engine version (e.g., `nextflow -version`, `snakemake --version`, `cwltool --version`)
- A machine-readable list of **software tools + versions** (one of):
  - pipeline-emitted versions file (preferred)
  - environment lockfile the run actually used (`pixi.lock`, `uv.lock`, or the per-rule conda environment files and their exports)
  - container image names + digests (`docker inspect`, `apptainer inspect`)
- Input dataset identifiers + checksums (or accessions + release dates)
- Reference assets versions (genome build, annotation release, db versions)
- QC reports + thresholds used
- Output directory layout (or a file manifest)

## Nextflow (recommended evidence)
Collect:
- `trace.txt` (or custom name) from `-with-trace`
- `report.html` from `-with-report`
- `timeline.html` from `-with-timeline`
- DAG image from `-with-dag`
- `.nextflow.log`
- `work/` directory *or* at least the task folders referenced in trace/log

How to capture next time (example):
```bash
nextflow run <pipeline> \
  -with-report report.html \
  -with-trace trace.txt \
  -with-timeline timeline.html \
  -with-dag flowchart.png
```

## Snakemake (recommended evidence)
Collect:
- `report.html` from `--report`
- `.snakemake/log/*` (scheduler + job logs)
- workflow files: `Snakefile`, `config.yaml`, profiles
- If you need exact commands, run with `--printshellcmds` and capture stdout/stderr.

How to capture next time (example; `--report` alone only builds a report from a finished run, so add `--report-after-run` to run and report in one call, and keep the workflow's own `--software-deployment-method` such as `conda` or `apptainer`):
```bash
snakemake --cores 16 --printshellcmds --report report.html --report-after-run
```

## CWL / cwltool (recommended evidence)
Collect:
- Provenance Research Object folder produced by CWLProv (PROV traces + packed inputs/outputs)
- Workflow + tool definition files (`*.cwl`)
- Inputs object (`inputs.yml` / `inputs.json`)

How to capture next time (example):
```bash
cwltool --provenance provenance_ro/ workflow.cwl inputs.yml
```

