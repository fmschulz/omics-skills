---
name: bio-binning-qc
description: Bin metagenomic contigs with QuickBin and assess MAG quality with CheckM2, GUNC, EukCC, and GTDB-Tk. Use when binning an assembly or scoring bin completeness and contamination.
---

# Bio Binning QC

Bin metagenomic contigs, route bins by domain, run domain-specific quality checks, and join the results into normalized tables.

## Instructions

Tool guides and versions: [docs/README.md](docs/README.md).

1. Map each sample's reads back to the assembly (BBMap or `bwa-mem2` for short reads, minimap2 for long reads; see `/bio-reads-qc-mapping`), then compute per-sample contig depth from the sorted BAMs with CoverM v0.7.0+.
2. Bin contigs with QuickBin from Bryce Foster's BBTools container (`bryce911/bbtools:39.85`; record the digest when pulled). QuickBin is the default for short-read and long-read assemblies ([docs/quickbin.md](docs/quickbin.md)). On a CUDA GPU node, SemiBin2 v2.3.0+ is the alternative. Use MetaBAT2 v2.18+ only to reproduce a prior pipeline.
3. Run `/tracking-taxonomy-updates` for BBTools-container QuickClade domain triage on the bin directory and the source assembly with `percontig`. Persist the per-contig screen so mixed bins are visible.
4. Route bins by the QuickClade domain screen:
   - Bacteria or Archaea -> run GTDB-Tk taxonomy assignment. If the GTDB-Tk reference package is missing, set it up under `$BIO_DB_ROOT`, export `GTDBTK_DATA_PATH`, run `gtdbtk check_install`, and record the release before classification.
   - Eukaryota -> run EukCC v2.1.3+ for eukaryotic bins.
   - Viral or virus-like -> remove from MAG QC and route candidate contigs/genomes to `/bio-viromics`; use vConTACT3 for phage/prokaryotic-virus evidence and GVClass for giant-virus/Nucleocytoviricota candidates.
   - Mixed or low-confidence -> flag as potential chimeras and inspect per-contig assignments before QC scoring.
5. Run domain-specific QC:
   - CheckM2 v1.1.0+ for bacterial and archaeal bins (v1.1.0 is a breaking upgrade: update the pinned Pixi environment and refresh the DIAMOND v3 database from Zenodo DOI 10.5281/zenodo.14897628).
   - EukCC v2.1.3+ for eukaryotic bins.
   - GUNC v1.1.0+ (needed for the `progenomes_3` and `gtdb_214` databases) for bacterial and archaeal bins only, as a chimerism check next to CheckM2. Do not apply GUNC to eukaryotic bins. `gunc run` reads `.fa` files from `--input_dir` by default; set `--file_suffix` to match other bin suffixes.
6. Normalize routed outputs with `scripts/build_bin_qc_tables.py`. The join rejects GUNC rows for non-prokaryotic routes, refuses prokaryotic or eukaryotic bins that lack their domain-specific QC or taxonomy outputs, and refuses to overwrite existing outputs. Accepted routes are `prokaryote`, `eukaryote`, `prokaryotic_virus`, `giant_virus`, and `manual_review`.

## Quick Reference

| Task | Action |
|------|--------|
| Build normalized tables | `uv run --script skills/bio-binning-qc/scripts/build_bin_qc_tables.py --routing domain_routing.tsv --checkm2 quality_report.tsv --gunc GUNC.progenomes_3.maxCSS_level.tsv --eukcc eukcc.csv --gtdbtk gtdbtk.bac120.summary.tsv --out-dir results/bio-binning-qc` |
| Input tables | Native tool outputs, tab-separated: CheckM2 (`Name`, `Completeness`, `Contamination`), GUNC (`genome`, `clade_separation_score`, `pass.GUNC`), EukCC folder mode (`bin`, `completeness`, `contamination`, `ncbi_lng`), GTDB-Tk (`user_genome`, `classification`). FASTA suffixes on bin names are stripped before joining. When GTDB-Tk writes both `bac120` and `ar53` summaries, concatenate them with a single header line. |

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

- results/bio-binning-qc/bins/ (QuickBin or SemiBin2 output)
- results/bio-binning-qc/quickclade_percontig.tsv and domain_routing.tsv (from `/tracking-taxonomy-updates`)
- results/bio-binning-qc/bin_metrics.tsv (one row per routed bin; written by `build_bin_qc_tables.py`)
- results/bio-binning-qc/gtdbtk_taxonomy.tsv (one row per prokaryotic bin; written by `build_bin_qc_tables.py`)
- results/bio-binning-qc/bin_qc_report.json (routed-bin counts by domain; written by `build_bin_qc_tables.py`)
- results/bio-binning-qc/logs/

## Quality Gates

- [ ] Completeness, contamination, and GUNC chimerism results are reported against project thresholds (for example MIMAG, see [docs/README.md](docs/README.md)).
- [ ] On execution failure, preserve logs and report the failed command; retry only after diagnosing the cause and recording the changed parameters. Report unmet biological thresholds as results; never tune parameters solely to pass a gate.
- [ ] Verify contigs.fasta and coverage.tsv are non-empty.
- [ ] Verify reference DBs for QC tools exist under the reference root.
- [ ] QuickClade `percontig` screen exists for the source assembly and bin set before CheckM2/EukCC/GTDB-Tk decisions.
- [ ] Bacterial and archaeal bins have GTDB-Tk taxonomy with the database release recorded.
- [ ] Viral/virus-like bins are routed to `/bio-viromics` instead of reported as MAGs.
- [ ] Mixed-domain bins are flagged as possible contamination/chimeras with per-contig evidence.
- [ ] `bin_metrics.tsv` covers every routed bin, including viral and manual-review rows, and `gtdbtk_taxonomy.tsv` covers every prokaryotic bin.
