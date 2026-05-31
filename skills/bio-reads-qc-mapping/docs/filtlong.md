# Filtlong v0.3.1 - Long Read Quality Filtering

Last verified: 2026-05-30
Tool version/release checked: Filtlong v0.3.1 (GitHub release)
Official docs/manual: https://github.com/rrwick/Filtlong/tree/v0.3.1#full-usage
Release/source: https://github.com/rrwick/Filtlong/releases/tag/v0.3.1

## Overview

Filtlong filters Nanopore or PacBio long-read FASTQ by read length and quality. Without an external reference it scores reads from FASTQ quality values; with an assembly or short-read reference it scores read identity through k-mer matches. In v0.3.0+, the old `--illumina_1`/`--illumina_2` long options were renamed to `--short_1`/`--short_2`, while `-1`/`-2` stayed valid. v0.3.1 adds short-form options and unit suffixes.

## Official Documentation

- [Filtlong GitHub Repository](https://github.com/rrwick/Filtlong)
- [Filtlong v0.3.1 README / full usage](https://github.com/rrwick/Filtlong/tree/v0.3.1#full-usage)
- [Filtlong v0.3.1 Release](https://github.com/rrwick/Filtlong/releases/tag/v0.3.1)

## Installation

```bash
# Via conda/mamba
conda install -c bioconda filtlong=0.3.1

# Via pixi
pixi add filtlong

# From source
git clone https://github.com/rrwick/Filtlong.git
cd Filtlong
git checkout v0.3.1
make
```

## Key Command-Line Flags

### Basic Syntax

```bash
filtlong [options] input.fastq.gz | gzip > output.fastq.gz
```

### Output Thresholds

- `-l, --min_length <int>` - Discard reads shorter than this length; supports `k`, `kb`, `m`, `mb`, `g`, `gb` suffixes.
- `-L, --max_length <int>` - Discard reads longer than this length; supports unit suffixes.
- `--keep_percent <float>` - Keep the best percent of input bases.
- `-t, --target_bases <int>` - Keep the best reads until this many bases remain; supports unit suffixes.
- `--min_mean_q <float>` - Discard reads below this mean quality.
- `--min_window_q <float>` - Discard reads with a low-quality window below this threshold.

### External References

- `-a, --assembly <file>` - Reference assembly in FASTA format.
- `-1, --short_1 <file>` - First short-read FASTQ reference file.
- `-2, --short_2 <file>` - Second short-read FASTQ reference file.

Avoid the pre-v0.3.0 long names `--illumina_1` and `--illumina_2`; use `--short_1` and `--short_2`. The short forms `-1` and `-2` are unchanged.

### Trimming

- `--trim` - With an external reference, trim non-k-mer-matching bases from read ends.
- `--split <int>` - With an external reference, split reads at this many consecutive non-k-mer-matching bases; supports unit suffixes.

### Score Weights

- `--length_weight <float>` - Weight for length score.
- `--mean_q_weight <float>` - Weight for mean quality score.
- `--window_q_weight <float>` - Weight for window quality score.

### Output Control

- `--window_size <int>` - Sliding window size for window-quality scoring.
- `--verbose` - Write filtering summary to stderr.
- `--version` - Display version and exit.

## Common Usage Examples

### Basic Length Filtering

```bash
filtlong --min_length 1000 input.fastq.gz | gzip > filtered.fastq.gz
```

### Keep Best Reads by Percentage

```bash
filtlong --keep_percent 90 input.fastq.gz | gzip > filtered.fastq.gz
```

### Target Specific Coverage

```bash
# Keep best reads totaling 500 Mbp.
filtlong --target_bases 500000000 input.fastq.gz | gzip > filtered.fastq.gz
```

### Quality-Based Filtering

```bash
filtlong --min_mean_q 10 --min_window_q 10 \
  input.fastq.gz | gzip > filtered.fastq.gz
```

### End Trimming Before Filtering

```bash
filtlong -1 short_R1.fastq.gz -2 short_R2.fastq.gz \
  --trim --min_length 1kb \
  input.fastq.gz | gzip > filtered.fastq.gz
```

### Short-Read-Assisted Filtering and Splitting

```bash
filtlong -1 short_R1.fastq.gz -2 short_R2.fastq.gz \
  --min_length 1kb \
  --target_bases 500mb \
  --trim \
  --split 500 \
  input.fastq.gz | gzip > filtered.fastq.gz
```

### Aggressive High-Quality Subset

```bash
filtlong \
  --min_length 5000 \
  --keep_percent 50 \
  --min_mean_q 12 \
  input.fastq.gz | gzip > filtered.fastq.gz
```

### Prefer Length Over Quality

```bash
filtlong --length_weight 2 --mean_q_weight 1 --window_q_weight 1 \
  input.fastq.gz | gzip > filtered.fastq.gz
```

## Input/Output Formats

### Input Formats

- FASTQ, gzip-compressed or uncompressed.
- Nanopore or PacBio long reads.
- Multiple files can be concatenated before filtering.

### Output Format

- FASTQ written to stdout; pipe to `gzip` for compressed output.

## Performance Tips

1. Filtlong is single-threaded.
2. Memory scales with total input bases because reads are scored before final selection.
3. Use `--target_bases` when you need a fixed assembly coverage target.
4. Use `--assembly` or `--short_1`/`--short_2` only when the reference is high quality and representative; poor short-read coverage or biological differences can make valid long reads look low quality.

## Scoring System

Filtlong v0.3.1 scores reads from:

1. **Length score** - Longer reads score higher.
2. **Mean quality score** - Higher average base quality scores higher; with an external reference this is inferred from reference k-mer matches instead of FASTQ qualities.
3. **Window quality score** - Reads with consistent high-quality windows score higher; `--window_size` controls the sliding window.

Adjust relative importance with the three score-weight flags:

```bash
# Emphasize length.
filtlong --length_weight 2 --mean_q_weight 1 --window_q_weight 1 input.fastq.gz

# Emphasize quality.
filtlong --length_weight 1 --mean_q_weight 3 --window_q_weight 3 input.fastq.gz
```

## Parameter Recommendations

### Nanopore Genomic DNA

```bash
filtlong --min_length 1000 --keep_percent 90
```

### Nanopore High-Quality Subset

```bash
filtlong --min_length 5000 --keep_percent 50 --min_mean_q 10
```

### PacBio CLR

```bash
filtlong --min_length 500 --keep_percent 90
```

### PacBio HiFi

```bash
filtlong --min_length 1000 --keep_percent 95 --min_mean_q 15
```

### Target Coverage

```bash
# 50x for a 100 Mbp genome.
filtlong --target_bases 5000000000 --min_length 1000
```

## Common Workflows

### Pre-Assembly Filtering

```bash
filtlong \
  --target_bases 5000000000 \
  --min_length 5000 \
  --verbose \
  raw_reads.fastq.gz | gzip > filtered_reads.fastq.gz
```

### Short-Read-Assisted Nanopore Cleanup

```bash
filtlong -1 short_R1.fastq.gz -2 short_R2.fastq.gz \
  --trim \
  --split 1kb \
  --min_length 1kb \
  nanopore_reads.fastq.gz | gzip > filtered_nanopore.fastq.gz
```

### Polishing Read Selection

```bash
filtlong \
  --min_length 1000 \
  --keep_percent 90 \
  reads.fastq.gz | gzip > polishing_reads.fastq.gz
```
