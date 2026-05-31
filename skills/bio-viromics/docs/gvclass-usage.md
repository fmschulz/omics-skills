# GVClass Usage Guide

Last verified: 2026-05-30
Tool version/release checked: GVClass v1.6.0 software; compatible runtime resource bundle v1.5.0
Official docs/manual: https://github.com/NeLLi-team/gvclass#readme
Release/source: https://github.com/NeLLi-team/gvclass/tree/v1.6.0 ; https://github.com/NeLLi-team/gvclass

## Official Documentation
- GitHub: https://github.com/NeLLi-team/gvclass
- Publication: "Conservative taxonomy and quality assessment of giant virus genomes with GVClass." npj Viruses (2024), DOI: 10.1038/s44298-024-00069-7

## Overview
GVClass is a specialized tool for identifying giant viruses (Nucleocytoviricota) in sequence data. It assigns taxonomy with GVOG-based phylogenetic analysis and reports quality metrics. Current upstream guidance treats genus/species labels as nearest-reference labels unless the query is very close to an existing reference.

## Installation

### Pixi (Local/Development)
```bash
curl -fsSL https://pixi.sh/install.sh | bash
git clone https://github.com/NeLLi-team/gvclass.git
cd gvclass
pixi install
pixi run setup-db
```

### Apptainer/Singularity (HPC - Recommended)
```bash
wget https://raw.githubusercontent.com/NeLLi-team/gvclass/main/gvclass-a
chmod +x gvclass-a
```

The Apptainer image includes the database (~700MB) and dependencies.

## Key Commands & Flags

### Basic Command Structure

**Pixi:**
```bash
pixi run gvclass INPUT_DIR -o OUTPUT_DIR [OPTIONS]
```

**Apptainer:**
```bash
./gvclass-a INPUT_DIR OUTPUT_DIR [OPTIONS]
```

### Command-Line Options

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--threads` | `-t` | Total CPU threads | 16 |
| `--max-workers` | `-j` | Parallel workers | Auto |
| `--output-dir` | `-o` | Output directory | `<input>_results` |
| `--tree-method` | - | Tree builder: `fasttree` or `iqtree` | fasttree |
| `--mode-fast` | `-f` | Skip order-level markers (2-3x faster) | False |
| `--extended` | `-e` | Include all marker trees in output | False |
| `--contigs` | `-C` | Classify individual contigs separately | False |
| `--sensitive` | - | Sensitive HMM search mode using E-value 1e-5 | Default behavior in current resources |
| `--resume` | - | Continue interrupted run | False |
| `--verbose` | `-v` | Enable debug output | False |
| `--database` | `-d` | Override default database path | Auto |

## Common Usage Examples

### Basic analysis
```bash
pixi run gvclass my_genomes -o my_results -t 32
```

### Fast mode (recommended for large datasets)
```bash
./gvclass-a my_genomes results -t 32 --mode-fast
```

### High-accuracy mode with IQ-TREE
```bash
pixi run gvclass my_genomes -t 32 --tree-method iqtree
```

### Classify individual contigs from assembly
```bash
pixi run gvclass --contigs assembled_contigs.fna -o results -t 32
```

### Sensitive HMM search mode
```bash
pixi run gvclass my_genomes -o my_results -t 32 --sensitive
```

### Control parallelization (4 workers × 8 threads each)
```bash
./gvclass-a data results -t 32 -j 4
```

### Resume interrupted analysis
```bash
pixi run gvclass my_genomes -o my_results --resume
```

### Extended output with all trees
```bash
./gvclass-a genomes results -t 32 --extended
```

## Input/Output

### Input Requirements

**File formats:**
- `.fna` (nucleic acid FASTA)
- `.faa` (protein FASTA)

**Recommendations:**
- Minimum length: 20kb (50kb+ preferred for accuracy)
- Clean filenames: avoid special characters (`;`, `:`)
- Protein headers: format as `filename|proteinid`
- Input as directory containing multiple genome files
- GVClass works best on bins/GVMAGs; use `--contigs` when treating contigs in a multi-contig FASTA as independent genomes

### Output Structure

Results saved to `<input_name>_results/` containing:

**Main output files:**
- `gvclass_summary.tsv` - Tab-separated taxonomy assignments
- `gvclass_summary.csv` - Spreadsheet-compatible format
- Individual query subdirectories with detailed phylogenetic analysis

### Key Output Columns

| Column | Description |
|--------|-------------|
| `taxonomy_majority` | Full taxonomic lineage (majority rule) |
| `taxonomy_strict` | Conservative taxonomy (strict consensus) |
| `estimated_completeness` | Estimated percentage of the expected genome recovered |
| `estimated_contamination` | Estimated percentage of assembly likely to represent contaminant or mixed-origin sequence |
| `contamination_type` | High-level contamination interpretation when contamination is elevated |
| `order_dup` | Average copy number of expected order-level markers; elevated values suggest duplicated, chimeric, or mixed bins |
| `gvog8_unique` | Unique GVOG8 core markers found |
| `gvog8_total` | Total GVOG8 markers (including duplicates) |
| `gvog8_dup` | GVOG8 duplication level |
| `weighted_order_completeness` | Conservation-weighted completeness |
| `avgdist` | Average phylogenetic distance to references |
| `LENbp`, `GCperc`, `genecount`, `CODINGperc`, `ttable` | Basic genome statistics and gene-calling metadata |

## Performance Tips

1. **Use fast mode** (`--mode-fast`) for large datasets - provides 2-3x speedup
2. **Optimize threading**: Total threads = workers × threads per worker
3. **FastTree vs IQ-TREE**: FastTree is faster, IQ-TREE is more accurate
4. **Pre-filter sequences**: Remove contigs <20kb before analysis
5. **Use Apptainer on HPC**: Includes all dependencies and database
6. **Resume capability**: Use `--resume` for interrupted runs on large datasets
7. **Contig mode**: Use `-C` only when analyzing individual contigs from assemblies

## Quality Interpretation

**Completeness interpretation:**
- Higher `estimated_completeness` supports more confident taxonomy, but final confidence depends on marker support and distance to references.
- Use low-completeness results cautiously and report the likely rank limit.

**Contamination indicators:**
- Elevated `estimated_contamination`: inspect `contamination_type` and any per-query contamination candidate tables
- `order_dup` or `gvog8_dup` >1: check for co-assemblies, mixed bins, or duplicated marker sets
- High `avgdist`: May indicate novel lineage or poor quality

## Integration with Viromics Workflow

GVClass is specialized for giant virus (NCLDV) detection and classification:
1. **Input**: Contigs from assembly or viral detection tools
2. **Analysis**: Phylogenetic placement using GVOG markers
3. **Output**: Taxonomic assignment and quality metrics
4. **Use case**: Complement to geNomad for focused NCLDV analysis
5. **Integration**: Can be run in parallel with or after general viral detection

## Global Installation (Optional)

### Apptainer wrapper
```bash
mkdir -p "$HOME/bin"
cp gvclass-a "$HOME/bin/"
chmod +x "$HOME/bin/gvclass-a"
echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.bashrc"
```

### Pixi wrapper
```bash
cd /path/to/gvclass
ln -s "$(pwd)/gvclass" "$HOME/bin/gvclass"
```

## Configuration File

Create `gvclass_config.yaml` for custom defaults:
```yaml
database:
  path: resources
  download_url: https://zenodo.org/records/19674504/files/resources_v1_5_0.tar.gz?download=1
  download_version: v1.5.0

pipeline:
  tree_method: fasttree
  mode_fast: false
  completeness_mode: novelty-aware
  sensitive_mode: true
  threads: 16
```

## Troubleshooting

- **Low completeness**: May indicate non-giant virus or novel lineage
- **High duplication**: Check for contamination or co-assembled genomes
- **No taxonomy assigned**: Sequence may be too short or divergent
- **Memory errors**: Reduce `--max-workers` or increase available RAM
- **IQ-TREE failures**: Fall back to FastTree or check input quality
