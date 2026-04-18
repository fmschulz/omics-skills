---
name: bio-annotation
description: Functional annotation and taxonomy inference from sequence homology.
---

# Bio Annotation

Functional annotation and taxonomy inference from sequence homology.

## Instructions

1. Read `docs/README.md` and the relevant tool guides before running anything.
2. For InterProScan, read `docs/interproscan-usage.md` and validate the exact CLI with `--help` or `--version`.
3. Run InterProScan for domain/family annotation.
4. Run eggnog-mapper for orthology-based annotation.
5. Run DIAMOND and resolve taxonomy with TaxonKit.

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
- Input FASTA and reference DBs are readable.
Inputs:
- proteins.faa (FASTA protein sequences).
- reference_db/ (eggNOG, InterPro, DIAMOND databases + taxdump).

## Output

- results/bio-annotation/annotations.parquet
- results/bio-annotation/taxonomy.parquet
- results/bio-annotation/annotation_report.md
- results/bio-annotation/logs/

## Quality Gates

- [ ] Annotation hit rate and taxonomy rank coverage meet project thresholds.
- [ ] On failure: retry with alternative parameters; if still failing, record in report and exit non-zero.
- [ ] Verify proteins.faa is non-empty and amino acid encoded.
- [ ] Verify proteins.faa does not contain `*` stop symbols before InterProScan, or strip them deliberately.
- [ ] Verify InterProScan output options are valid: use `-b` or `-d`, never both together.
- [ ] Verify packaged InterProScan installs have been initialized with `python3 setup.py -f interproscan.properties` when required.
- [ ] Verify required InterProScan helper binaries are resolvable, especially `ps_scan.pl`, `pfscan`, and `pfsearch`.
- [ ] Run a small login-node smoke test on 1-2 proteins before submitting a large cluster job.
- [ ] Verify required reference DBs exist under the reference root.

## Examples

### Example 1: Expected input layout

```text
proteins.faa (FASTA protein sequences).
reference_db/ (eggNOG, InterPro, DIAMOND databases + taxdump).
```

## Troubleshooting

**Issue**: Missing inputs or reference databases
**Solution**: Verify paths and permissions before running the workflow.

**Issue**: InterProScan fails immediately with CLI or runtime setup errors
**Solution**: Check `docs/interproscan-usage.md` for mutually exclusive output flags, `*` stripping, one-time `setup.py` initialization, and ProSite `PATH` requirements.

**Issue**: Low-quality results or failed QC gates
**Solution**: Review reports, adjust parameters, and re-run the affected step.
