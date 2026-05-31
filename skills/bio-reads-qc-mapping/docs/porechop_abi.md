# Porechop_ABI 0.5.1 source / v0.5.0 tag - Legacy/Fallback Nanopore Adapter Trimming

Last verified: 2026-05-30
Tool version/release checked: source `__version__ = '0.5.1'` on master; latest GitHub tag v0.5.0
Official docs/manual: https://github.com/bonsai-team/Porechop_ABI
Release/source: https://github.com/bonsai-team/Porechop_ABI/tags and https://github.com/bonsai-team/Porechop_ABI/blob/master/porechop_abi/version.py

## Overview

Porechop_ABI is a targeted fallback for finding and removing Oxford Nanopore adapters when current basecaller/demultiplexer trimming is unavailable or when adapter discovery is part of the analysis question. For new ONT workflows, prefer Dorado for basecalling/demultiplexing/trimming context and Chopper or Filtlong for FASTQ-level filtering.

**Note:** the original Porechop developer declared Porechop unsupported/abandonware. Treat original Porechop as legacy-only; use Porechop_ABI only when you have a specific adapter-discovery or legacy reproducibility reason.

## Official Documentation

- [Porechop_ABI](https://github.com/bonsai-team/Porechop_ABI)
- [Porechop_ABI tags](https://github.com/bonsai-team/Porechop_ABI/tags)
- [Original Porechop](https://github.com/rrwick/Porechop) (unsupported legacy reference)
- [Dorado](https://github.com/nanoporetech/dorado)
- [Chopper](https://github.com/wdecoster/chopper)

## Installation

```bash
# Via conda/mamba
conda install -c bioconda porechop_abi

# Via pixi (recommended for this workflow)
pixi add porechop_abi
```

## Key Command-Line Flags

### Basic Syntax
```bash
porechop_abi -i INPUT [-o OUTPUT] [options]
```

### Input/Output
- `-i <file>`, `--input <file>` - FASTA/FASTQ input or directory (required)
- `-o <file>`, `--output <file>` - Output FASTA/FASTQ (default: stdout)
- `--format <format>` - Output format (auto, fasta, fastq, fasta.gz, fastq.gz)

### Threading
- `-t <int>`, `--threads <int>` - Number of threads for adapter alignment (default: 4)

### Adapter Search
- `--adapter_threshold <float>` - Minimum % match for an adapter (default: 90.0)
- `--check_reads <int>` - Number of reads to check for adapters (default: 10000)
- `--scoring_scheme <str>` - Alignment scoring scheme (default: "3,-6,-5,-2")

### End Adapter Trimming
- `--end_size <int>` - Number of bp at read ends to search for adapters (default: 150)
- `--min_trim_size <int>` - Minimum bp to trim from read ends (default: 4)
- `--extra_end_trim <int>` - Additional bp to trim from ends (default: 2)
- `--end_threshold <float>` - Min % match for end adapters (default: 75.0)

### Middle Adapter Splitting
- `--no_split` - Skip splitting reads with middle adapters
- `--discard_middle` - Discard reads with middle adapters
- `--middle_threshold <float>` - Min % match for middle adapters (default: 85.0)
- `--extra_middle_trim_good_side <int>` - Extra bp trim on good side (default: 10)
- `--extra_middle_trim_bad_side <int>` - Extra bp trim on bad side (default: 100)
- `--min_split_read_size <int>` - Minimum size for split reads (default: 1000)

### Barcode Demultiplexing
- `-b <dir>`, `--barcode_dir <dir>` - Output directory for demultiplexed reads
- `--barcode_threshold <float>` - Min % match for barcodes (default: 75.0)
- `--barcode_diff <float>` - Min % difference between best/second barcode (default: 5.0)
- `--require_two_barcodes` - Only demultiplex reads with barcodes at both ends
- `--untrimmed` - Output untrimmed reads to file
- `--discard_unassigned` - Discard reads without barcode match

### Output Control
- `-v <int>`, `--verbosity <int>` - Progress info: 0=none, 1=some, 2=lots, 3=full (default: 1)

## Common Usage Examples

### Basic Adapter Trimming

```bash
porechop_abi -i input.fastq -o output.fastq
```

### Trim with Multiple Threads

```bash
porechop_abi -i input.fastq -o output.fastq -t 16
```

### Discard Chimeric Reads

```bash
porechop_abi -i input.fastq -o output.fastq --discard_middle
```

### No Read Splitting (Trim Only)

```bash
porechop_abi -i input.fastq -o output.fastq --no_split
```

### Output to Gzipped FASTQ

```bash
porechop_abi -i input.fastq -o output.fastq.gz --format fastq.gz
```

### Demultiplex Barcoded Reads

```bash
porechop_abi -i input.fastq -b demultiplexed_reads/ -t 16
```

### Demultiplex with Strict Barcode Matching

```bash
porechop_abi -i input.fastq -b demultiplexed_reads/ \
  --barcode_threshold 80 \
  --require_two_barcodes \
  --discard_unassigned
```

### Process Directory of FASTQ Files

```bash
porechop_abi -i fastq_directory/ -o trimmed_output.fastq -t 16
```

### Conservative Trimming (Less Aggressive)

```bash
porechop_abi -i input.fastq -o output.fastq \
  --end_threshold 80 \
  --middle_threshold 90 \
  --extra_end_trim 0
```

### Aggressive Trimming

```bash
porechop_abi -i input.fastq -o output.fastq \
  --end_threshold 70 \
  --extra_end_trim 5 \
  --extra_middle_trim_bad_side 150
```

### Verbose Output for Debugging

```bash
porechop_abi -i input.fastq -o output.fastq -v 3
```

## Input/Output Formats

### Input Formats
- FASTQ (gzipped or uncompressed)
- FASTA (gzipped or uncompressed)
- Directory containing FASTQ files (processed recursively)

### Output Formats
- FASTQ (default)
- FASTA
- Gzipped versions (fastq.gz, fasta.gz)
- Outputs to stdout if no `-o` specified

### Barcode Demultiplexing Output
- Creates separate files per barcode in output directory
- Format: `BC01.fastq`, `BC02.fastq`, etc.
- `none.fastq` for reads without barcode match (unless `--discard_unassigned`)

## Performance Tips

### Threading
- Use `-t` to set threads equal to CPU cores
- Optimal: 8-16 threads for most datasets
- Adapter alignment is parallelized across threads

### Memory Usage
- Porechop_ABI has modest memory requirements
- Typically <2GB RAM for most operations
- Scales with read length and number of concurrent threads

### Speed Optimization
- Reduce `--check_reads` if adapter set is well-known (faster startup)
- Use `--no_split` if chimeric reads are rare (faster processing)
- Process gzipped files directly (automatic detection)

### Disk I/O
- Output to compressed format to save disk space
- Use pipes to avoid intermediate files
- Process input directory in one pass

## Adapter Detection

Porechop_ABI can discover adapters and also works with known ONT adapter/barcode contexts such as:
- Native barcoding kits (NBD103, NBD104, NBD114, etc.)
- PCR barcoding kits (PCR12, PCR96, etc.)
- Rapid barcoding kits (RBK001, RBK004, RB096, etc.)
- Standard ONT adapters (including reverse complement)

### Adapter Search Process

1. **Initial scan**: Checks first N reads (default: 10000)
2. **Adapter identification**: Finds which adapters are present
3. **End trimming**: Searches read ends (default: 150bp) for adapters
4. **Middle detection**: Searches full read for internal adapters
5. **Splitting/trimming**: Removes or splits based on adapter location

## Parameter Recommendations

### Standard Nanopore Run
```bash
porechop_abi -i input.fastq -o output.fastq -t 16
```

### Conservative Trimming (Keep More Data)
```bash
porechop_abi -i input.fastq -o output.fastq \
  -t 16 \
  --end_threshold 80 \
  --middle_threshold 90 \
  --no_split
```

### Aggressive Trimming (Higher Quality)
```bash
porechop_abi -i input.fastq -o output.fastq \
  -t 16 \
  --end_threshold 70 \
  --extra_end_trim 5 \
  --discard_middle
```

### Barcoded Run (Standard)
```bash
porechop_abi -i input.fastq -b barcodes/ -t 16
```

### Barcoded Run (Strict)
```bash
porechop_abi -i input.fastq -b barcodes/ \
  -t 16 \
  --barcode_threshold 80 \
  --barcode_diff 10 \
  --require_two_barcodes \
  --discard_unassigned
```

### Quick Processing (Skip Chimera Detection)
```bash
porechop_abi -i input.fastq -o output.fastq \
  -t 16 \
  --no_split \
  --check_reads 5000
```

## Common Workflows

### Fallback Adapter Trimming Pipeline
```bash
# Use only when basecaller/demultiplexer trimming is unavailable
# or adapter discovery is explicitly needed.
porechop_abi -i raw_reads.fastq -o trimmed_reads.fastq -t 16

# Quality filter with Filtlong
filtlong --min_length 1000 trimmed_reads.fastq | gzip > filtered_reads.fastq.gz

# Map with minimap2
minimap2 -ax map-ont reference.fa filtered_reads.fastq.gz > mapped.sam
```

### Demultiplex and Process Each Barcode
```bash
# Demultiplex
porechop_abi -i multiplexed.fastq -b barcodes/ -t 16

# Process each barcode
for bc in barcodes/BC*.fastq; do
    barcode=$(basename $bc .fastq)
    filtlong --min_length 1000 $bc | \
      minimap2 -ax map-ont reference.fa - | \
      samtools sort -o ${barcode}.bam
done
```

### Conservative Trim + Assembly Prep
```bash
porechop_abi -i raw_reads.fastq -o trimmed_reads.fastq \
  -t 16 \
  --end_threshold 75 \
  --no_split

filtlong --target_bases 5000000000 \
  --min_length 5000 \
  trimmed_reads.fastq | gzip > assembly_reads.fastq.gz
```

## Alternatives and Notes

### When to Use Porechop_ABI
- Targeted adapter discovery in ONT FASTQ files
- Reproducing a legacy pipeline that used Porechop/Porechop_ABI
- Chimeric read detection and splitting when this behavior is specifically desired
- Fallback trimming when Dorado or kit-aware demultiplexing outputs are unavailable

### Alternatives to Consider
- **Dorado**: ONT basecaller/demultiplexer with trimming and read summaries
- **Chopper**: streaming FASTQ quality/length/end trimming
- **Filtlong**: long-read filtering and read selection for assembly
- **Cutadapt**: general-purpose adapter trimmer when adapter sequences are known

### Maintenance Status
- Original Porechop is no longer maintained.
- Prefer Dorado/Chopper/Filtlong for new ONT workflows unless adapter discovery is the reason to use Porechop_ABI.
- Document the reason whenever Porechop_ABI is used in a new analysis.
