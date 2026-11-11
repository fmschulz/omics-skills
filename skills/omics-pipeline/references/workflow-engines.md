# Workflow engines: Prefect with Dask, or Nextflow

**Last verified:** 2026-10-01 (the date the source guides were checked; this condensed page was not re-verified on 2026-11-09)
**Tool version/release checked:** Prefect 3.8.7; Dask/distributed 2026.8.0; prefect-dask 0.3.7; Nextflow v26.04.6 (versions from the source guides, not re-checked)
**Official docs/manual:** https://docs.prefect.io/latest/ ; https://docs.dask.org/en/stable/ ; https://www.nextflow.io/docs/latest/
**Release/source:** https://github.com/PrefectHQ/prefect/releases/tag/3.8.7 ; https://github.com/dask/dask/releases/tag/2026.8.0 ; https://github.com/nextflow-io/nextflow/releases/tag/v26.04.6

Check a version-specific detail against the upstream documentation before you rely on it.

Read this when a pipeline must run as a repeatable workflow on a workstation, a cluster, or both. Scheduler flags and accounts come from the `hpc-slurm` skill.

## Choose the engine

| The step is mostly... | Engine |
| --- | --- |
| A CLI tool that reads and writes files (FASTQ, BAM, FASTA), run on Slurm, PBS or LSF | Nextflow |
| A Python function (transforms, API calls, ML, metadata) or control flow that depends on results | Prefect with Dask |
| Both: Python decides what runs, tools do the heavy work | Hybrid: Prefect as control plane (batching, approvals, notifications), Nextflow as compute plane |

Rule of thumb: "run a tool over files" is a Nextflow process; "Python decides what to do next" is a Prefect task.

Nextflow gives scheduler-native jobs, `-resume` caching, per-process resources and portable profiles. It costs a DSL learning curve, and thousands of tiny processes overload the scheduler and shared filesystems.

Prefect with Dask gives Python-native code, retries, state tracking and easy local parallelism. It costs overhead for many tiny tasks, trouble with non-picklable objects, and port and network setup for Dask and the Prefect API on HPC.

## Anti-patterns

- Nextflow for steps that pass large in-memory Python objects.
- Prefect with Dask to drive thousands of short scheduler jobs. A scheduler-native engine is simpler.
- Double scheduling without intent (Prefect schedules the run, Dask schedules tasks, Slurm schedules the Dask workers). It adds start-up latency and debugging work.
- Stacked retries. Use Prefect or Nextflow retries, not both, unless you state the policy.

## Rules for either engine

- Collect the scheduler, container policy, data location, scale, and whether steps are CLI tools or Python functions before you choose.
- Give every tool an explicit thread count (`task.cpus` in Nextflow, `threads_per_worker` in Dask) and a resource plan per step.
- Pin the stack: a pixi lockfile or an Apptainer image for tools (Docker is often blocked on HPC), uv for Python. Write Nextflow code that passes `nextflow lint`; recent Nextflow versions parse with strict syntax.
- Prefect on Dask: create the Dask cluster in the task runner (`cluster_class="dask_jobqueue.SLURMCluster"`) so it starts at flow runtime and closes with the flow. Do not build a cluster at import time.
- Strip compound FASTQ suffixes (`.fastq.gz`, `.fq.gz`, `.fastq`, `.fq`) explicitly before you derive sample names. `Path.stem` leaves `.fastq` in the name.
- Put the Nextflow work directory on fast scratch, and keep it and `.nextflow/` between runs so `-resume` hits the cache.
- Test on a small dataset through the same launcher as production. Check resume and retry before you scale up, then verify the Nextflow trace file and non-empty result files.

## Submit Nextflow through Slurm

`~/.agents/skills/omics-pipeline/scripts/submit_nextflow.sh main.nf 'data/*.fastq.gz' results` submits a launcher job (2 CPUs, 8 GB, 24 h) that runs `nextflow run -profile slurm -resume` with trace, report and timeline in `results/run-metadata/`, and fails on an empty trace or empty results.
The caller passes `SLURM_ACCOUNT` (required) and any `SBATCH_PARTITION`, `SBATCH_QOS` and `SBATCH_CLUSTERS`; the wrapper uses `--chdir` to the project root (`PROJECT_ROOT`, default `$PWD`). On a multi-cluster site `--parsable` prints `jobid;cluster`: strip the suffix and pass the cluster to `squeue -M` and `sacct -M`.
