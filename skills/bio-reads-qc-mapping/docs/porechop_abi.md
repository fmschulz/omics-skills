# Porechop_ABI 0.5.1 source / v0.5.0 tag - Legacy/Fallback Nanopore Adapter Trimming

Last verified: 2026-05-30
Tool version/release checked: source `__version__ = '0.5.1'` on master; latest GitHub tag v0.5.0
Official docs/manual: https://github.com/bonsai-team/Porechop_ABI
Release/source: https://github.com/bonsai-team/Porechop_ABI/tags and https://github.com/bonsai-team/Porechop_ABI/blob/master/porechop_abi/version.py

## When to use

Porechop_ABI is a targeted fallback for finding and removing Oxford Nanopore adapters when basecaller or demultiplexer trimming is unavailable, when adapter discovery is part of the question, or to reproduce a legacy pipeline. For new ONT workflows, prefer Dorado trimming and Chopper or Filtlong for FASTQ-level filtering. Cutadapt fits when the adapter sequences are known. The original Porechop is unmaintained; use it for legacy reproduction only. Document the reason whenever Porechop_ABI runs in a new analysis.

```bash
pixi add porechop_abi
porechop_abi -i input.fastq -o output.fastq -t 16
```

## Key flags

| Flag | Meaning (default) |
|------|-------------------|
| `-i`, `-o` | Input FASTA/FASTQ or directory; output file (stdout when omitted) |
| `--format` | `auto`, `fasta`, `fastq`, `fasta.gz`, `fastq.gz` |
| `-t` | Threads for adapter alignment (4); always pass it |
| `--check_reads` | Reads scanned for adapter discovery (10000) |
| `--adapter_threshold`, `--end_threshold`, `--middle_threshold` | Minimum % match: adapter 90, read end 75, middle 85 |
| `--end_size`, `--extra_end_trim` | End search window (150 bp) and extra trim (2 bp) |
| `--no_split`, `--discard_middle` | Keep reads with a middle adapter unsplit; discard them |
| `-b`, `--barcode_threshold`, `--barcode_diff`, `--require_two_barcodes`, `--discard_unassigned` | Demultiplex to `BC01.fastq`..., `none.fastq` for unmatched (75, 5) |

## Examples

```bash
# Conservative trimming
porechop_abi -i input.fastq -o output.fastq -t 16 --end_threshold 80 --middle_threshold 90 --no_split
# Strict demultiplexing
porechop_abi -i input.fastq -b barcodes/ -t 16 --barcode_threshold 80 --barcode_diff 10 --require_two_barcodes --discard_unassigned
# Fallback trim, then filter for assembly
porechop_abi -i raw.fastq -o trimmed.fastq -t 16
filtlong --min_length 1000 trimmed.fastq | gzip > filtered.fastq.gz
```

Memory stays under about 2 GB. Lower `--check_reads` when the adapter set is known.
