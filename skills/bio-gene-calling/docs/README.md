# Tool Documentation

Last updated: 2026-02-01

## Overview

This directory contains practical usage guides for gene calling tools used in the bio-gene-calling skill.

## Tools

### Prokaryotic Gene Calling

- **[pyrodigal.md](pyrodigal.md)** - Python binding to Prodigal (v3.7.0)
  - Fast prokaryotic gene prediction
  - Metagenomic and single-genome modes
  - Thread-safe parallel processing
  - Source: https://github.com/althonos/pyrodigal

- **[prodigal-gv.md](prodigal-gv.md)** - Modified Prodigal for viruses (v2.11.0)
  - Optimized for giant viruses
  - Additional metagenomic models
  - Compatible with standard Prodigal
  - Source: https://github.com/apcamargo/prodigal-gv

### Eukaryotic Gene Calling

- **[braker.md](braker.md)** - Pipeline for eukaryotic annotation (v3.0.8)
  - Combines GeneMark and AUGUSTUS
  - RNA-Seq and protein evidence integration
  - Automated training
  - Source: https://github.com/Gaius-Augustus/BRAKER

- **[augustus.md](augustus.md)** - Eukaryotic gene prediction (v3.5.0)
  - Probabilistic modeling
  - 90+ trained species
  - Evidence integration
  - Source: https://github.com/Gaius-Augustus/Augustus

### RNA Gene Detection

- **[trnascan-se.md](trnascan-se.md)** - tRNA detection (v2.0.12)
  - Covariance model-based
  - Bacterial, archaeal, eukaryotic modes
  - Uses Infernal v1.1
  - Source: https://github.com/UCSC-LoweLab/tRNAscan-SE

## Quick Reference

| Tool | Organism Type | Mode | Typical Use Case |
|------|---------------|------|------------------|
| pyrodigal | Bacteria, Archaea | Meta/Single | Fast prokaryotic gene calling |
| prodigal-gv | Viruses | Meta | Viral genomes, especially giants |
| BRAKER | Eukaryotes | Evidence-based | High-quality eukaryotic annotation |
| AUGUSTUS | Eukaryotes | Ab initio + hints | Eukaryotic gene prediction |
| tRNAscan-SE | All domains | Domain-specific | tRNA detection |

## Documentation Format

Each tool guide includes:
- Official documentation URLs
- Installation commands
- Key command-line flags
- Common usage examples for gene calling
- Input/output format specifications
- Performance optimization tips

## Usage Notes

- All tools are installed via pixi (see pixi.toml in skill root)
- Examples assume tools are in PATH
- Adjust thread counts based on available resources
- Check tool-specific QC recommendations
