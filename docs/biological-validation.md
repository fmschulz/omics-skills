# Biological Validation Reference

The biological validation program qualifies eight core omics skills against versioned truth sets and records scheduler evidence separately from scientific scores.

## Evidence levels

| Level | Required evidence | Permitted claim |
|---|---|---|
| Fixture | Deterministic local inputs, schemas, command plans, normalized outputs, and failure tests | The repository contract works on the fixture. |
| Scheduler integration | Pinned environment and databases, completed scheduler job, exit state, elapsed time, peak RSS, and checked outputs | The pinned external tools ran on the named scheduler profile. |
| Biological validation | Versioned truth labels, stratified scientific metrics, controls, and documented limitations | The tested tool stack achieved the reported metrics on the named truth set. |

One level does not imply the next. A completed Slurm job is not biological validation until the result is scored against truth labels.

## Registry

[`validation/truth-sets.json`](https://github.com/fmschulz/omics-skills/blob/main/validation/truth-sets.json) records the candidate truth sets, evidence tier, biological strata, metrics, limitations, source release, license, and artifacts for:

- read QC and mapping;
- assembly and assembly QC;
- gene calling and ncRNA detection;
- functional annotation;
- phylogenomics;
- protein clustering and pangenomes;
- viromics;
- interdomain horizontal gene transfer.

Run the registry gate with:

```bash
uv run --script validation/scripts/validate_registry.py
```

A truth set can move from `candidate` to `ready` only after every required artifact has an immutable URL and a locally verified SHA-256. Upstream MD5 values remain provenance; they do not replace the local SHA-256 gate.

## Execution surfaces

| Skill | Current surface | Scheduler validation requirement |
|---|---|---|
| `bio-reads-qc-mapping` | External-tool driver | Execute the driver, score retained reads and mapping truth, then test reuse. |
| `bio-assembly-qc` | External-tool driver | Execute the driver and score MetaQUAST metrics against a gold assembly. |
| `bio-gene-calling` | Restartable external-tool driver | Execute each domain route and compare CDS, protein, tRNA, and rRNA calls with truth records. |
| `bio-annotation` | Artifact builder | Add an upstream annotation adapter before scoring CAFA or curated labels. |
| `bio-phylogenomics` | External-tool driver | Execute marker trees and compare supported splits with the reference tree. |
| `bio-protein-clustering-pangenome` | Artifact builder | Run an orthology tool first, then submit its predictions to QfO-compatible scoring. |
| `bio-viromics` | Artifact builder | Run geNomad and CheckV first, then score labeled contigs before building the evidence bundle. |
| `bio-interdomain-hgt` | Artifact builder | Run homology, context, and tree stages first; score simulations separately from curated empirical controls. |

## Slurm job contract

[`validation/schemas/slurm-job.schema.json`](https://github.com/fmschulz/omics-skills/blob/main/validation/schemas/slurm-job.schema.json) requires:

- validation, driver, and truth-set identifiers;
- cluster, account, partition, QOS, CPU, memory, and time values;
- checksummed Pixi lock or container record;
- checksummed database files or directory trees;
- version commands, the analysis command, and minimum output sizes.

Render without submission:

```bash
validation/scripts/submit_slurm_job.sh --dry-run \
  validation/jobs/<ready-job>.json \
  tasks/biological-validation/runs/<validation-id>/job.sbatch
```

The renderer rejects `draft` jobs and unresolved placeholders. A later `--submit` invocation re-renders the manifest and requires the result to match an existing dry-run script byte for byte. `--submit` also requires `OMICS_VALIDATION_SUBMIT_APPROVED=1`; set it only after the rendered script has been reviewed and approved. Submit from the login node named by `scheduler.cluster`; the generated Slurm log paths are absolute under `workdir`.

## Run evidence

Collect scheduler accounting after the job reaches a terminal state:

```bash
sacct -j "$JOB_ID" \
  --format=JobIDRaw,State,ExitCode,ElapsedRaw,MaxRSS,AllocCPUS,ReqMem,NodeList \
  --parsable2 > tasks/biological-validation/runs/<validation-id>/sacct.psv

uv run --script validation/scripts/collect_slurm_evidence.py \
  validation/jobs/<ready-job>.json \
  --job-id "$JOB_ID" \
  --sacct-file tasks/biological-validation/runs/<validation-id>/sacct.psv \
  --output tasks/biological-validation/runs/<validation-id>/run-evidence.json
```

The run record stores Slurm state, exit code, elapsed seconds, peak RSS, requested resources, nodes, output sizes, and output SHA-256 values. Driver-specific scoring adds scientific metrics only after the scheduler and artifact checks pass.

## Current pilot

[`validation/jobs/phylogenomics-qfo-pilot.draft.json`](https://github.com/fmschulz/omics-skills/blob/main/validation/jobs/phylogenomics-qfo-pilot.draft.json) defines the first pilot. It remains `draft` until these values are known on a scheduler login node:

- the cluster name plus a small-job account, partition, and QOS on it;
- the remote checkout and data paths;
- the QfO subset and reference-tree artifact SHA-256 values;
- the solved Pixi lock SHA-256.

Pick the small-job partition of the cluster that holds the data, never a different
cluster. Job IDs collide across clusters, so `scheduler.cluster` in the job manifest
is required and is passed to `sacct -M` when evidence is collected; the run record
keeps it so a result can never be attributed to the wrong scheduler.
