# Nextflow on HPC (Slurm/PBS) playbook

Last verified: 2026-10-01
Tool version/release checked: Nextflow v26.04.6
Official docs/manual: https://www.nextflow.io/docs/latest/; https://www.nextflow.io/docs/latest/executor.html
Release/source: https://github.com/nextflow-io/nextflow/releases/tag/v26.04.6

## Why Nextflow for HPC bioinformatics
- Nextflow’s executor layer lets you keep pipeline logic independent of the execution platform (local vs Slurm vs PBS).
- Each process is executed as a scheduler job under HPC executors.
- Caching/resume is first-class (good for long, multi-step genomics pipelines).

## Minimal repository layout (DSL2)
- `main.nf`
- `nextflow.config`
- `modules/`
  - `fastqc.nf`
  - `align_bwa.nf`
- Optional: `conf/` for profile-specific configs

## Minimal skeleton (main.nf)
DSL2 is the only dialect, so `nextflow.enable.dsl = 2` is not needed. Nextflow v26.04+ parses scripts and configs with the strict syntax by default; check code with `nextflow lint`.

```nextflow
include { FASTQC } from './modules/fastqc'

workflow {
  reads_ch = channel.fromPath(params.reads)
  FASTQC(reads_ch)
}
```

## Minimal module example (modules/fastqc.nf)
```nextflow
process FASTQC {
  tag "$reads.baseName"

  input:
    path reads

  output:
    // FastQC strips .gz and .fastq/.fq itself; a glob avoids rebuilding its name rules.
    path "*_fastqc.zip"
    path "*_fastqc.html"

  script:
  """
  fastqc -t ${task.cpus} $reads
  """
}
```

## HPC config example (nextflow.config)
```groovy
params {
  reads  = null
  outdir = "results"
}

// Prefer setting workDir to fast scratch on HPC when possible
// workDir = "/scratch/$USER/nxf-work"

profiles {
  local {
    process.executor = 'local'
  }

  slurm {
    process.executor = 'slurm'
    process.queue    = 'compute'
    process.cpus     = 4
    process.memory   = '16 GB'
    process.time     = '2h'
    // process.clusterOptions = '--account=site-account'

    // Protect the scheduler / shared FS from too many tiny jobs
    // executor.queueSize       = 100
    // executor.submitRateLimit = '10 sec'
  }

  pbs {
    process.executor = 'pbs'
    process.queue    = 'workq'
    process.cpus     = 4
    process.memory   = '16 GB'
    process.time     = '2h'
  }
}
```

Run:
- Local: `nextflow run main.nf -profile local --reads 'data/*.fastq.gz'`
- Slurm:  `nextflow run main.nf -profile slurm --reads '/path/*.fastq.gz'`
- Resume: `nextflow run main.nf -profile slurm -resume --reads '/path/*.fastq.gz'`

For a scheduler-submitted launch job, use
`scripts/submit_nextflow.sh` from the project root. It requires `SLURM_ACCOUNT`,
submits the launch through `sbatch --chdir` set to the current directory,
enables trace/report/timeline artifacts, and rejects a run whose trace or
declared result directory is missing or empty. On multi-cluster sites, export
`SBATCH_CLUSTERS` (and `SBATCH_PARTITION`, `SBATCH_QOS`) first; `--parsable`
then prints `jobid;cluster`.

## Resuming and caching (agent guidance)
- Use `-resume` to reuse cached task results.
- Preserve the work directory and `.nextflow/` cache for resumability.
- Avoid nondeterministic inputs if you want reliable cache hits.
- Be deliberate about cleanup: aggressive cleanup trades off resumability/debuggability.

## Filesystem performance guidance (HPC)
- Put the **work directory** on fast scratch if available.
- Consider `scratch true` for processes that benefit from node-local execution, staging only final outputs.
- Avoid generating huge numbers of tiny intermediate files when possible (pipe/stream between tools).

## Pitfalls
- Too many tiny processes add scheduler overhead and filesystem pressure.
- Mis-specified resources get jobs killed by the scheduler; start conservative and tune from trace reports.
- Container policy mismatches (Docker blocked on HPC): plan for Apptainer/Singularity images.
