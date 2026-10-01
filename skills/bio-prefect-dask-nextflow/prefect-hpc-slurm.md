# Prefect on HPC (Slurm): two common patterns

Last verified: 2026-10-01
Tool version/release checked: Prefect 3.8.7; Dask/distributed 2026.8.0; prefect-dask 0.3.7 (maintained in the Prefect repository under `src/integrations/prefect-dask`; install through `prefect[dask]`)
Official docs/manual: https://docs.prefect.io/v3/concepts/work-pools; https://docs.prefect.io/integrations/prefect-dask; https://jobqueue.dask.org/
Release/source: https://github.com/PrefectHQ/prefect/releases/tag/3.8.7; https://github.com/dask/dask/releases/tag/2026.8.0; https://github.com/PrefectHQ/prefect/tree/main/src/integrations/prefect-dask

## Pattern A: Prefect → Slurm worker (one Slurm job per flow run)
Best when:
- Each flow run is a substantial HPC workload.
- You want Slurm to enforce quotas/policies.
- Prefect is used for orchestration, metadata, retries, UI.

### Conceptual steps
1. Install `prefect-slurm` (community package from EBI-Metagenomics, v0.1.7 on PyPI as of 2026-10-01; not maintained by Prefect).
2. Create a Slurm work pool (`--type slurm`).
3. Configure Slurm REST API (`slurmrestd`) access and JWT token handling.
4. Start a Slurm worker bound to that work pool.

Tasks inside a flow run share the flow run's Slurm job; `prefect-slurm` does not submit one job per task.

### Operational notes
- Ensure flow-run jobs can reach the Prefect API endpoint (Cloud or self-hosted).
- Decide where outputs live (shared filesystem vs object store).
- Activate the project's pinned environment (pixi or uv) in the job script before running the flow; do not rely on whatever is on `PATH`.

### Pitfalls
- Requires Slurm REST API enabled and reachable.
- Token/credentials management can be a stumbling block.
- If compute nodes have restricted networking, Prefect API reachability can fail.

## Pattern B: Prefect + Dask-jobqueue on Slurm (Dask spins up worker jobs)
Best when:
- You need distributed Python across multiple nodes for in-memory or partitioned compute.
- You can tolerate more moving parts and debug complexity.

### Template
Install the extra dependency first: `uv add "prefect[dask]" dask-jobqueue`.

```python
from prefect import flow, task
from prefect_dask import DaskTaskRunner

@task
def heavy_step(x: int) -> int:
    return x * x

@flow(
    task_runner=DaskTaskRunner(
        cluster_class="dask_jobqueue.SLURMCluster",
        cluster_kwargs={
            "cores": 8,
            "processes": 1,
            "memory": "32GB",
            "walltime": "02:00:00",
            "queue": "compute",  # the site's partition
            # "account": "site-account",  # always set the site's account
            # "job_extra_directives": [...],
        },
        adapt_kwargs={"minimum": 0, "maximum": 10},
    )
)
def hpc_flow(items: list[int]) -> list[int]:
    futures = [heavy_step.submit(x) for x in items]
    return [f.result() for f in futures]
```

`DaskTaskRunner` constructs this cluster when the flow starts and closes the
client and temporary cluster when the flow run ends. Do not call a cluster
factory while Python evaluates the `@flow` decorator; that submits workers at
import time and leaves ownership unclear after failures.

### Pitfalls (double scheduling)
You may end up with:
- Prefect schedules the flow run
- Dask schedules tasks
- Slurm schedules Dask workers

It can be correct, but increases startup latency and debugging complexity.

## Recommendation for CLI-heavy bioinformatics on HPC
If most steps are external CLI tools (bwa, samtools, gatk), prefer Nextflow for the compute plane.
See: [nextflow-hpc.md](nextflow-hpc.md)
