# Pyrodigal

Last verified: 2026-05-30
Tool version/release checked: Pyrodigal v3.7.1
Official docs/manual: https://pyrodigal.readthedocs.io/en/stable/
Release/source: https://github.com/althonos/pyrodigal/releases/tag/v3.7.1 ; https://github.com/althonos/pyrodigal

Python bindings and a command-line interface around Prodigal for fast prokaryotic gene finding.

## Official Documentation
- GitHub: https://github.com/althonos/pyrodigal
- Documentation: https://pyrodigal.readthedocs.io/
- CLI guide: https://pyrodigal.readthedocs.io/en/stable/guide/cli.html
- Output writer guide: https://pyrodigal.readthedocs.io/en/stable/guide/outputs.html

## Installation

```bash
# uv/pip
uv pip install pyrodigal
pip install pyrodigal

# Conda/Bioconda, when using a conda-style environment
conda install -c bioconda pyrodigal
```

Pre-built wheels are published on PyPI. Use the version bundled by the active pixi or conda environment when reproducibility matters.

## Key Features

- Python API plus `pyrodigal` CLI
- CLI is a near drop-in replacement for `prodigal` on FASTA input
- Thread-safe for parallel processing
- SIMD-accelerated (up to 50% faster than original Prodigal)
- No intermediate files
- In-memory processing
- Python output writers for CDS FASTA, protein FASTA, GFF3-like output, GenBank, and score files

## Command-Line Examples

### Metagenomic mode

```bash
pyrodigal \
  -p meta \
  -i contigs.fna \
  -o genes.gff \
  -f gff \
  -a proteins.faa \
  -d cds.fna \
  -j 8
```

### Single-genome mode with a training file

```bash
pyrodigal \
  -p single \
  -i genome.fna \
  -o genes.gff \
  -f gff \
  -a proteins.faa \
  -d cds.fna \
  -t training.trn
```

### Standard input

```bash
zcat contigs.fna.gz | pyrodigal -p meta -i - -o genes.gff -f gff -a proteins.faa
```

The CLI accepts FASTA input only. Stdin is supported, but compressed streams must be decompressed before piping.

## Python Usage Examples

### Metagenomic mode

```python
import pyrodigal

gene_finder = pyrodigal.GeneFinder(meta=True)
genes = gene_finder.find_genes(sequence_bytes)

for gene in genes:
    print(f">{gene.name}")
    print(gene.translate())
```

### Single mode

```python
gene_finder = pyrodigal.GeneFinder()
gene_finder.train(training_sequence)
genes = gene_finder.find_genes(sequence_bytes)
```

### Write standard output files from Python

```python
genes = gene_finder.find_genes(sequence_bytes)

with open("cds.fna", "w") as dst:
    genes.write_genes(dst, sequence_id="contig_1")

with open("proteins.faa", "w") as dst:
    genes.write_translations(dst, sequence_id="contig_1")

with open("genes.gff", "w") as dst:
    genes.write_gff(dst, sequence_id="contig_1", header=True)

with open("genes.gbk", "w") as dst:
    genes.write_genbank(dst, sequence_id="contig_1")

with open("scores.sco", "w") as dst:
    genes.write_scores(dst, sequence_id="contig_1")
```

### Parallel processing

```python
import multiprocessing.pool

gene_finder = pyrodigal.GeneFinder()
gene_finder.train(training_seq)

with multiprocessing.pool.ThreadPool() as pool:
    results = pool.map(gene_finder.find_genes, sequences)
```

## Input/Output Formats

**Input:**
- CLI: FASTA nucleotide sequences
- Python API: raw bytes or strings containing DNA sequence

**Output:**
- CLI: coordinate output via `-o`, proteins via `-a`, CDS via `-d`, scores via `-s`
- Python API: `Genes` objects with `.write_genes()`, `.write_translations()`, `.write_gff()`, `.write_genbank()`, `.write_scores()`
- Training data can be serialized and reused

## Key Parameters

- `meta=True` - Use metagenomic mode (pre-trained)
- `closed=True` - Ignore genes running off sequence edges
- `mask=True` - Prevent predictions across unknown nucleotides
- `translation_table` - Set genetic code (default: 11)
- `min_gene`, `min_edge_gene`, `max_overlap` - Control small-gene and overlap behavior in the API or matching CLI flags
- CLI `-j/--jobs` - Parallelize across multiple input sequences

## Performance Tips

- Use metagenomic mode for mixed communities
- Train once, reuse for similar genomes
- Leverage ThreadPool for parallel processing
- SIMD instructions provide 30-50% speedup
- In-memory operation eliminates I/O overhead
- Pre-allocates node arrays based on GC%
