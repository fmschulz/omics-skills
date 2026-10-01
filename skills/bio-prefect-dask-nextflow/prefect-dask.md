# Prefect + Dask playbook (local-first, scalable to clusters)

Last verified: 2026-10-01
Tool version/release checked: Prefect 3.8.7; Dask/distributed 2026.8.0; prefect-dask 0.3.7 (maintained in the Prefect repository under `src/integrations/prefect-dask`; install through `prefect[dask]`)
Official docs/manual: https://docs.prefect.io/integrations/prefect-dask; https://docs.dask.org/en/stable/; https://distributed.dask.org/en/stable/
Release/source: https://github.com/PrefectHQ/prefect/releases/tag/3.8.7; https://github.com/dask/dask/releases/tag/2026.8.0; https://github.com/PrefectHQ/prefect/tree/main/src/integrations/prefect-dask

## What this gives you
- Prefect handles orchestration (retries, states, schedules, artifacts).
- Dask handles parallel execution of Prefect tasks (local or distributed).

## Install
Add the official extra to the project's uv environment:
- `uv add "prefect[dask]"`

## Local setup (optional)
1. Start a local Prefect server/UI:
   - `prefect server start`
2. Run flows locally during development (you can still run without the UI).

## Key rules (agent should enforce)
- **Concurrency requires `.submit()` or `.map()`**. Direct task calls run sequentially.
- `DaskTaskRunner` starts worker processes, so guard the flow call with
  `if __name__ == "__main__":`.
- Without `address`, `DaskTaskRunner` creates a temporary local cluster for the flow run and closes it afterwards. Set `n_workers` and `threads_per_worker` explicitly so the run stays inside its CPU allocation.

## Minimal template: sample-parallel QC
```python
from __future__ import annotations

from pathlib import Path
import subprocess

from prefect import flow, task
from prefect_dask import DaskTaskRunner

def sample_name(path: Path) -> str:
    name = path.name
    for suffix in (".fastq.gz", ".fq.gz", ".fastq", ".fq"):
        if name.endswith(suffix):
            return name[:-len(suffix)]
    return path.stem

@task(retries=2, retry_delay_seconds=30)
def fastqc(reads: Path, outdir: Path) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    sample_out = outdir / sample_name(reads)
    sample_out.mkdir(exist_ok=True)

    cmd = ["fastqc", "--threads", "1", "-o", str(sample_out), str(reads)]
    subprocess.run(cmd, check=True)

    # Return a deterministic artifact path
    return sample_out

@flow(
    name="qc-fastq",
    task_runner=DaskTaskRunner(
        cluster_kwargs={"n_workers": 4, "threads_per_worker": 1}
    ),
)
def qc_flow(reads_glob: str, outdir: str = "results/qc") -> list[str]:
    reads = list(Path(".").glob(reads_glob))
    futures = [fastqc.submit(r, Path(outdir)) for r in reads]
    results = [f.result() for f in futures]
    return [str(p) for p in results]

if __name__ == "__main__":
    qc_flow("data/*.fastq.gz")
```

## Connecting to an existing Dask cluster
If a Dask scheduler is already running (local or remote):

```python
from prefect import flow
from prefect_dask import DaskTaskRunner

@flow(task_runner=DaskTaskRunner(address="tcp://scheduler-host:8786"))
def my_flow():
    ...
```

## Tuning guidance
- Prefer **coarse-ish task granularity** (1 task per sample or per chunk), not 10k tiny tasks.
- Pass **paths/URIs**, not huge objects.
- Make tasks idempotent: write outputs to deterministic locations and check for existence.

## When NOT to use DaskTaskRunner
- Work is mostly many small CLI calls on HPC; Nextflow is usually a better fit.
- Tasks depend on non-picklable state (open DB connections, open file handles, GPU contexts) that is not recreated inside the task.
