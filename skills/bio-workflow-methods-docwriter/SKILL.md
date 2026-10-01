---
name: bio-workflow-methods-docwriter
description: Generate reproducible Methods from Nextflow, Snakemake, or CWL run artifacts. Use when documenting exact commands, versions, parameters, QC gates, provenance, and outputs.
---

# Bio Workflow Methods Docwriter

Write Methods text and run documentation from real workflow artifacts. Every command, version, and parameter comes from evidence; nothing is inferred.

## Instructions

1. Collect the evidence package listed in [reference/evidence-checklist.md](reference/evidence-checklist.md): launch command, configs, engine version, tool versions or container digests, input checksums or accessions, reference and database versions, QC reports, and the final output list.
2. Build a draft `run_manifest.yaml` with the extractor for the engine:
   - Nextflow: `extract_nextflow_run.py` reads `trace.txt` and the `work/` task folders. `--tool-versions` is a JSON mapping of process name to `{"tool": ..., "version": ...}`; `--outputs-manifest` lists one final output path per line.
   - Snakemake: `extract_snakemake_run.py` reads a JSONL file with one record per job (`rule`, `status`, `tool`, `version`, `command`, `inputs`, `outputs`). Assemble it from `--printshellcmds` logs and the version records; see `fixtures/snakemake/jobs.jsonl`.
   - CWL: `extract_cwl_run.py` reads one normalized JSON record (run metadata plus `steps` and `outputs`), not a raw CWLProv folder; see `fixtures/cwl/provenance.json`.
3. Fill the remaining fields from evidence only. While drafting, mark a missing value `NOT CAPTURED`; the final manifest must not contain it. If the value cannot be recovered, record the gap under `limitations` and do not call the manifest reproducible.
4. Validate the manifest against [schemas/run-manifest.schema.json](schemas/run-manifest.schema.json) with `validate_run_manifest.py`.
5. Draft `METHODS.md` from [templates/methods_report.md](templates/methods_report.md): workflow summary at the top, then inputs, exact rerun command, environment, steps as executed, QC, outputs, and limitations.
6. For manuscript Methods prose, hand the manifest to `/scientific-writing`. Keep script names, internal flags, and runtime bookkeeping in Methods or the supplement, not in Results.

Resolve the installed skill once:

```bash
METHODS_SKILL="${METHODS_SKILL:-$HOME/.agents/skills/bio-workflow-methods-docwriter}"
```

Each script declares its dependencies inline (PEP 723), so `uv run --script` needs no separate environment.

## Quick Reference

| Task | Action |
|------|--------|
| Evidence checklist | [reference/evidence-checklist.md](reference/evidence-checklist.md) |
| Standards to align with | [reference/standards.md](reference/standards.md) |
| Manifest schema | [schemas/run-manifest.schema.json](schemas/run-manifest.schema.json) (LinkML source: [schemas/workflow-run-schema.yaml](schemas/workflow-run-schema.yaml)) |
| Drafting templates | [METHODS.md template](templates/methods_report.md), [paper-summary YAML](templates/paper_summary.yaml) |
| Extract a Nextflow draft | `uv run --script "$METHODS_SKILL/scripts/extract_nextflow_run.py" --help` |
| Extract a Snakemake draft | `uv run --script "$METHODS_SKILL/scripts/extract_snakemake_run.py" --help` |
| Extract a CWL draft | `uv run --script "$METHODS_SKILL/scripts/extract_cwl_run.py" --help` |
| Validate manifest | `uv run --script "$METHODS_SKILL/scripts/validate_run_manifest.py" run_manifest.yaml` |
| Complete example manifest | [examples/run_manifest.example.yaml](examples/run_manifest.example.yaml) |

## Input Requirements

- Workflow artifacts (Nextflow/Snakemake/CWL logs and configs)
- Tool version records or container digests
- QC reports and output manifests

## Output

- `METHODS.md` (agent-authored; workflow summary first, then detailed steps)
- `run_manifest.yaml` (machine-readable run manifest)
- Artifact contract: [schemas/run-manifest.schema.json](schemas/run-manifest.schema.json)
- Paper-summary schema: [schemas/bio-paper-schema.yaml](schemas/bio-paper-schema.yaml)

## Quality Gates

- [ ] No invented commands, versions, or parameters
- [ ] Every step has inputs, outputs, and versions captured
- [ ] Commands were sourced from task scripts, not environment-bearing wrappers, and contain no credentials
- [ ] No `NOT CAPTURED`, `UNKNOWN`, or `TBD` placeholder remains in a required field
- [ ] Workflow summary appears at top of `METHODS.md`
- [ ] The final manifest passes `validate_run_manifest.py`

## Examples

### Example 1: Nextflow run to validated manifest

```bash
METHODS_SKILL="${METHODS_SKILL:-$HOME/.agents/skills/bio-workflow-methods-docwriter}"
uv run --script "$METHODS_SKILL/scripts/extract_nextflow_run.py" \
  --trace trace.txt --workdir work --out run_manifest.yaml \
  --run-id rnaseq-2026-02-02 --pipeline-name nf-core/rnaseq --pipeline-version 3.14.0 \
  --commit-sha <sha> --engine-version <nextflow -version> \
  --launch-command "<exact launch command>" \
  --tool-versions tool-versions.json --outputs-manifest outputs.txt
uv run --script "$METHODS_SKILL/scripts/validate_run_manifest.py" run_manifest.yaml
```

## Troubleshooting

**Issue**: Missing tool versions in logs
**Solution**: Use `NOT CAPTURED` only while assembling a draft. The final validator rejects it; recover the version from provenance or report the missing evidence in `limitations` without claiming a reproducible manifest.
