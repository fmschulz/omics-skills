# Tool Documentation

This directory contains comprehensive usage guides for the bioinformatics tools used in the bio-reads-qc-mapping skill.

**Last verified:** 2026-05-30
**Tool version/release checked:** BBTools v39.85; minimap2 v2.31; Filtlong v0.3.1; Porechop_ABI source 0.5.1 / tag v0.5.0
**Official docs/manual:** See linked per-tool guides in this directory.
**Release/source:** See linked per-tool guides in this directory.

## Tools Covered

### Short Read Processing
- **[bbduk.md](bbduk.md)** - BBTools/BBDuk v39.85 quality control, adapter trimming, and contamination filtering
- **[bbmap.md](bbmap.md)** - BBTools/BBMap v39.85 short read alignment to reference genomes

### Long Read Processing
- **Dorado** - ONT basecalling, demultiplexing, summaries, and trimming when starting from signal/BAM
- **Chopper** - FASTQ-only long-read quality, length, and end trimming
- **[filtlong.md](filtlong.md)** - Filtlong v0.3.1 long read quality filtering (Nanopore/PacBio)
- **[porechop_abi.md](porechop_abi.md)** - Porechop_ABI source version 0.5.1 / latest tag v0.5.0 targeted legacy/fallback ONT adapter discovery and trimming

### Universal Read Mapping
- **[minimap2.md](minimap2.md)** - minimap2 v2.31 versatile aligner for both short and long reads

## Quick Reference

| Tool | Primary Use | Input | Output |
|------|-------------|-------|--------|
| bbduk | Short read QC/trimming | FASTQ | FASTQ |
| bbmap | Short read mapping | FASTQ | SAM/BAM |
| Dorado | ONT basecalling/demux/trimming summary | POD5/BAM/FASTQ | BAM/FASTQ/TSV |
| Chopper | Long-read FASTQ QC/filtering | FASTQ | FASTQ |
| Filtlong | Long read filtering | FASTQ | FASTQ |
| Porechop_ABI | Legacy/fallback ONT adapter discovery | FASTQ | FASTQ |
| minimap2 | Universal read mapping | FASTQ/FASTA | SAM/PAF |

## Common Workflows

### Short Read QC and Mapping
```bash
bbtools() {
  docker run --rm -u "$(id -u):$(id -g)" \
    -v "$PWD":/work -w /work \
    bryce911/bbtools:39.85 "$@"
}

# 1. Quality control and adapter trimming
bbtools bbduk.sh in1=R1.fq in2=R2.fq out1=clean_R1.fq out2=clean_R2.fq \
  ref=adapters.fa ktrim=r k=23 mink=11 hdist=1 qtrim=rl trimq=20

# 2. Map to reference
bbtools bbmap.sh ref=reference.fa in1=clean_R1.fq in2=clean_R2.fq out=mapped.sam
```

### Nanopore Read QC and Mapping
```bash
# 1. Prefer basecaller/demultiplexer trimming when starting from ONT signal/BAM.
# For FASTQ-only reads, filter and trim with Chopper:
chopper --quality 10 --minlength 1000 --headcrop 0 --tailcrop 0 \
  < raw.fastq.gz | gzip > filtered.fastq.gz

# 2. Map to reference
minimap2 -ax map-ont reference.fa filtered.fastq.gz > mapped.sam
```

### PacBio Read QC and Mapping
```bash
# 1. Quality filter
filtlong --min_length 1000 --keep_percent 90 raw.fastq | gzip > filtered.fastq.gz

# 2. Map to reference (HiFi)
minimap2 -ax map-hifi reference.fa filtered.fastq.gz > mapped.sam
```

## Installation

Run BBTools programs through Bryce Foster's official Docker image. As of
2026-05-30, `bryce911/bbtools:39.85` and `latest` point to digest
`sha256:e697da46d8955a30256cc1c2a9ed8da362ad5a86ed16b6a41ab64ed03801a2a1`.

Install non-BBTools dependencies via conda/mamba or pixi:

```bash
# BBTools container
docker pull bryce911/bbtools:39.85

# Other tools
conda install -c bioconda minimap2 chopper filtlong porechop_abi
pixi add minimap2 chopper filtlong porechop_abi
```

## Documentation Sources

- **bbduk/bbmap**: [BBTools JGI DOE](https://jgi.doe.gov/data-and-tools/software-tools/bbtools/) | [BBDuk manual](https://bbmap.org/tools/bbduk) | [BBMap manual](https://bbmap.org/docs.html) | [Container tags](https://hub.docker.com/r/bryce911/bbtools/tags)
- **minimap2**: [GitHub](https://github.com/lh3/minimap2) | [Manual](https://lh3.github.io/minimap2/minimap2.html) | [v2.31 release](https://github.com/lh3/minimap2/releases/tag/v2.31)
- **Dorado**: [GitHub](https://github.com/nanoporetech/dorado)
- **Chopper**: [GitHub](https://github.com/wdecoster/chopper)
- **Filtlong**: [GitHub](https://github.com/rrwick/Filtlong) | [v0.3.1 release](https://github.com/rrwick/Filtlong/releases/tag/v0.3.1)
- **Porechop_ABI**: [GitHub](https://github.com/bonsai-team/Porechop_ABI) | [tags](https://github.com/bonsai-team/Porechop_ABI/tags) for targeted fallback adapter discovery. The original Porechop is unmaintained.

## Performance Guidelines

### Memory Requirements
| Tool | Typical RAM | Notes |
|------|-------------|-------|
| bbduk | 1-4 GB | Small references; 85% of RAM for large refs |
| bbmap | 4-32 GB | Depends on reference size |
| minimap2 | 4-16 GB | Use -I flag to limit memory |
| Chopper | Low | Streaming FASTQ filter |
| Filtlong | 10-20x input | ~10-20 bytes per input base |
| Porechop_ABI | <2 GB | Fallback adapter discovery/trimming |

### Threading Recommendations
- **bbduk/bbmap**: 4-12 threads (diminishing returns beyond 12)
- **minimap2**: 8-16 threads optimal
- **Dorado**: GPU recommended where available
- **Chopper**: streaming; pair with external compression threads if needed
- **Porechop_ABI**: 8-16 threads when fallback adapter discovery is needed
- **Filtlong**: Single-threaded only

### Speed Optimization Tips
1. Use compressed input/output directly (all tools support gzip)
2. Pre-build indices for repeated mapping operations
3. Use appropriate presets for your data type
4. Pipe between tools to avoid intermediate files
5. Use fast local storage (SSD) for temporary files

## File Format Support

| Format | bbduk | bbmap | minimap2 | Chopper | Filtlong | Porechop_ABI |
|--------|-------|-------|----------|---------|----------|--------------|
| FASTQ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| FASTQ.gz | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| FASTA | ✓ | ✓ | ✓ | - | - | ✓ |
| SAM | ✓ (in) | ✓ | ✓ (out) | - | - | - |
| BAM | ✓ (in) | ✓ | - | - | - | - |
| PAF | - | - | ✓ (out) | - | - | - |

## Getting Help

Each tool provides built-in help:

```bash
bbtools() {
  docker run --rm -u "$(id -u):$(id -g)" \
    -v "$PWD":/work -w /work \
    bryce911/bbtools:39.85 "$@"
}

bbtools bbduk.sh --help
bbtools bbmap.sh --help
minimap2 --help
chopper --help
filtlong --help
porechop_abi --help
```

For detailed usage examples and parameter recommendations, see the individual tool documentation files in this directory.
