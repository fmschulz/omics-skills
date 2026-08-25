---
name: bio-workflow-methods-docwriter
description: Generate reproducible Methods from Nextflow, Snakemake, or CWL run artifacts. Use when documenting exact commands, versions, parameters, QC gates, provenance, and outputs.
---

# Bio Workflow Methods Docwriter

Create publication-ready Methods and run documentation from real workflow artifacts.

## Instructions

1. Collect the workflow evidence package (logs, configs, version files).
2. Build `run_manifest.yaml` strictly from evidence.
3. Validate the manifest against the schema.
4. Draft `METHODS.md` with a concise workflow summary at the top.
5. Verify QC gates and reproducibility details are captured.

Resolve the installed skill with:

```bash
METHODS_SKILL="${METHODS_SKILL:-$HOME/.agents/skills/bio-workflow-methods-docwriter}"
```

## Quick Reference

| Task | Action |
|------|--------|
| Evidence checklist | See `reference/evidence-checklist.md` |
| Standards to align with | See [reference/standards.md](reference/standards.md) |
| Manifest schema | `schemas/run-manifest.schema.json` (LinkML source: [schemas/workflow-run-schema.yaml](schemas/workflow-run-schema.yaml)) |
| Drafting templates | [METHODS.md template](templates/methods_report.md), [paper-summary YAML](templates/paper_summary.yaml) |
| Extract a Nextflow draft | `uv run "$METHODS_SKILL/scripts/extract_nextflow_run.py" --help` |
| Extract Snakemake evidence | `uv run --script "$METHODS_SKILL/scripts/extract_snakemake_run.py" --help` |
| Extract CWL evidence | `uv run --script "$METHODS_SKILL/scripts/extract_cwl_run.py" --help` |
| Validate manifest | `uv run "$METHODS_SKILL/scripts/validate_run_manifest.py" run_manifest.yaml` |
| Examples | See `examples/` |

## Input Requirements

- Workflow artifacts (Nextflow/Snakemake/CWL logs and configs)
- Tool version records or container digests
- QC reports and output manifests

## Output

- `METHODS.md` (agent-authored; workflow summary + detailed steps)
- `run_manifest.yaml` (machine-readable run manifest)
- Artifact contract: [schemas/run-manifest.schema.json](schemas/run-manifest.schema.json)
- LinkML source: [schemas/workflow-run-schema.yaml](schemas/workflow-run-schema.yaml)
- Paper-summary schema: [schemas/bio-paper-schema.yaml](schemas/bio-paper-schema.yaml)

## Quality Gates

- [ ] No invented commands, versions, or parameters
- [ ] Every step has inputs, outputs, and versions captured
- [ ] Commands were sourced from task scripts, not environment-bearing wrappers, and contain no credentials
- [ ] No `NOT CAPTURED`, `UNKNOWN`, or `TBD` placeholder remains in a required field
- [ ] Workflow summary appears at top of `METHODS.md`
- [ ] The engine-specific extractor output passes `validate_run_manifest.py`; the fixture-backed Nextflow path proves trace, task script, input, output, version, and final-output evidence end to end.

## Examples

### Example 1: Validate a manifest

```bash
METHODS_SKILL="${METHODS_SKILL:-$HOME/.agents/skills/bio-workflow-methods-docwriter}"
uv run "$METHODS_SKILL/scripts/validate_run_manifest.py" run_manifest.yaml
```

## Troubleshooting

**Issue**: Missing tool versions in logs
**Solution**: Use `NOT CAPTURED` only while assembling a draft. The final validator rejects it; recover the version from provenance or report the missing evidence in `limitations` without claiming a reproducible manifest.
