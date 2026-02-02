# Tool Documentation

Last updated: 2026-02-01

## Assembly Tools

### SPAdes v4.2.0
Versatile genome assembler for short-read data (Illumina, IonTorrent) with support for hybrid assembly using long reads.

- Documentation: [spades.md](spades.md)
- Official website: https://github.com/ablab/spades
- Use cases: Bacterial genomes, metagenomes, plasmids, single-cell, hybrid assemblies

### Flye v2.9.6
Long-read assembler optimized for PacBio and Oxford Nanopore data with sophisticated repeat resolution.

- Documentation: [flye.md](flye.md)
- Official website: https://github.com/fenderglass/Flye
- Use cases: PacBio/ONT genomes, metagenomes, high-quality long-read assemblies

## Quality Control Tools

### QUAST v5.3.0
Comprehensive assembly quality assessment tool providing contiguity, completeness, and correctness metrics.

- Documentation: [quast.md](quast.md)
- Official website: http://quast.sourceforge.net/
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

## Tool Selection Guide

| Read Type | Genome Type | Recommended Tool | Alternative |
|-----------|-------------|------------------|-------------|
| Illumina paired-end | Bacterial | SPAdes --isolate | - |
| Illumina paired-end | Metagenomic | SPAdes --meta | - |
| PacBio HiFi | Any | Flye --pacbio-hifi | SPAdes (hybrid) |
| ONT Q20+ | Any | Flye --nano-hq | SPAdes (hybrid) |
| Illumina + PacBio | Any | SPAdes (hybrid) | Flye + polishing |
| Illumina + ONT | Any | SPAdes (hybrid) | Flye + polishing |

## Performance Considerations

| Tool | Memory (bacterial) | Memory (human) | Runtime (bacterial) | Runtime (human) |
|------|-------------------|----------------|---------------------|-----------------|
| SPAdes | 8-32 GB | 128-256 GB | 1-4 hours | 24-72 hours |
| Flye | 2-4 GB | 141-450 GB | 1-2 hours | 780-4000 CPU hours |
| QUAST | 2-8 GB | 16-64 GB | 5-30 minutes | 1-4 hours |

## Additional Resources

- All tools available via pixi (see `pixi.toml` in skill root)
- Paper summaries with use cases: `../summaries/`
- General bioinformatics references: `../../bio-skills-references.md`
