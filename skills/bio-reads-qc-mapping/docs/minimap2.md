# minimap2 v2.31 - Versatile Sequence Aligner

Last verified: 2026-05-30
Tool version/release checked: minimap2 v2.31 (GitHub release page)
Official docs/manual: https://lh3.github.io/minimap2/minimap2.html
Release/source: https://github.com/lh3/minimap2/releases/tag/v2.31

## Overview

Minimap2 is a versatile pairwise aligner for genomic and spliced nucleotide sequences. It works with DNA or mRNA sequences against a large reference database and is optimized for mapping long reads (PacBio/Nanopore), finding overlaps between long reads, and aligning Illumina reads.

## Official Documentation

- [minimap2 GitHub Repository](https://github.com/lh3/minimap2)
- [minimap2 Manual Page](https://lh3.github.io/minimap2/minimap2.html)
- [minimap2 Cookbook](https://github.com/lh3/minimap2/blob/master/cookbook.md)
- [minimap2 v2.31 Release](https://github.com/lh3/minimap2/releases/tag/v2.31)

## Installation

```bash
# Add to the project Pixi environment
pixi add minimap2

# From source
git clone https://github.com/lh3/minimap2
cd minimap2
git checkout v2.31
make
```

## Key Command-Line Flags

### Basic Syntax
```bash
minimap2 [options] <target.fa|target.mmi> [query.fa] [...]
```

### Preset Options (-x)
- `-x map-pb` - PacBio CLR reads vs reference (k=19)
- `-x map-ont` - Oxford Nanopore reads vs reference (k=15)
- `-x map-hifi` - PacBio HiFi reads vs reference (k=19)
- `-x sr` - Short single-end reads vs reference
- `-x splice` - Long RNA-seq reads vs reference
- `-x splice:hq` - High-quality RNA-seq (PacBio Iso-Seq/traditional cDNA)
- `-x asm5` - Assembly to reference mapping (asm5/asm10/asm20 for divergence)
- `-x ava-pb` - PacBio all-vs-all overlap
- `-x ava-ont` - ONT all-vs-all overlap

### Input/Output Options
- `-a` - Output in SAM format (default is PAF)
- `-o <file>` - Output file (default: stdout)
- `-t <int>` - Number of threads (default: 3)
- `-d <file>` - Save index to file
- `--split-prefix <str>` - Prefix for split index files

### Alignment Parameters
- `-k <int>` - Kmer size (default varies by preset)
- `-w <int>` - Minimizer window size (default varies by preset)
- `-I <num>` - Maximum number of target bases per index batch (default: 8G bases); this is not a byte-valued RAM limit
- `-f <float>` - Filter out top fraction of repetitive minimizers
- `-g <int>` - Stop chain elongation if there are no minimizers within INT bp (default: 10k)

### Output Control
- `--cs[=STR]` - Output cs tag; STR is 'short' (default) or 'long'
- `-c` - Output CIGAR in PAF format
- `--MD` - Output MD tag for SAM output
- `-Y` - Use soft clipping for supplementary alignments
- `--eqx` - Output =/X CIGAR operators for match/mismatch

### Mapping Sensitivity
- `-N <int>` - Retain at most INT secondary alignments (default: 5)
- `-p <float>` - Minimum score ratio for retaining a secondary alignment relative to its primary alignment (default: 0.8); it does not filter alignment identity
- `-r <int>` - Bandwidth for chaining and alignment, as `INT1[,INT2]`: INT1 for initial chaining and extension, INT2 for re-chaining and closing gaps (default: 500,20k)
- `-n <int>` - Minimum number of minimizers on chain (default: 3)
- `-m <int>` - Minimum chain score (default: 40)

### Spliced Alignment (RNA-seq)
- `-u <mode>` - Splice mode: f (forward), b (reverse), n (non-canonical)
- `-G <int>` - Maximum intron size (default: 200k)
- `--junc-bed <file>` - Junction BED file for known splice sites

## Common Usage Examples

### Map Oxford Nanopore Reads

```bash
minimap2 -ax map-ont reference.fa reads.fq > output.sam
```

### Map PacBio CLR Reads

```bash
minimap2 -ax map-pb reference.fa reads.fq > output.sam
```

### Map PacBio HiFi Reads

```bash
minimap2 -ax map-hifi reference.fa reads.fq > output.sam
```

### Map Illumina Short Reads (Paired-End)

```bash
minimap2 -ax sr reference.fa read1.fq read2.fq > output.sam
```

### RNA-Seq Spliced Alignment

```bash
minimap2 -ax splice -uf -k14 reference.fa rna_reads.fq > output.sam
```

### Create and Use Index

```bash
# Build index
minimap2 -d reference.mmi reference.fa

# Map using index
minimap2 -ax map-ont reference.mmi reads.fq > output.sam
```

### Map with Multiple Threads

```bash
minimap2 -ax map-ont -t 16 reference.fa reads.fq > output.sam
```

### Output PAF Format (Default)

```bash
minimap2 -x map-ont reference.fa reads.fq > output.paf
```

### Map with cs Tag (for Variant Calling)

```bash
minimap2 -ax map-ont --cs reference.fa reads.fq > output.sam
```

### All-vs-All Overlap (for Assembly)

```bash
minimap2 -x ava-ont reads.fq reads.fq > overlaps.paf
```

### Assembly-to-Reference Alignment

```bash
minimap2 -ax asm5 reference.fa assembly.fa > alignment.sam
```

## Input/Output Formats

### Input Formats
- FASTA (gzipped or uncompressed)
- FASTQ (gzipped or uncompressed)
- Pre-built minimap2 index (.mmi)

### Output Formats
- **PAF** (Pairwise mApping Format) - Default, tab-delimited
  - Lightweight format for long-read alignments
  - Columns: query name, length, start, end, strand, target name, length, start, end, matches, alignment length, mapping quality
- **SAM** (Sequence Alignment Map) - With `-a` flag
  - Standard alignment format compatible with downstream tools

### Index Files
- `.mmi` - Minimap2 index file
- Can be created with `-d` flag
- Speeds up repeated mappings against same reference

## Performance Tips

### Memory Management
- `-I 8G` indexes at most 8 billion target bases per batch, not 8 GB of RAM.
- Lowering `-I` can reduce peak indexing memory by creating a multi-part index. Minimap2 warns that mapping quality is incorrect when it maps against a multi-part index because it cannot compare hits across all target batches.
- Pre-build an index with `-d` to avoid rebuilding it on repeated runs; measure resident memory on the target dataset rather than treating the index file size or `-I` value as a RAM estimate.

### Threading
- Minimap2 scales well with multiple threads
- Optimal: 8-16 threads for most datasets
- Use `-t` to specify thread count
- Example: `-t 16`

### Speed Optimization
- Use appropriate presets (`-x`) for your data type
- Pre-build index for large references used repeatedly
- Use `-I` to split a large target into index batches only when the multi-part-index mapping-quality limitation is acceptable
- Skip secondary alignments with `-N 0` if not needed

### Disk I/O
- Process gzipped files directly (no decompression needed)
- Pipe output to samtools to compress SAM on-the-fly
- Use PAF format instead of SAM when possible (smaller file size)

### Index Optimization
- Build index once for repeated mapping jobs
- Targets longer than the `-I` base limit are split into multiple index batches
- Use `--split-prefix` to control split index file naming

## Parameter Recommendations

### Oxford Nanopore Genomic DNA
```bash
minimap2 -ax map-ont -t 16 reference.fa reads.fq
```

### PacBio HiFi High-Accuracy Reads
```bash
minimap2 -ax map-hifi -t 16 reference.fa reads.fq
```

### PacBio CLR Long Reads
```bash
minimap2 -ax map-pb -t 16 reference.fa reads.fq
```

### Illumina Short Reads
```bash
minimap2 -ax sr -t 16 reference.fa read1.fq read2.fq
```

### Nanopore RNA-Seq (cDNA)
```bash
minimap2 -ax splice -uf -k14 -t 16 reference.fa reads.fq
```

### Approximate Alignment Identity Filtering (>=95% in PAF)
```bash
minimap2 -x map-ont -t 16 --secondary=no reference.fa reads.fq | \
  awk 'BEGIN { OFS="\t" } $11 > 0 && ($10 / $11) >= 0.95'
```

PAF column 10 is the number of matching bases and column 11 is the alignment block length. This ratio is a convenient PAF-level approximation, not a substitute for a variant-aware identity calculation. The `-p` option controls secondary-alignment score filtering and must not be used as an identity threshold.

### Assembly Alignment (5% divergence)
```bash
minimap2 -ax asm5 reference.fa assembly.fa
```

## Preset Details

| Preset | Use Case | Key Parameters |
|--------|----------|----------------|
| map-pb | PacBio CLR | k=19, w=19 |
| map-ont | ONT reads | k=15, w=10 |
| map-hifi | PacBio HiFi | k=19, w=19, higher accuracy |
| sr | Illumina | k=21, w=11 |
| splice | RNA-seq | Splice-aware, intron detection |
| asm5/10/20 | Assembly | 5%/10%/20% sequence divergence |

## Output Processing

### Convert to BAM and Sort

```bash
minimap2 -ax map-ont reference.fa reads.fq | \
  samtools sort -@ 4 -o output.bam
```

### Filter by Mapping Quality

```bash
minimap2 -ax map-ont reference.fa reads.fq | \
  samtools view -q 30 -b > filtered.bam
```

### Calculate Coverage

```bash
minimap2 -ax map-ont reference.fa reads.fq | \
  samtools sort | \
  samtools depth - > coverage.txt
```
