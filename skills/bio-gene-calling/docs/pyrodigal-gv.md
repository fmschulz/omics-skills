# pyrodigal-gv

Last verified: 2026-05-30
Tool version/release checked: pyrodigal-gv v0.3.2; bundled prodigal-gv model set `PRODIGAL_GV_VERSION` v2.11.0
Official docs/manual: https://github.com/althonos/pyrodigal-gv#readme
Release/source: https://github.com/althonos/pyrodigal-gv/releases/tag/v0.3.2 ; https://github.com/althonos/pyrodigal-gv

Pyrodigal extension for viral gene calling, including giant viruses and viruses with alternative genetic codes. Use the `pyrodigal-gv` CLI or `pyrodigal_gv.ViralGeneFinder`; do not document new workflows around the standalone `prodigal-gv` C binary.

## Official Documentation
- GitHub: https://github.com/althonos/pyrodigal-gv
- PyPI: https://pypi.org/project/pyrodigal-gv/
- Base Pyrodigal CLI/output docs: https://pyrodigal.readthedocs.io/en/stable/

## Installation

```bash
# uv/pip
uv pip install pyrodigal-gv
pip install pyrodigal-gv

# Conda/Bioconda, when using a conda-style environment
conda install -c bioconda pyrodigal-gv
```

## Key Features

- Python module extending Pyrodigal with the prodigal-gv viral metagenomic model set
- `pyrodigal-gv` CLI based on the Pyrodigal CLI
- CLI runs in metagenomic mode by default
- `pyrodigal_gv.ViralGeneFinder` for Python workflows
- Optional `viral_only=True` in Python to restrict metagenomic model selection to viral models
- 10 additional metagenomic models for viruses
- Optimized for giant viruses (mimiviruses, chlorella viruses)
- Supports alternative genetic codes (11 and 15)
- Specialized models for gut phages and NCLDV
- Compatible with Pyrodigal output writers

## Command-Line Flags

```bash
pyrodigal-gv [options] -i input.fna -a proteins.faa
```

**Common Options:**
- `-p meta` - Metagenomic mode; default for `pyrodigal-gv`
- `-p single` - Single-genome mode; behaves like Pyrodigal and normally is not useful for viral model selection
- `-i FILE` - Input sequence file (FASTA)
- `-a FILE` - Output protein sequences
- `-d FILE` - Output DNA sequences of genes
- `-o FILE` - Output gene coordinates
- `-f FORMAT` - Output coordinate format, for example `gff`
- `-j/--jobs N` - Parallel jobs for multi-sequence inputs

## Common Usage Examples

### Standard Viral Gene Calling

```bash
pyrodigal-gv \
  -i viral_genome.fna \
  -o genes.gff \
  -f gff \
  -a proteins.faa \
  -d cds.fna \
  -j 8
```

### Generate All Output Formats

```bash
pyrodigal-gv \
  -i genome.fna \
  -a proteins.faa \
  -d cds.fna \
  -o genes.gff \
  -f gff \
  -s scores.sco
```

### Python API

```python
import pyrodigal_gv

finder = pyrodigal_gv.ViralGeneFinder(meta=True, viral_only=True)
genes = finder.find_genes(sequence_bytes)

with open("proteins.faa", "w") as dst:
    genes.write_translations(dst, sequence_id="viral_contig_1")

with open("genes.gff", "w") as dst:
    genes.write_gff(dst, sequence_id="viral_contig_1", header=True)
```

## Input/Output Formats

**Input:**
- FASTA nucleotide sequences (.fna, .fasta)
- DNA sequences (single or multi-FASTA)

**Output:**
- Gene coordinates via `-o` and `-f`
- Protein sequences in FASTA (via `-a`)
- Gene nucleotide sequences in FASTA (via `-d`)
- Potential-gene scores via `-s`
- Python `Genes` objects with the same writer methods as Pyrodigal

## Viral Model Set

**Additional Metagenomic Models:**
1. Giant viruses (mimivirus-like)
2. Chlorella viruses
3. Alternative genetic codes (11, 15)
4. Gut phage optimizations
5. NCLDV (nucleo-cytoplasmic large DNA viruses)

These models improve gene calling accuracy for non-standard viral genomes.

## Performance Tips

- Use the default `pyrodigal-gv` metagenomic mode for viral genomes
- Use `-j/--jobs` for large multi-FASTA inputs
- Models automatically selected based on GC content
- No training required in metagenomic mode
- Use Python `viral_only=True` when you explicitly want to exclude non-viral Pyrodigal metagenomic bins
