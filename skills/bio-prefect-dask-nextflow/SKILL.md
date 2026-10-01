---
name: bio-prefect-dask-nextflow
description: Choose and scaffold Prefect+Dask or Nextflow pipelines. Use when designing a local, distributed, or Slurm-backed bioinformatics workflow.
---

# Bio Prefect + Dask + Nextflow

Choose a workflow engine for a local, distributed, or HPC bioinformatics pipeline and scaffold it.

Supplementary docs last verified: 2026-10-01 against Prefect 3.8.7, prefect-dask 0.3.7 (maintained in the Prefect repository; install with `prefect[dask]`), Dask/distributed 2026.8.0, and Nextflow v26.04.6.

## Instructions

1. Collect requirements: scheduler, container policy, data location, scale, and whether steps are CLI tools or Python functions.
2. Choose the engine with [decision-matrix.md](decision-matrix.md): Nextflow for file-based CLI tools on a scheduler, Prefect+Dask for Python-heavy or dynamic work, or a hybrid with Prefect as the control plane and Nextflow as the compute plane.
3. Generate a runnable scaffold with a clear data layout, per-step resources, and explicit thread counts (`task.cpus` in Nextflow, `threads_per_worker` in Dask).
4. Pin the software: pixi for tool stacks or Apptainer images on HPC, uv for Python (`uv add "prefect[dask]"`). Nextflow v26.04+ parses scripts and configs with the strict syntax by default; write code that passes `nextflow lint`.
5. Run heavy work through the scheduler, never on a login node. Submit the Nextflow launcher with `scripts/submit_nextflow.sh`; it runs from the current directory, so call it from the project root.
6. Validate with a small test dataset, then check resume (`-resume`, or Prefect retries plus idempotent outputs) before scaling.

## Quick Reference

| Task | Action |
|------|--------|
| Engine choice | [decision-matrix.md](decision-matrix.md) |
| Prefect+Dask scaffold | [prefect-dask.md](prefect-dask.md) |
| Prefect on Slurm | [prefect-hpc-slurm.md](prefect-hpc-slurm.md) |
| Nextflow on HPC | [nextflow-hpc.md](nextflow-hpc.md) |
| Submit Nextflow through Slurm | `SLURM_ACCOUNT=... scripts/submit_nextflow.sh main.nf 'data/*.fastq.gz' results` |
| Multi-cluster sites | Export `SBATCH_CLUSTERS`, `SBATCH_PARTITION`, and `SBATCH_QOS` before the wrapper; `--parsable` then prints `jobid;cluster`, so strip the suffix and pass the cluster to `squeue -M` and `sacct -M` |
| Examples | [examples.md](examples.md) |

## Input Requirements

- Workflow requirements and steps
- Target environment (local, cluster, cloud)
- Scheduler, account, partition, and container constraints
- Data locations and expected volumes

## Output

- Engine recommendation with rationale
- Runnable scaffold (files and commands)
- Resource plan per step (CPUs, memory, walltime)
- Validation plan and checkpoints

## Quality Gates

- [ ] A tiny test run completes end-to-end through the same launcher used for production.
- [ ] Resume and retry behavior is verified; Prefect and Nextflow retries are not stacked without a stated policy.
- [ ] The resource plan matches the cluster's limits, and every tool receives an explicit thread count.
- [ ] Temporary Dask clusters are created by the task runner at flow runtime and closed with the flow.
- [ ] Compound FASTQ suffixes (`.fastq.gz`) do not leak into sample output names.
- [ ] The Nextflow launch runs through `sbatch` and verifies the trace file and non-empty result artifacts.

## Examples

### Example 1: Engine recommendation

```text
Choice: Nextflow
Why: CLI-heavy pipeline, HPC scheduler required, reproducible cache/resume needed.
```

## Troubleshooting

**Issue**: Workflow fails on HPC because of an environment mismatch
**Solution**: Pin the tool stack (pixi lockfile or Apptainer image) and validate with a minimal test dataset on a compute node.

**Issue**: Nextflow v26.04+ rejects a script or config that ran on an older version
**Solution**: The strict parser is now the default. Fix the reported pattern (see the Nextflow strict-syntax migration guide), or set `NXF_SYNTAX_PARSER=v1` as a temporary workaround and record it.
