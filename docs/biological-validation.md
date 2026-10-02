# Validation

The tests show that the pack's contracts hold on small fixtures. They do not show that the external tools produce correct biology. The validation program keeps these claims apart.

## Evidence levels

| Level | Required evidence | Permitted claim |
|---|---|---|
| Fixture | Deterministic local inputs, schemas, command plans, normalized outputs and failure tests | The repository contract works on the fixture. |
| Scheduler integration | Pinned environment and databases, a completed scheduler job, exit state, elapsed time, peak RSS and checked outputs | The pinned external tools ran on the named scheduler profile. |
| Biological validation | Versioned truth labels, stratified scientific metrics, controls and documented limitations | The tested tool stack reached the reported metrics on the named truth set. |

One level does not imply the next. A completed Slurm job is not biological validation until its result is scored against truth labels.

## What the tests cover

`make test` runs the skill, supplementary-doc and citation validators, the unit and fixture tests, and the routing benchmark. For skills that ship a driver or an artifact builder, the fixture tests check command plans, restart and reuse decisions, output normalization, schema validation and failure paths. They do not run the heavy external tools or their databases. A production run still needs pinned databases and containers, a scheduler job, and the QC gates in each skill.

## Truth-set registry

[`validation/truth-sets.json`](https://github.com/fmschulz/omics-skills/blob/main/validation/truth-sets.json) records, for eight core skills, the candidate truth set, its evidence tier, biological strata, metrics, limitations, source release, license and artifacts. The skills are read QC and mapping, assembly, gene calling and ncRNA detection, functional annotation, phylogenomics, protein clustering and pangenomes, viromics, and interdomain horizontal gene transfer.

```bash
uv run --script validation/scripts/validate_registry.py
```

A truth set moves from `candidate` to `ready` only when every required artifact has an immutable URL and a locally verified SHA-256. Upstream MD5 values stay as provenance; they do not replace the SHA-256 check. All eight truth sets are `candidate`.

| Skill | Current surface | Needed for scheduler validation |
|---|---|---|
| `bio-reads-qc-mapping` | External-tool driver | Run the driver, score retained reads and mapping against truth, then test reuse. |
| `bio-assembly-qc` | External-tool driver | Run the driver and score MetaQUAST metrics against a gold assembly. |
| `bio-gene-calling` | Restartable external-tool driver | Run each domain route and compare CDS, protein, tRNA and rRNA calls with truth records. |
| `bio-annotation` | Artifact builder | Add an upstream annotation adapter before scoring CAFA or curated labels. |
| `bio-phylogenomics` | External-tool driver | Run marker trees and compare supported splits with the reference tree. |
| `bio-protein-clustering-pangenome` | Artifact builder | Run an orthology tool, then submit its predictions to QfO-compatible scoring. |
| `bio-viromics` | Artifact builder | Run geNomad and CheckV, then score labeled contigs before building the evidence bundle. |
| `bio-interdomain-hgt` | Artifact builder | Run the homology, context and tree stages; score simulations apart from curated empirical controls. |

## Slurm jobs

A job manifest follows [`validation/schemas/slurm-job.schema.json`](https://github.com/fmschulz/omics-skills/blob/main/validation/schemas/slurm-job.schema.json) and names:

- the validation, driver and truth set
- the cluster, account, partition, QOS, CPUs, memory and time
- a checksummed Pixi lock or container, and checksummed databases
- version commands, the analysis command and the expected outputs

Render the job without submitting it:

```bash
validation/scripts/submit_slurm_job.sh --dry-run \
  validation/jobs/<ready-job>.json \
  tasks/biological-validation/runs/<validation-id>/job.sbatch
```

The renderer rejects `draft` jobs and unresolved placeholders. Review the rendered script before you submit it with the same arguments and `--submit`:

- `--submit` renders the manifest again. When the script path already holds the reviewed script, the two must match byte for byte; when it does not, the new render is written and submitted unreviewed, so always run `--dry-run` first.
- `--submit` also requires `OMICS_VALIDATION_SUBMIT_APPROVED=1`. Set it only after the rendered script is approved.
- The wrapper calls `sbatch` without `-M`, so the job runs on the cluster of the host you submit from. Submit from a login node of the cluster named in `scheduler.cluster`, the one that holds the data, never from another cluster.

After the job ends, collect its evidence. `--fetch-sacct` queries `sacct -M` with the manifest's `scheduler.cluster`, because job IDs repeat across clusters.

```bash
uv run --script validation/scripts/collect_slurm_evidence.py \
  validation/jobs/<ready-job>.json \
  --job-id "$JOB_ID" --fetch-sacct \
  --output tasks/biological-validation/runs/<validation-id>/run-evidence.json
```

The run record stores the cluster, Slurm state, exit code, elapsed seconds, peak RSS, requested resources, nodes, and output sizes and SHA-256 values. Scientific metrics are added only after these scheduler and artifact checks pass.

## Current pilot

The first pilot, [`validation/jobs/phylogenomics-qfo-pilot.draft.json`](https://github.com/fmschulz/omics-skills/blob/main/validation/jobs/phylogenomics-qfo-pilot.draft.json), stays `draft` until these values are known on a scheduler login node:

- the cluster, and a small-job account, partition and QOS on it
- the remote checkout and data paths
- the SHA-256 values of the QfO subset and the reference tree
- the SHA-256 of the solved Pixi lock

Phylogenomics goes first because it needs no large reference database.

Comparative-discovery thresholds need separate prokaryote, eukaryote, phage and Nucleocytoviricota campaigns.
