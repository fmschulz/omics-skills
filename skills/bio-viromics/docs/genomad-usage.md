# geNomad Usage Guide

Last verified: 2026-10-01
Tool version/release checked: geNomad v1.12.0 (`genomad --help` from bioconda); geNomad database v1.9 listed in the official NERSC database index
Official docs/manual: https://portal.nersc.gov/genomad/
Release/source: https://github.com/apcamargo/genomad/releases/tag/v1.12.0 ; https://github.com/apcamargo/genomad

## Official Documentation
- Primary: https://portal.nersc.gov/genomad/
- GitHub: https://github.com/apcamargo/genomad
- Citation: Camargo et al. (2023) *Nature Biotechnology* https://doi.org/10.1038/s41587-023-01953-y

## Overview
geNomad identifies virus and plasmid sequences in nucleotide FASTA, finds proviruses inside host contigs, assigns ICTV taxonomy to viruses, and annotates genes with its marker database.

## Installation

```bash
pixi add genomad
```

Docker (upstream image):
```bash
docker pull antoniopcamargo/genomad
docker run --rm -ti -v "$(pwd):/app" antoniopcamargo/genomad
```

## Database Setup

```bash
genomad download-database .
```

`download-database` fetches the latest database into `genomad_db/`. The NERSC index listed database v1.9 at verification time. Record the version from the database directory in the run manifest.

## Key Commands & Flags

```bash
genomad end-to-end [OPTIONS] INPUT OUTPUT DATABASE
```

| Flag | Description |
|------|-------------|
| `-t, --threads` | Threads to use. Default: the number of CPUs available to the process; set it to the allocated CPU count. |
| `--cleanup` | Delete intermediate files after the run. |
| `--restart` | Overwrite existing intermediate files. By default geNomad resumes. |
| `--splits N` | Split the MMseqs2 search into N chunks to lower memory use. Default 0. |
| `--sensitivity, -s` | MMseqs2 marker search sensitivity. Default 4.2. |
| `--conservative` | Stricter post-classification filters. |
| `--relaxed` | Disable all post-classification filters. |
| `--enable-score-calibration` | Run score calibration; required for `--max-fdr` to take effect. |
| `--max-fdr FLOAT` | Maximum false discovery rate. Ignored unless scores were calibrated. Default 0.1. |
| `--lenient-taxonomy` | Allow virus taxonomy below family (subfamily, genus, subgenus, species). |
| `--full-ictv-lineage` | Report hidden ICTV ranks. Subfamily and subgenus appear only with `--lenient-taxonomy`. |

`--conservative` and `--relaxed` cannot be combined with explicit thresholds such as `--min-score`, `--max-fdr`, `--min-number-genes`, or `--max-uscg`.

## Common Usage Examples

### Basic viral detection
```bash
genomad end-to-end -t 16 --cleanup input.fna.gz output_dir genomad_db
```

### Lower memory use
```bash
genomad end-to-end -t 16 --cleanup --splits 8 input.fna.gz output_dir genomad_db
```

### Stricter filters
```bash
genomad end-to-end -t 16 --conservative --cleanup input.fna.gz output_dir genomad_db
```

### Calibrated scores with an FDR cutoff
```bash
genomad end-to-end -t 16 --enable-score-calibration --max-fdr 0.05 \
  input.fna.gz output_dir genomad_db
```

### Full ICTV lineage below family
```bash
genomad end-to-end -t 16 --full-ictv-lineage --lenient-taxonomy --cleanup \
  input.fna.gz output_dir genomad_db
```

## Input/Output

### Input
- Nucleotide FASTA: isolate genomes, metagenome assemblies, metatranscriptome assemblies
- Compressed `.gz`, `.bz2`, `.xz`; v1.11.2 added `.zst` on Python versions with Zstandard support

### Output
`<prefix>` is the input file name without extensions. The summary directory `output_dir/<prefix>_summary/` holds:

| File | Contents |
|------|----------|
| `<prefix>_virus_summary.tsv` | One row per virus: coordinates for proviruses, score, FDR when calibrated, hallmark count, taxonomy |
| `<prefix>_virus.fna` | Virus sequences, with proviruses excised |
| `<prefix>_virus_proteins.faa` | Proteins encoded by the viruses |
| `<prefix>_virus_genes.tsv` | Per-gene annotation |
| `<prefix>_plasmid_summary.tsv`, `<prefix>_plasmid.fna`, `<prefix>_plasmid_proteins.faa`, `<prefix>_plasmid_genes.tsv` | The same for plasmids |
| `<prefix>_summary.json` | Run summary |

## Performance Tips

1. Use `--splits` when the MMseqs2 search runs out of memory.
2. Use `--cleanup` to remove intermediate files.
3. Set `-t` to the CPUs you were allocated. The default is every CPU the process may run on, which is the whole node when the scheduler does not bind CPUs.
4. Use `--conservative` when false positives cost more than missed viruses, and `--relaxed` for exploratory screens followed by CheckV.

## Integration with Viromics Workflow

1. Detects candidate viral contigs and proviruses in the assembly.
2. Gives a first taxonomy for each virus.
3. Writes viral sequences for CheckV QC.
4. Provides gene annotations for the marker and family-copy comparisons.
