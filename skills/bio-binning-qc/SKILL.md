---
name: bio-binning-qc
description: Perform metagenomic binning, refinement, and QC with completeness/contamination checks.
---

# Bio Binning QC

Perform metagenomic binning, refinement, and QC with completeness/contamination checks.

## Instructions

1. Compute per-sample depth/coverage with CoverM v0.7.0+ (or BBMap for short reads, minimap2 for long reads).
2. Bin contigs with **QuickBin** (high-fidelity, CheckM2-agnostic; scales well on both short-read and long-read assemblies). On a GPU node, run **SemiBin2 v2.2.1+** instead — self-supervised contrastive learning with CUDA-backed PyTorch. MetaBAT2 v2.15+ is kept only as a legacy fallback for reproducing prior pipelines.
3. Classify bins by domain (bacteria/archaea vs eukaryotes).
4. Run domain-specific QC:
   - CheckM2 v1.1.0+ for bacterial and archaeal bins (note: v1.1.0 is a breaking upgrade — new DIAMOND v3 database from Zenodo DOI 10.5281/zenodo.14897628 and new dependency tree; re-install via mamba and refresh the DB).
   - EukCC v2.1.3+ for eukaryotic bins.
   - GUNC v1.0.6+ for contamination detection across all domains; treat it as a complement to CheckM2 (improves recall of chimeric bins).

## Quick Reference

| Task | Action |
|------|--------|
| Run workflow | Follow the steps in this skill and capture outputs. |
| Validate inputs | Confirm required inputs and reference data exist. |
| Review outputs | Inspect reports and QC gates before proceeding. |
| Tool docs | See `docs/README.md`. |

## Input Requirements

Prerequisites:
- Tools available in the active environment (Pixi/conda/system). See `docs/README.md` for expected tools.
- Reference DB root: set `BIO_DB_ROOT` (default `/media/shared-expansion/db/` on WSU).
- Coverage/depth tables or reads available to compute coverage.
Inputs:
- contigs.fasta
- coverage.tsv (per-sample depth table)

## Output

- results/bio-binning-qc/bins/
- results/bio-binning-qc/bin_metrics.tsv
- results/bio-binning-qc/bin_qc_report.html
- results/bio-binning-qc/logs/

## Quality Gates

- [ ] Completeness and contamination meet project thresholds.
- [ ] Chimera and contamination flags are below thresholds.
- [ ] On failure: retry with alternative parameters; if still failing, record in report and exit non-zero.
- [ ] Verify contigs.fasta and coverage.tsv are non-empty.
- [ ] Verify reference DBs for QC tools exist under the reference root.

## Examples

### Example 1: Expected input layout

```text
contigs.fasta
coverage.tsv (per-sample depth table)
```

## Troubleshooting

**Issue**: Missing inputs or reference databases
**Solution**: Verify paths and permissions before running the workflow.

**Issue**: Low-quality results or failed QC gates
**Solution**: Review reports, adjust parameters, and re-run the affected step.