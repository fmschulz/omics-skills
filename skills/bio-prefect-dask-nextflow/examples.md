# Examples (Prefect-only, Nextflow-only, Hybrid)

Last verified: 2026-05-30
Tool version/release checked: Prefect 3.7.2; Dask/distributed 2026.3.0; prefect-dask package release v0.2.6 (archived repository; install through `prefect[dask]`); Nextflow v26.04.3
Official docs/manual: https://docs.prefect.io/latest/ ; https://docs.dask.org/en/stable/ ; https://www.nextflow.io/docs/latest/
Release/source: https://github.com/PrefectHQ/prefect/releases/tag/3.7.2 ; https://github.com/dask/dask/releases/tag/2026.3.0 ; https://github.com/nextflow-io/nextflow/releases/tag/v26.04.3

## Example 1: Prefect + Dask local QC
Use when:
- You’re iterating quickly on a workstation.
- Steps are Python-heavy or need dynamic branching.

Blueprint:
- A Prefect flow maps over samples and runs tasks via `.submit()`.
- DaskTaskRunner runs tasks in parallel on a LocalCluster.
- Outputs written to `results/` with deterministic paths.

## Example 2: Nextflow on Slurm for alignment
Use when:
- You’re executing a classic file-based genomics pipeline on HPC.

Blueprint processes:
- FASTQC → ALIGN (bwa mem) → SORT/INDEX (samtools) → METRICS
- Profiles: `local`, `slurm`, `pbs`
- Run with `-resume` to recover from partial failures.

## Example 3: Hybrid: Prefect orchestrates batches, Nextflow executes compute
Pattern:
- Prefect flow:
  1. Ingest new samples (LIMS/DB/S3)
  2. Validate inputs + stage to shared/scratch
  3. Batch samples (e.g., 50 samples/run)
  4. Submit a Nextflow run per batch (via CLI or as a scheduler job)
  5. Parse Nextflow reports (trace/timeline) and publish artifacts/metrics
  6. Notify on failure; optionally require approval for reruns

Watch-outs:
- Don’t double-retry (Prefect retries + Nextflow retries) without a clear policy.
- Standardize work/results paths so Prefect can locate outputs reliably.
