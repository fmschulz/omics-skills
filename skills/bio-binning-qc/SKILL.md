---
name: bio-binning-qc
description: Bin and refine metagenomic contigs, then assess MAG quality. Use when recovering genomes with QuickBin and checking completeness, contamination, and bin consistency.
---

# Bio Binning QC

Perform metagenomic binning, refinement, and QC with completeness/contamination checks.

## Instructions

Tool guides and versions: [docs/README.md](docs/README.md).

1. Compute per-sample depth/coverage with CoverM v0.7.0+ (or BBMap for short reads, minimap2 for long reads).
2. Bin contigs with **QuickBin** through Bryce Foster's official BBTools container (`bryce911/bbtools:39.85`; record digest when pulled). QuickBin is high-fidelity, CheckM2-agnostic, and scales well on both short-read and long-read assemblies. On a GPU node, run **SemiBin2 v2.3.0+** instead — self-supervised contrastive learning with CUDA-backed PyTorch. MetaBAT2 v2.18+ is kept only as a legacy fallback for reproducing prior pipelines.
3. Run `/tracking-taxonomy-updates` for BBTools-container QuickClade domain triage on the bin directory and the source assembly with `percontig`. Persist the per-contig screen so mixed bins are visible.
4. Route bins by the QuickClade domain screen:
   - Bacteria or Archaea -> run GTDB-Tk taxonomy assignment. If the GTDB-Tk reference package is missing, set it up under `$BIO_DB_ROOT`, export `GTDBTK_DATA_PATH`, run `gtdbtk check_install`, and record the release before classification.
   - Eukaryota -> run EukCC v2.1.3+ for eukaryotic bins.
   - Viral or virus-like -> remove from MAG QC and route candidate contigs/genomes to `/bio-viromics`; use vConTACT3 for phage/prokaryotic-virus evidence and GVClass for giant-virus/Nucleocytoviricota candidates.
   - Mixed or low-confidence -> flag as potential chimeras and inspect per-contig assignments before QC scoring.
5. Run domain-specific QC:
   - CheckM2 v1.1.0+ for bacterial and archaeal bins (v1.1.0 is a breaking upgrade: update the pinned Pixi environment and refresh the DIAMOND v3 database from Zenodo DOI 10.5281/zenodo.14897628).
   - EukCC v2.1.3+ for eukaryotic bins.
   - GUNC v1.0.6+ for bacterial and archaeal bins only; treat it as a complement to CheckM2 for chimerism detection. Do not apply GUNC to eukaryotic bins.
6. Normalize routed outputs with `scripts/build_bin_qc_tables.py`. The join
   rejects GUNC rows for non-prokaryotic routes and refuses prokaryotic or
   eukaryotic bins that lack their domain-specific QC/taxonomy outputs.

## Quick Reference

| Task | Action |
|------|--------|
| Build normalized tables | `uv run --script scripts/build_bin_qc_tables.py --routing domain_routing.tsv --checkm2 checkm2.tsv --gunc gunc.tsv --eukcc eukcc.tsv --gtdbtk gtdbtk.tsv --out-dir results/bio-binning-qc` |

## Input Requirements

Prerequisites:
- Tools declared in the project's pinned Pixi environment. See `docs/README.md` for expected tools.
- Reference DB root: set `BIO_DB_ROOT` to the project or site-local database directory.
- Coverage/depth tables or reads available to compute coverage.
- Docker or Apptainer/Singularity available for `bryce911/bbtools` QuickBin runs, or a documented local BBTools install.
Inputs:
- contigs.fasta
- coverage.tsv (per-sample depth table)

## Output

- results/bio-binning-qc/bins/
- results/bio-binning-qc/quickclade_percontig.tsv
- results/bio-binning-qc/domain_routing.tsv
- results/bio-binning-qc/gtdbtk_taxonomy.tsv
- results/bio-binning-qc/bin_metrics.tsv
- results/bio-binning-qc/bin_qc_report.html
- results/bio-binning-qc/logs/

## Quality Gates

- [ ] Completeness and contamination meet project thresholds.
- [ ] Chimera and contamination flags are below thresholds.
- [ ] On failure: retry with alternative parameters; if still failing, record in report and exit non-zero.
- [ ] Verify contigs.fasta and coverage.tsv are non-empty.
- [ ] Verify reference DBs for QC tools exist under the reference root.
- [ ] QuickClade `percontig` screen exists for the source assembly and bin set before CheckM2/EukCC/GTDB-Tk decisions.
- [ ] Bacterial and archaeal bins have GTDB-Tk taxonomy with the database release recorded.
- [ ] Viral/virus-like bins are routed to `/bio-viromics` instead of reported as MAGs.
- [ ] Mixed-domain bins are flagged as possible contamination/chimeras with per-contig evidence.
- [ ] Normalized `bin_metrics.tsv` and `gtdbtk_taxonomy.tsv` cover every routed bin, including explicit viral/manual-review rows.
