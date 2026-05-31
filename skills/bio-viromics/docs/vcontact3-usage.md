# vConTACT3 Usage Guide

Last verified: 2026-05-30
Tool version/release checked: vConTACT3 3.2.4 source tag; ReadTheDocs release notes list changes through v3.2.0
Official docs/manual: https://vcontact3.readthedocs.io/en/latest/
Release/source: https://bitbucket.org/MAVERICLab/vcontact3/commits/tag/3.2.4 ; https://bitbucket.org/MAVERICLab/vcontact3

## Official Documentation
- ReadTheDocs: https://vcontact3.readthedocs.io/
- Bitbucket: https://bitbucket.org/MAVERICLab/vcontact3

## Overview
vConTACT3 is a viral genome clustering and taxonomic assignment tool that improves upon previous versions through enhanced speed, scalability, and accuracy. It uses gene-sharing networks and protein cluster analysis for hierarchical viral classification.

## Installation

### Bioconda/Mamba (New Environment - Recommended)
```bash
mamba create --name vcontact3 python=3.11
mamba activate vcontact3
mamba install -c bioconda vcontact3
```

### Bioconda/Mamba (Base Environment)
```bash
mamba install -c bioconda vcontact3
```

Requires Python >=3.10 and <3.12.

### Pip Installation (Latest Version)
```bash
git clone https://bitbucket.org/MAVERICLab/vcontact3.git
cd vcontact3
python -m pip install .
```

Note: MMSeqs2 must be separately installed when using pip

### Requirements File Method
```bash
git clone https://bitbucket.org/MAVERICLab/vcontact3.git
cd vcontact3
mamba install -c bioconda --file requirements.txt
pip install .
```

### Optional: ANI Export Support
```bash
pip install vclust
```

## Key Commands & Flags

### Main Subcommands

| Command | Purpose |
|---------|---------|
| `vcontact3 version` | Display current version |
| `vcontact3 prepare_databases` | List, download, and setup reference databases |
| `vcontact3 run` | Perform clustering and taxonomic assignment |

### Run Command Options

| Flag | Description |
|------|-------------|
| `--nucleotide` | Input nucleotide sequence file (FASTA) |
| `--proteins` | Pre-predicted protein sequences (FASTA) |
| `--gene2genome` | Gene-to-genome mapping file (TSV) |
| `--len-nucleotide` | Genome length data (TSV) |
| `--output` | Output directory for results |
| `--db-path` | Path to a downloaded vConTACT3 database version or directory |
| `--db-domain` | Database domain selection (e.g., prokaryotes) |
| `--exports` | Optional output/export types, for example `graphml`, `cytoscape`, `profiles`, or `ani` |
| `--threads` | Number of threads for parallel processing |
| `--reduce-memory` | Downcast arrays to reduce memory use |
| `--max-iterations` | Mixed-realm component resolution iterations |
| `-h, --help` | Display help message |

## Common Usage Examples

### Basic nucleotide input workflow
```bash
vcontact3 prepare_databases --list-versions
vcontact3 prepare_databases --get-version latest --set-location ./vcontact3_db

vcontact3 run \
  --nucleotide genomes.fna \
  --db-path ./vcontact3_db \
  --db-domain prokaryotes \
  --output results_dir \
  --threads 32
```

### Protein-based workflow
```bash
vcontact3 run \
  --proteins proteins.faa \
  --gene2genome gene2genome.tsv \
  --len-nucleotide genome_lengths.tsv \
  --db-path ./vcontact3_db \
  --output results_dir
```

### Custom configuration with multiple exports
```bash
vcontact3 run \
  --nucleotide genomes.fna \
  --db-domain prokaryotes \
  --exports graphml cytoscape profiles \
  --output results_dir
```

### Database preparation
```bash
vcontact3 prepare_databases --list-versions
vcontact3 prepare_databases --get-version latest --set-location ./vcontact3_db
```

### Multi-threaded analysis
```bash
vcontact3 run \
  --nucleotide viral_genomes.fna \
  --output results \
  --threads 32
```

## Input/Output

### Input Formats

**Nucleotide mode:**
- FASTA file with viral genome sequences
- Simplest workflow for most users

**Protein mode (advanced):**
- `--proteins`: FASTA with predicted proteins
- `--gene2genome`: TSV mapping protein IDs to genome IDs
- `--len-nucleotide`: TSV with genome lengths

### Output Files

Located in specified output directory:
- **final_assignments.csv** - Main taxonomy and clustering assignments
- **network files** - GraphML/Cytoscape visualizations if requested with `--exports`
- **pc_profiles/** - Protein-cluster profiles when requested with `--exports profiles`
- **ANI matrices** - Genome similarity data (if vclust installed)
- Additional export-specific files, documented in the ReadTheDocs exports page

## Performance Tips

1. Use `--nucleotide` mode for simplest workflow
2. Increase `--threads` for large datasets
3. Use protein mode only if you have pre-computed gene calls
4. Install vclust for ANI-based similarity analysis
5. Limit export formats to only what you need to reduce runtime
6. Pre-filter low-quality genomes using CheckV before clustering
7. Use `--reduce-memory` for memory-constrained runs

## Integration with Viromics Workflow

vConTACT3 performs clustering and taxonomic assignment after quality control:
1. Input: High/medium quality viral genomes from CheckV
2. Analysis: Gene-sharing network construction and hierarchical clustering
3. Output: Genome clusters and taxonomic assignments
4. Downstream: Use clusters for diversity analysis and taxonomy for ecological interpretation

## Platform Compatibility

- Linux x86_64: Fully supported
- Intel Macs: Expected to work
- Apple Silicon: May require Rosetta terminal emulation or compilation from source

## Troubleshooting

- **Memory issues**: Reduce dataset size or use more powerful hardware
- **MMSeqs2 not found (pip install)**: Install MMSeqs2 separately from source
- **Python version errors**: Ensure Python 3.10 or 3.11 (not 3.12+)
- **Database errors**: Run `vcontact3 prepare_databases --list-versions` and `vcontact3 prepare_databases --get-version latest --set-location ./vcontact3_db`
