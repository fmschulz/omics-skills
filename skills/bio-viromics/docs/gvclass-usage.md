# GVClass Usage Guide

Last verified: 2026-10-01
Tool version/release checked: GVClass v2.0.3 software; runtime resource bundle v2.0.0 (Zenodo record https://zenodo.org/records/21225457)
Official docs/manual: https://NeLLi-team.github.io/gvclass/
Release/source: https://github.com/NeLLi-team/gvclass/releases/tag/v2.0.3 ; https://github.com/NeLLi-team/gvclass

## Official Documentation
- Documentation site (CLI, configuration, output columns, markers): https://NeLLi-team.github.io/gvclass/
- GitHub: https://github.com/NeLLi-team/gvclass
- Citation: Pitot et al. (2024) *npj Viruses* https://doi.org/10.1038/s44298-024-00069-7

## Overview
GVClass assigns taxonomy to giant-virus genomes and MAGs in Nucleocytoviricota, Mirusviricota, and Preplasmiviricota (PPV). It calls genes across nine genetic codes, detects marker proteins with HMM panels, places each marker protein in its own reference tree, and takes a nearest-neighbor majority vote across trees. Marker counts feed completeness and contamination models tuned for giant viruses. Genus and species labels are nearest-reference labels, not new taxon assignments.

v2.0.0 changed the summary schema: `taxonomy_strict`, `gvog8_unique`, and `gvog8_total` were removed. Parsers written for v1.x must be updated.

## Installation

### Pixi (local)
```bash
git clone https://github.com/NeLLi-team/gvclass.git
cd gvclass
pixi install
pixi run setup-db
pixi run example
```

### Apptainer (HPC)
```bash
wget https://raw.githubusercontent.com/NeLLi-team/gvclass/main/gvclass-a
chmod +x gvclass-a
```

The wrapper pulls `library://nelligroup-jgi/gvclass/gvclass:2.0.3`, which embeds the v2.0.0 database, and caches materialized resources under `~/.cache/gvclass/resource-cache/v2.0.0`. Use `--resource-cache-dir` to put that cache on scratch. The wrapper calls `apptainer` by name.

## Key Commands & Flags

**Pixi** (run from the repository directory):
```bash
pixi run gvclass QUERY_DIR -o OUTPUT_DIR -t THREADS [OPTIONS]
```

**Apptainer** (query first, results second):
```bash
./gvclass-a QUERY_DIR RESULTS_DIR -t THREADS [OPTIONS]
```

| Flag | Default | Description |
|------|---------|-------------|
| `-o, --output-dir` | `<query_dir>_results` | Output directory |
| `-t, --threads` | 4 (Pixi config), 16 (wrapper) | Total threads; match the allocation |
| `-j, --max-workers` | auto | Genomes processed in parallel |
| `--threads-per-worker` | auto | Threads per worker |
| `-d, --database` | config | Database path; overrides `GVCLASS_DB` and the config |
| `--tree-method` | `veryfasttree` | `veryfasttree`, `iqtree` (slower), or `fasttree` (alias for VeryFastTree) |
| `--iqtree-mode` | `fast` | Species-tree IQ-TREE mode: `fast` or `ufboot` |
| `--mode-fast` | on | Skip the 576 order-level marker trees |
| `-e, --extended` | off | Build trees for all markers; turns fast mode off |
| `--sensitive` | on | HMM search at `E=1e-5`, `domE=1e-5`, no GA cutoffs |
| `--completeness-mode` | `novelty-aware` | `legacy` or `novelty-aware` |
| `--species-tree` | off | Build a concatenated-marker species tree per query |
| `-C, --contigs` | off | Classify each contig of an FNA as its own query |
| `--min-length` | 20000 | Minimum total length for bin/MAG `.fna` inputs; `0` removes the floor |
| `--contigs-min-length` | 10000 | Minimum contig length with `--contigs` |
| `--resume` | off | Skip queries already completed in `run_status.json` |
| `--plain-output` | off | Disable emoji and ANSI colors in logs |

The `--cluster-*` flags are parsed but have no effect. Submit one GVClass run as one batch job.

## Common Usage Examples

### Directory of bins
```bash
pixi run gvclass my_bins -o my_results -t 16
```

### HPC run, four genomes in parallel with four threads each
```bash
./gvclass-a my_bins results -t 16 -j 4
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
- A directory of `.fna` or `.faa` files (also `.fasta`, `.fas`), one file per putative genome; bins are the intended input.
- For giant-virus discovery from contigs, filter to 30 kb or more (50 kb preferred).
- Files with the same stem (`sample.fna` and `sample.faa`) are rejected.

### Run-level output

| File | Contents |
|------|----------|
| `gvclass_summary.tsv` / `.csv` | One row per query, 44 columns |
| `gvclass_summary.extended.tar.gz` | Per-contig contamination diagnostics |
| `gvclass_failed_queries.tsv` | Written only when queries fail; the run then exits non-zero |
| `run_status.json` | Versions, settings, per-query status, and checksums; used by `--resume` |
| `run.log` | Chronological run log |
| `<query>.tar.gz` | Per-query trees and summaries |

### Key Summary Columns

| Column | Description |
|--------|-------------|
| `taxonomy_majority` | Lineage from the per-marker nearest-neighbor majority vote |
| `taxonomy_confidence` | `high`, or one or more of `low_support`, `reduced_fastmode`, `no_support` |
| `species` ... `domain` | Per-rank calls with per-taxon counts |
| `avgdist` | Average tree distance to the reference neighbors |
| `estimated_completeness` | Completeness for the assigned lineage |
| `completeness_model_reliability` | `advisory_only`, `moderate`, or `high`; a property of the model, not the genome |
| `estimated_contamination` | Primary contamination estimate |
| `contamination_type` | `clean`, `cellular`, `mixed_viral`, `phage`, `duplication`, or `uncertain` when contamination is 10 or more |
| `order_dup`, `gvog8_dup` | Marker duplication factors; near 1 for one clean genome |
| `gvog4_completeness`, `gvog8_completeness` | Core NCLDV markers present as `n/4` and `n/8` |
| `busco_completeness`, `cog_completeness` and their `_dup` | Cellular marker panels; high duplication flags cellular carry-over |
| `capsid_group` | Capsid-type tally across NCLDV, Mirusviricota, and PPV capsid groups |
| `LENbp`, `GCperc`, `genecount`, `CODINGperc`, `ttable` | Genome statistics and the genetic code used |

The column reference lists all 44: https://NeLLi-team.github.io/gvclass/reference/output/

## Quality Interpretation

- Read `taxonomy_confidence` with the duplication columns; duplicated markers inflate vote counts without adding independent evidence.
- `reduced_fastmode` means order resolution rests on the core markers; rerun with `--extended` when order-level placement matters.
- `order_dup` or `gvog8_dup` above about 2 points to multiple populations, a chimera, or a mixed bin.
- Elevated `busco_dup` or `cog_dup` points to cellular sequence in the bin.
- A high `avgdist` can mean a novel lineage or a poor-quality query; separate the two with completeness and duplication.
- Treat `estimated_completeness` as advisory when `completeness_model_reliability` is `advisory_only`.

## Integration with Viromics Workflow

1. Input: bins or long contigs routed as giant-virus candidates by QuickClade or geNomad.
2. Analysis: per-marker phylogenetic placement and quality models.
3. Output: taxonomy, completeness, contamination, and duplication metrics.
4. Follow with core-gene phylogenies in `/bio-phylogenomics` for placement claims beyond the nearest reference.

## Troubleshooting

- **Run exits non-zero after finishing**: one or more queries failed; read `gvclass_failed_queries.tsv`.
- **Query skipped as too short**: lower `--min-length` or `--contigs-min-length` only when the shorter sequences are wanted.
- **No taxonomy assigned**: the query is too short, too divergent, or not a giant virus.
- **Memory errors**: lower `--max-workers`.
