# GVClass Usage Guide

Last verified: 2026-11-11
Tool version/release checked: GVClass v2.1.0 software (2026-10-19); runtime resource bundle v2.1.0 (Zenodo DOI 10.5281/zenodo.23381313, about 1.5 GB in 24 parts). Options and columns checked against the CHANGELOG and docs of the v2.1.0 tag; not run (the bundle and the new torch environment are too large for a smoke test)
Official docs/manual: https://NeLLi-team.github.io/gvclass/
Release/source: https://github.com/NeLLi-team/gvclass/releases/tag/v2.1.0 ; https://github.com/NeLLi-team/gvclass

## Official Documentation
- Documentation site (CLI, configuration, output columns, markers): https://NeLLi-team.github.io/gvclass/
- GitHub: https://github.com/NeLLi-team/gvclass
- Citation: Pitot et al. (2024) *npj Viruses* https://doi.org/10.1038/s44298-024-00069-7

## Overview
GVClass assigns taxonomy to giant-virus genomes and MAGs in Nucleocytoviricota, Mirusviricota, and Preplasmiviricota (PPV). It calls genes across nine genetic codes, detects marker proteins with HMM panels, places each marker protein in its own reference tree, and takes a nearest-neighbor majority vote across trees. Marker counts feed completeness and contamination models tuned for giant viruses. Genus and species labels are nearest-reference labels, not new taxon assignments.

Parsers written for earlier versions need updates:

- v2.0.0 removed `taxonomy_strict`, `gvog8_unique`, and `gvog8_total`.
- v2.1.0 merged the entrypoints `gvclass` and `gvclass-a` into one `gvclass` (`gvclass-a` is gone from `main`; a job script that downloads it must download `gvclass` and keep its `--image` or `--apptainer` argument).
- v2.1.0 no longer emits the labels `moderate` and `high` in `completeness_model_reliability`.
- v2.1.0 reports `NaN` (not 0) for an estimate without informative markers, and a contamination estimate only for NCLDV targets with supported evidence.
- v2.1.0 gives a eukaryotic domain only when its markers are at least 80% of the markers voting for a cellular domain. Otherwise the domain stays unassigned and `taxonomy_confidence` reports `mixed_cellular`.
- The resource bundle v2.1.0 is required. Setup uses one exact source and does not follow Zenodo's latest release or fall back to an older bundle.

## Installation

### Pixi (local)
```bash
git clone https://github.com/NeLLi-team/gvclass.git
cd gvclass
pixi install
pixi run setup-db
pixi run example
```

`pixi run setup-db` downloads the bundle in 24 checked parts into `resources/` (or into `GVCLASS_DB`). The environment now includes torch and transformers.

### Apptainer (HPC)
```bash
wget https://raw.githubusercontent.com/NeLLi-team/gvclass/main/gvclass
chmod +x gvclass
./gvclass --apptainer QUERY_DIR RESULTS_DIR -t 32
```

The launcher pulls `library://nelligroup-jgi/gvclass/gvclass:2.1.0` and caches resources under `~/.cache/gvclass/resource-cache/v2.1.0`. `--resource-cache-dir` moves that cache to scratch. `--image PATH_OR_URI` selects a local `.sif` and implies `--apptainer`. The launcher calls `apptainer` by name. Container mode forwards the analysis options; `--config`, `--database` and the `--cluster-*` options work only in native mode, and `gvclass screen` is native only.

## Key Commands & Flags

**Pixi** (run from the repository directory):
```bash
pixi run gvclass QUERY_DIR -o OUTPUT_DIR -t THREADS [OPTIONS]
```

**Apptainer** (query first, results second or `-o`):
```bash
./gvclass --apptainer QUERY_DIR RESULTS_DIR -t THREADS [OPTIONS]
```

| Flag | Default | Description |
|------|---------|-------------|
| `-o, --output-dir` | `<query_dir>_results` | Output directory |
| `-t, --threads` | 4 (native), 16 (container) | Total threads; match the allocation |
| `-j, --max-workers` | auto | Genomes processed in parallel |
| `--threads-per-worker` | auto | Threads per worker |
| `-c, --config` | `config/gvclass_config.yaml` | YAML configuration (native only) |
| `-d, --database` | config | Database path; overrides `GVCLASS_DB` and the config (native only) |
| `--tree-method` | `veryfasttree` | `veryfasttree`, `iqtree` (slower), or `fasttree` (alias for VeryFastTree) |
| `--iqtree-mode` | `fast` | Species-tree IQ-TREE mode: `fast` or `ufboot` |
| `--mode-fast` | on | Skip the order-level marker trees; the order-level HMM searches still run |
| `-e, --extended` | off | Build trees for all markers; turns fast mode off |
| `--sensitive` / `--no-sensitive` | on | HMM search at `E=1e-5`, `domE=1e-5`, no GA cutoffs; `--no-sensitive` wins when both are given |
| `--completeness-mode` | `novelty-aware` | `legacy` or `novelty-aware` |
| `--species-tree` | off | Build a concatenated-marker species tree per query |
| `--species-tree-combined` | off | Enable `--species-tree` and add a combined tree of queries and references per viral panel |
| `--species-tree-trim` | `witchi` | `witchi`, `pytrimal`, or `none` |
| `-C, --contigs` | off | Classify each contig of an FNA as its own query |
| `--min-length` | 20000 | Minimum total length for bin/MAG `.fna` inputs; `0` removes the floor |
| `--allow-short` | off | Bypass the nucleotide length threshold; other FASTA checks stay |
| `--contigs-min-length` | 10000 | Minimum contig length with `--contigs` |
| `--resume` | off | Skip queries already completed in `run_status.json` that match the current quality schema and model set |
| `--plain-output` | off | Disable emoji and ANSI colors in logs |

The `--cluster-*` flags are parsed but have no effect. Submit one GVClass run as one batch job.

### `gvclass screen` (new in v2.1.0)

```bash
pixi run gvclass screen --install                 # once: 3.2 GB download, 6 GiB installed
pixi run gvclass screen BIN_OR_FOLDER -o SCREEN_DIR -t 8
```

It flags possible contamination in giant-virus bins and gives no contamination estimate: a cellular screen scores 10 kb windows for bacterial, archaeal and eukaryotic sequence, and a giant-virus screen finds contigs of a second giant virus (5 kb or longer). A flag is a review prompt, not a deletion instruction. Its authors report a false-flag rate of 1.2% of 3 kb windows of new giant-virus genomes and 18.8% of herpesvirus windows.

## Common Usage Examples

### Directory of bins
```bash
pixi run gvclass my_bins -o my_results -t 16
```

### HPC run, four genomes in parallel with four threads each
```bash
./gvclass --apptainer my_bins results -t 16 -j 4
```

### Contigs from an assembly
```bash
pixi run gvclass assembled_contigs.fna -o results -t 16 --contigs --contigs-min-length 30000
```

### All marker trees and a species tree
```bash
pixi run gvclass my_bins -o my_results -t 16 --extended --species-tree
```

### Resume an interrupted run
```bash
pixi run gvclass my_bins -o my_results -t 16 --resume
```

## Input/Output

### Input
- A directory of `.fna` or `.faa` files (also `.fa`, `.fasta`, `.fas`), one file per putative genome; bins are the intended input.
- For giant-virus discovery from contigs, filter to 30 kb or more (50 kb preferred).
- Files with the same stem (`sample.fna` and `sample.faa`) are rejected.

### Run-level output

| File | Contents |
|------|----------|
| `gvclass_summary.tsv` / `.csv` | One row per query, 50 columns |
| `gvclass_summary.extended.tar.gz` | Per-contig contamination diagnostics, including `contamination_model_applicability` |
| `gvclass_failed_queries.tsv` | Written only when queries fail; the run then exits non-zero |
| `run_status.json` | Versions, settings, per-query status, and checksums; used by `--resume` |
| `run.log` | Chronological run log |
| `<query>.tar.gz` | Per-query trees and summaries, including `stats/<query>.contamination_candidates.tsv` and `contamination_review.tsv` |

A query that runs again keeps its earlier working directory as `<query>.previous.<unique>/`. A failed search, tree, or summary step fails the query; GVClass does not fall back silently.

### Key Summary Columns

| Column | Description |
|--------|-------------|
| `taxonomy_majority` | Lineage from the per-marker nearest-neighbor majority vote |
| `taxonomy_confidence` | `high`, or flags: `low_support`, `mixed_cellular` (eukaryotic markers won the domain vote without 80% of the cellular-domain markers), `reduced_fastmode`, `no_support` |
| `species` ... `domain` | Per-rank calls with per-taxon counts |
| `avgdist` | Average tree distance to the reference neighbors |
| `estimated_completeness` | Marker-recovery estimate (%); `NaN` when there is no informative marker. It does not certify absolute completeness |
| `completeness_query_support` | `supported`, `limited_support`, `insufficient_evidence`, `unassigned`, `unsupported_target`, or `unavailable` |
| `estimated_completeness_strategy`, `completeness_model_group` | How and with which resource group the estimate was made |
| `completeness_model_reliability` | `unvalidated_legacy`, `advisory_only` (marker dropout validation only), or `unavailable`; never `moderate` or `high` |
| `estimated_contamination` | Contamination estimate (`extra_trees_v1`); `NaN` for MIRUS, PPV and other targets and for inputs without evidence |
| `contamination_query_support`, `estimated_contamination_strategy`, `contamination_model_reliability` | Evidence status, method and validation status of the contamination estimate |
| `contamination_type` | `clean` below the reporting threshold (10), else `cellular`, `mixed_viral`, `phage`, `duplication`, or `uncertain`. `clean` is a threshold result, not proof of absence |
| `order_dup`, `gvog4_dup`, `gvog8_dup` | Marker duplication factors; near 1 for one clean genome |
| `gvog4_completeness`, `gvog8_completeness` | Core NCLDV markers present as `n/4` and `n/8` |
| `busco_completeness`, `cog_completeness` and their `_dup` | Cellular marker panels; high duplication flags cellular carry-over |
| `capsid_group` | Capsid-type tally across NCLDV, Mirusviricota, and PPV capsid groups |
| `LENbp`, `GCperc`, `genecount`, `CODINGperc`, `ttable` | Genome statistics and the genetic code used |

The column reference lists all 50: https://NeLLi-team.github.io/gvclass/reference/output/

## Quality Interpretation

- Read `taxonomy_confidence` with the duplication columns; duplicated markers inflate vote counts without adding independent evidence.
- `mixed_cellular` means eukaryotic markers won the domain vote without enough support. Check the bin for cellular carry-over before accepting a domain.
- `reduced_fastmode` means order resolution rests on the core markers; rerun with `--extended` when order-level placement matters.
- `order_dup` or `gvog8_dup` above about 2 points to multiple populations, a chimera, or a mixed bin.
- Elevated `busco_dup` or `cog_dup` points to cellular sequence in the bin.
- A high `avgdist` can mean a novel lineage or a poor-quality query; separate the two with completeness and duplication.
- Every bundled model reports `unvalidated_legacy`: read the completeness and contamination values as marker-based estimates. `NaN` with `insufficient_evidence` is missing evidence, not a complete or clean genome.
- Use `contamination_candidates.tsv` and `contamination_review.tsv` to see which contigs to review. A review row is not a deletion instruction.

## Integration with Viromics Workflow

1. Input: bins or long contigs routed as giant-virus candidates by QuickClade or geNomad.
2. Analysis: per-marker phylogenetic placement and quality models.
3. Output: taxonomy, completeness, contamination, and duplication metrics.
4. Follow with core-gene phylogenies, as the [phylogenomics page](../../omics-pipeline/references/phylogenomics.md) describes, for placement claims beyond the nearest reference.

## Troubleshooting

- **Run exits non-zero after finishing**: one or more queries failed; read `gvclass_failed_queries.tsv`.
- **Query skipped as too short**: lower `--min-length` or `--contigs-min-length`, or pass `--allow-short`, only when the shorter sequences are wanted.
- **No taxonomy assigned**: the query is too short, too divergent, or not a giant virus.
- **Memory errors**: lower `--max-workers`.
- **Database errors after an upgrade**: v2.1.0 needs bundle v2.1.0; run `pixi run setup-db` again.
