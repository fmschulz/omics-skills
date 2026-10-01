# Tool Documentation

Last verified: 2026-05-30
Tool version/release checked: Pyrodigal v3.7.1; pyrodigal-gv v0.3.2; BRAKER4 upstream workflow (checked 2026-07-11); legacy BRAKER v3.0.8; Infernal v1.1.5; tRNAscan-SE v2.0.12
Official docs/manual: See linked per-tool guides in this directory.
Release/source: See linked per-tool guides in this directory.

## Overview

This directory contains practical usage guides for gene calling and RNA-feature tools used in the bio-gene-calling skill.

## Tools

### Prokaryotic and viral gene calling

- **[pyrodigal.md](pyrodigal.md)** - Pyrodigal v3.7.1, Python bindings and CLI around Prodigal for bacteria and archaea
  - Fast prokaryotic gene prediction
  - Metagenomic and single-genome modes
  - CLI compatible with common Prodigal workflows plus Python output writers
  - Thread-safe parallel processing
  - Source: https://github.com/althonos/pyrodigal

- **[pyrodigal-gv.md](pyrodigal-gv.md)** - pyrodigal-gv v0.3.2 for viruses, including giant viruses and alternative-code viruses
  - Use the `pyrodigal-gv` CLI or `pyrodigal_gv.ViralGeneFinder` in new workflows
  - Distributes the prodigal-gv viral metagenomic model set (`PRODIGAL_GV_VERSION` v2.11.0)
  - The standalone `prodigal-gv` 2.11.0 binary (https://github.com/apcamargo/prodigal-gv) uses the same models; ViroSync pins a patched build of it. Use it with `-p meta` when results must match such a pipeline
  - Source: https://github.com/althonos/pyrodigal-gv

### Eukaryotic gene calling

- **BRAKER4** - current upstream Snakemake workflow; pin the repository commit, Snakefile checksum, and container lock from <https://github.com/Gaius-Augustus/BRAKER4>
- **[braker.md](braker.md)** - legacy BRAKER3 v3.0.8 reproduction guide
  - Combines GeneMark-ETP and AUGUSTUS internally (AUGUSTUS is not run as a standalone tool)
  - RNA-seq and protein evidence integration
  - Automated training
  - Upstream README marks BRAKER as deprecated in favor of BRAKER4; keep BRAKER3 only where this workflow explicitly requires it
  - Source: https://github.com/Gaius-Augustus/BRAKER

### RNA gene detection

- **[trnascan-se.md](trnascan-se.md)** - tRNA detection with tRNAscan-SE v2.0.12
  - Covariance model-based; isotype-specific models
  - Bacterial, archaeal, eukaryotic modes
  - Uses Infernal v1.1-era covariance-model searches
  - Source: https://github.com/UCSC-LoweLab/tRNAscan-SE

- **[infernal.md](infernal.md)** - Infernal v1.1.5 `cmsearch` for rRNA and other ncRNA detection against Rfam covariance models
  - Replaces barrnap as the default rRNA caller in this workflow
  - Domain-appropriate Rfam models (SSU, LSU, 5S, 5.8S; mitochondrial 12S/16S where applicable) — see SKILL.md for the model list
  - Source: http://eddylab.org/infernal/

## Quick reference

| Tool | Checked version | Organism type | Mode | Typical use case |
|------|-----------------|---------------|------|------------------|
| pyrodigal | 3.7.1 | Bacteria, archaea | Meta / single | Fast prokaryotic gene calling |
| pyrodigal-gv | 0.3.2 | Viruses (including giants) | Meta by default in CLI | Viral genomes |
| BRAKER4 | pinned commit | Eukaryotes | Snakemake ES/ET/EP/ETP | Current evidence-aware eukaryotic annotation |
| BRAKER3 | 3.0.8 | Eukaryotes | Evidence-based | High-quality eukaryotic annotation |
| tRNAscan-SE | 2.0.12 | All domains | Domain-specific | tRNA detection |
| Infernal `cmsearch` | 1.1.5 | All domains | Rfam covariance models | rRNA (SSU/LSU/5S/5.8S) and other ncRNA |

> **Retired from this workflow:** AUGUSTUS as a standalone tool (invoke it through BRAKER4 or a documented BRAKER3 reproduction); `barrnap` (replaced by Infernal `cmsearch` against domain-specific Rfam models).

## Documentation Format

Each tool guide includes:
- Official documentation URLs
- Installation commands
- Key command-line flags
- Common usage examples for gene calling
- Input/output format specifications
- Performance optimization tips

## Usage Notes

- Install the tools in the project's pinned Pixi environment; this skill ships no environment file
- Examples assume tools are in PATH
- Set thread counts explicitly to match the allocated CPUs
- Check tool-specific QC recommendations
