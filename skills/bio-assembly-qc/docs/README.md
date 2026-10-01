# Tool Documentation

Last verified: 2026-05-30
Tool version/release checked: SPAdes v4.2.0; Flye v2.9.6; Autocycler v0.6.2; QUAST v5.3.0
Official docs/manual: See linked per-tool guides in this directory.
Release/source: See linked per-tool guides in this directory.

## Assembly tools

### SPAdes v4.2.0
Genome assembler for short-read data (Illumina, IonTorrent) with hybrid assembly using long reads. [spades.md](spades.md) documents v4.2.0. v4.3.0 (2026-06-14) adds a low-memory `--frugal` mode, and its release notes list no removed options.

- Documentation: [spades.md](spades.md)
- Official website: https://github.com/ablab/spades
- Release/source: https://github.com/ablab/spades/releases/tag/v4.2.0
- Use cases: bacterial genomes, metagenomes, plasmids, single-cell, hybrid assemblies

### Flye / metaFlye v2.9.6
Long-read assembler for PacBio and Oxford Nanopore data with sophisticated repeat resolution. metaFlye mode (`--meta`) is the baseline for long-read metagenome assembly when HiFi-tuned alternatives are not available.

- Documentation: [flye.md](flye.md)
- Official website: https://github.com/fenderglass/Flye
- Release/source: https://github.com/mikolmogorov/Flye/releases/tag/2.9.6
- Use cases: PacBio/ONT isolates and metagenomes; ONT-only HiFi-poor datasets

### Autocycler v0.6.2 (bacterial isolate consensus)
Consensus assembler for bacterial isolate genomes. Use it when the goal is a complete, high-confidence isolate genome from multiple independent long-read assembly attempts. It complements Flye/Raven/miniasm-style draft assemblies; it is not the default path for mixed-community metagenomes.

- Documentation: [autocycler.md](autocycler.md)
- Official website: https://github.com/rrwick/Autocycler
- Release/source: https://github.com/rrwick/Autocycler/releases/tag/v0.6.2
- Use cases: haploid prokaryotic isolate genomes with enough long-read coverage to compare multiple draft assemblies

### metaMDBG v1.1+ (preferred for HiFi metagenomes; v1.4 current)
Minimizer-space de Bruijn graph assembler for PacBio HiFi metagenomes; v1.1+ also accepts ONT R10.4+ reads (`--in-ont`). In its benchmark it recovered up to twice as many circularized high-quality MAGs as metaFlye on HiFi data (Benoit et al. 2024, *Nature Biotechnology*, https://doi.org/10.1038/s41587-023-01983-6). It writes `contigs.fasta.gz` to `--out-dir`.

- Official website: https://github.com/GaetanBenoitDev/metaMDBG
- Release/source: https://github.com/GaetanBenoitDev/metaMDBG/releases
- Use cases: PacBio HiFi metagenomes (preferred over metaFlye for this read type)

### myloasm (optional, large or diverse long-read datasets)
Long-read metagenome assembler first released in 2025 (v0.7.0 current). Consider it when runtime limits a diverse or very large dataset and the read profile matches its assumptions. Record the choice and version in the run log.

- Source: https://github.com/bluenote-1577/myloasm

## Quality Control Tools

### QUAST v5.3.0
Assembly quality assessment: contiguity, and with a reference, completeness and misassembly metrics.

- Documentation: [quast.md](quast.md)
- Official website: http://quast.sourceforge.net/
- Release/source: https://github.com/ablab/quast/releases/tag/quast_5.3.0
- Use cases: Assembly QC, assembler comparison, reference-based/free evaluation

## Quick Start

**Typical workflow:**
```bash
# 1. Assemble with SPAdes (short reads)
spades.py --isolate -1 reads_R1.fastq.gz -2 reads_R2.fastq.gz -o spades_out -t 16

# OR assemble with Flye (long reads)
flye --nano-hq ont_reads.fastq.gz --genome-size 5m --out-dir flye_out --threads 16

# 2. Evaluate assembly quality
quast.py spades_out/contigs.fasta -r reference.fasta -o qc_results -t 8
```

## Tool selection guide

| Read type | Genome type | Recommended tool | Alternative |
|-----------|-------------|------------------|-------------|
| Illumina paired-end | Bacterial isolate | `spades.py --isolate` | — |
| Illumina paired-end | Metagenomic | `spades.py --meta` | — |
| PacBio HiFi | Isolate | `flye --pacbio-hifi` | Autocycler consensus when complete isolate closure is required |
| PacBio HiFi | Metagenomic | metaMDBG v1.1+ | metaFlye `--meta --pacbio-hifi` |
| ONT Q20+ | Isolate | `flye --nano-hq` | Autocycler consensus when complete isolate closure is required |
| ONT Q20+ | Metagenomic | metaFlye `--meta --nano-hq` | metaMDBG `--in-ont` (R10.4+); myloasm (when speed-bound) |
| Illumina + PacBio | Hybrid | SPAdes (hybrid) | Flye + short-read polishing |
| Illumina + ONT | Hybrid | SPAdes (hybrid) | Flye + short-read polishing |

## Performance Considerations

| Tool | Memory (bacterial) | Memory (human) | Runtime (bacterial) | Runtime (human) |
|------|-------------------|----------------|---------------------|-----------------|
| SPAdes | 8-32 GB | 128-256 GB | 1-4 hours | 24-72 hours |
| Flye | 2-4 GB | 141-450 GB | 1-2 hours | 780-4000 CPU hours |
| QUAST | 2-8 GB | 16-64 GB | 5-30 minutes | 1-4 hours |

## Additional Resources

- Install the tools into the project's pinned pixi environment; this skill ships no `pixi.toml`.
