# VeryFastTree Usage Guide

Last verified: 2026-10-01
Tool version/release checked: VeryFastTree v4.0.5 (`VeryFastTree -expert` from bioconda; flags below checked against it)
Official docs/manual: https://github.com/citiususc/veryfasttree
Release/source: https://github.com/citiususc/veryfasttree/releases/tag/v4.0.5

## Official Documentation
- GitHub: https://github.com/citiususc/veryfasttree
- Releases: https://github.com/citiususc/veryfasttree/releases
- VeryFastTree reimplements the FastTree-2 algorithm with parallelization and vector instructions and keeps its command line.

## Installation

```bash
pixi add veryfasttree
VeryFastTree -h
```

### From Source
Requires CMake and a C++ compiler; CUDA is optional.

```bash
git clone https://github.com/citiususc/veryfasttree.git
cd veryfasttree
git checkout v4.0.5
cmake -DEXT=AVX2 .
make
```

## Input/Output Formats

### Input
- FASTA, FASTQ, NEXUS, or interleaved PHYLIP alignments
- zlib- or bzip2-compressed files

### Output
- Newick tree with branch lengths and local support values on a 0–1 scale

## Key Command-Line Flags

`VeryFastTree -expert` lists every option.

### Essentials
```bash
-nt                     # Nucleotide alignment (default: protein)
-out <file>             # Write the tree to a file instead of stdout
-threads <n>            # Threads (default: OMP_NUM_THREADS)
-seed <n>               # Random seed
-log <file>             # Save intermediate trees and per-site rates
-n <number>             # Read <number> alignments from one interleaved PHYLIP file (e.g. seqboot output)
```

### Models
```bash
# Protein: JTT by default
-lg                     # Le-Gascuel 2008 instead of JTT
-wag                    # Whelan-Goldman 2001 instead of JTT
# Nucleotide: Jukes-Cantor by default
-gtr                    # GTR instead of Jukes-Cantor
-cat <n>                # Number of CAT rate categories (default 20)
-gamma                  # After CAT optimization, report the Gamma likelihood and rescale branch lengths
```

### Support
```bash
-boot <n>               # Number of resamples for local support (default 1000)
-nosupport              # No support values
```

### Speed and parallelism
```bash
-fastest                # Search only the top hit per node; faster, less thorough
-threads-level <0-4>    # Degree of parallelization (default 3)
-threads-mode <0-1>     # 1 (default): deterministic; 0: non-deterministic parts
-ext <name>             # Vector extension: AUTO (default), NONE, SSE, SSE3, AVX, AVX2, AVX512, CUDA
-double-precision       # 64-bit arithmetic
-fastexp <0-3>          # Exponential implementation; 0 (default) is the standard library
```

Since v4.0, deterministic mode (`-threads-mode 1`) is at least as fast as non-deterministic mode, per the tool's help text. Levels 2 and above traverse the tree in a different order, so results can differ from level 0 or 1.

### Memory
```bash
-disk-computing              # Store static data on disk when RAM runs short
-disk-computing-path <path>  # Directory for that data
-disk-dynamic-computing      # Also store dynamic data on disk (slower)
-disk-dynamic-limit <n>      # Cap memory-mapped files if mapping fails
```

## Common Usage Examples

### Protein tree with local support
```bash
VeryFastTree -boot 1000 -seed 1729 -threads 8 alignment.faa > tree.nwk
```

### Nucleotide tree under GTR
```bash
VeryFastTree -nt -gtr -threads 8 alignment.fna > tree.nwk
```

### LG model with Gamma-rescaled branch lengths
```bash
VeryFastTree -lg -gamma -threads 8 alignment.faa > tree.nwk
```

### Very large alignment with limited memory
```bash
VeryFastTree -fastest -disk-computing -disk-computing-path /scratch/$USER/vft \
  -threads 32 alignment.faa > tree.nwk
```

## Choosing Settings

- Exploratory or time-bounded work at any size: VeryFastTree is the default first tree; keep IQ-TREE for final inference.
- Above about 2,000 sequences: VeryFastTree with default settings; add `-fastest` only when runtime forces it.
- Memory limits: `-disk-computing`, then `-disk-dynamic-computing`.
- Set `-threads` to the allocated CPU count and keep the default deterministic mode for reproducible trees.
- Compare `-fastexp` or `-fastest` runs against a default run on a subset before using them for a result.

## Quality Control Checks

- Every input sequence appears in the output tree.
- Very long branches can point to alignment errors or contaminant sequences.
- Support values are on a 0–1 scale; the skill driver writes them to `support.tsv` unchanged. Many studies treat 0.7 or more as moderate and 0.9 or more as strong support; state the threshold you use.

## Integration with Downstream Tools

Post-process with ETE 4 ([ete-toolkit.md](ete-toolkit.md)) or inspect interactively with `ete4 explore -t tree.nwk`.

## Citation

- Piñeiro and Pichel (2024) *GigaScience*: VeryFastTree 4.0
- Piñeiro et al. (2020) *Bioinformatics*: VeryFastTree
- Price et al. (2010) *PLoS ONE*: FastTree 2

## Version Information

Checked against VeryFastTree v4.0.5 on 2026-10-01.
