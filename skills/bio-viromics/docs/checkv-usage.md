# CheckV Usage Guide

Last verified: 2026-10-01
Tool version/release checked: CheckV v1.1.1 (`checkv --help` and source from bioconda); database v1.5 from `CURRENT_RELEASE.txt` on the NERSC archive
Official docs/manual: https://bitbucket.org/berkeleylab/checkv
Release/source: https://pypi.org/project/checkv/ ; https://bitbucket.org/berkeleylab/checkv

## Official Documentation
- Bitbucket: https://bitbucket.org/berkeleylab/checkv
- PyPI: https://pypi.org/project/checkv/
- Database archive and changelog: https://portal.nersc.gov/CheckV/
- Citation: Nayfach et al. (2020) *Nature Biotechnology* https://doi.org/10.1038/s41587-020-00774-7

## Overview
CheckV assesses single-contig viral genomes: it identifies closed genomes, estimates completeness of fragments, and trims flanking host regions from integrated proviruses.

## Installation

```bash
pixi add checkv
```

With a PyPI install, provide the external dependencies upstream tested separately: DIAMOND v2.2.0 (upstream flags v2.1.9 as a core-dump risk) and HMMER v3.3.

## Database Setup

```bash
checkv download_database ./
export CHECKVDB=/path/to/checkv-db-v1.5
```

`download_database` fetches the release named in `https://portal.nersc.gov/CheckV/CURRENT_RELEASE.txt` (`checkv-db-v1.5` at verification time).

Add your own complete viral genomes to a copy of the database:
```bash
checkv update_database /path/to/checkv-db /path/to/updated-checkv-db genomes.fna
```

## Key Commands & Flags

```bash
checkv end_to_end [OPTIONS] INPUT OUTPUT
```

| Command | Purpose |
|---------|---------|
| `checkv end_to_end` | Full pipeline |
| `checkv contamination` | Identify and remove host contamination on proviruses |
| `checkv completeness` | Estimate completeness |
| `checkv complete_genomes` | Identify closed genomes from terminal repeats |
| `checkv quality_summary` | Summarize results across modules |

| Flag | Description |
|------|-------------|
| `-d PATH` | Database path. Defaults to `$CHECKVDB`. There is no long form. |
| `-t INT` | Threads. Default: the number of CPUs available to the process; set it to the allocated CPU count. |
| `--remove_tmp` | Delete intermediate files from the output directory. |
| `--restart` | Overwrite existing intermediate files. By default CheckV continues where it left off. |
| `--quiet` | Suppress logging. |
| `--conservative-trimming` | Identify fewer host regions during contamination trimming. |
| `--aggressive-trimming` | Identify more host regions during contamination trimming. |

## Common Usage Examples

### Standard quality assessment
```bash
checkv end_to_end viral_contigs.fna output_dir -t 16 -d /path/to/checkv-db-v1.5
```

### Individual modules
```bash
checkv contamination viral_contigs.fna output_dir -t 16
checkv completeness viral_contigs.fna output_dir -t 16
checkv complete_genomes viral_contigs.fna output_dir
checkv quality_summary viral_contigs.fna output_dir
```

## Input/Output

### Input
- Nucleotide FASTA of viral contigs, usually from geNomad or VirSorter2

### Key Output Files

| File | Description |
|------|-------------|
| `quality_summary.tsv` | Integrated results with quality tiers (primary output) |
| `completeness.tsv` | Completeness estimates per contig |
| `contamination.tsv` | Host contamination and trimmed coordinates |
| `complete_genomes.tsv` | Predicted closed genomes |
| `proviruses.fna` | Proviruses with host regions removed |
| `viruses.fna` | Sequences without host regions |

### Quality Tiers

`quality_summary.tsv` has a `checkv_quality` column and a `miuvig_quality` column. The tiers in source:

| `checkv_quality` | Rule | `miuvig_quality` |
|------------------|------|------------------|
| Complete | Closed-genome prediction (for example direct or inverted terminal repeats) at medium or high confidence | High-quality |
| High-quality | Completeness 90% or more | High-quality |
| Medium-quality | Completeness 50% to under 90% | Genome-fragment |
| Low-quality | Completeness under 50% | Genome-fragment |
| Not-determined | No completeness estimate | Genome-fragment |

## Performance Tips

1. Set `-t` to the allocated CPU count.
2. Pre-filter contigs by length when the project allows it; short fragments rarely get a completeness estimate.
3. Rerun the same command to resume an interrupted run; add `--restart` only to start over.
4. Set `CHECKVDB` so the database path is not repeated.

## Integration with Viromics Workflow

1. Input: viral contigs from geNomad or VirSorter2.
2. Output: quality tiers, completeness, and host-trimmed sequences.
3. Downstream: high- and medium-quality genomes go to vConTACT3 or group-specific comparison.
4. Filtering: apply the project's thresholds and report sequences that fail them.

## Troubleshooting

- **Low completeness**: the genome may be a fragment, or the lineage may be poorly represented in the database.
- **High contamination**: check the provirus calls; curate boundaries by hand when needed.
- **Not-determined tier**: the sequence is too divergent from the database for an estimate.
- **DIAMOND errors**: check the DIAMOND version; upstream tested v2.2.0 and documents v2.1.9 as problematic.
