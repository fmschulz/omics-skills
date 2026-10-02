# Tool Documentation

Last verified: 2026-05-30
Tool version/release checked: Boltz v2.2.1; ColabFold v1.6.1; Foldseek 10-941cd33; TM-Vec 1.0.2
Official docs/manual: See linked per-tool guides in this directory.
Release/source: See linked per-tool guides in this directory.

## Overview

This directory contains practical usage guides for structure prediction and annotation tools. Each guide includes installation instructions, command-line flags, common usage patterns, and performance tips.

## Tools

### Structure prediction

- **[boltz](boltz.md)** - Boltz-2 (MIT license, CUDA, NVIDIA cuEquivariance kernels)
  - GitHub: https://github.com/jwohlwend/boltz
  - Version checked: v2.2.1
  - Use for: default structure and complex prediction, protein-ligand binding affinity, drug discovery
  - Notes: replaces Boltz-1; predicts binding affinity alongside structure

- **[colabfold](colabfold.md)** - ColabFold with MMseqs2-GPU MSA backend
  - GitHub: https://github.com/sokrypton/ColabFold
  - Version checked: v1.6.1
  - Use for: cases where a wider MSA than Boltz-2 builds is needed
  - Notes: with the MMseqs2-GPU backend, ColabFold prediction ran 31.8× faster than the standard AlphaFold2 pipeline (Kallenborn et al. 2025, *Nature Methods*)

- **ESMFold** - fast monomer pre-screening only (15–20 GB VRAM)
  - Not used for final predictions; route ESMFold candidates to Boltz-2

> AlphaFold3 is not part of this stack (non-commercial license, large VRAM footprint). Use Boltz-2.

### Structure search and annotation

- **[foldseek](foldseek.md)** - Foldseek 10-941cd33; `--gpu 1` enables the GPU prefilter on CUDA Turing+ and needs a `makepaddedseqdb` target
  - GitHub: https://github.com/steineggerlab/foldseek
  - Use for: structure similarity search, clustering, large-scale database searches; 4-27× faster than CPU Foldseek on GPU (Kallenborn et al. 2025)

- **[tm-vec](tm-vec.md)** - Transformer-based structure embedding for rapid similarity search
  - GitHub: https://github.com/valentynbez/tmvec (maintained fork; provides the `tmvec build-db` and `tmvec search` CLI the driver uses)
  - Original: https://github.com/tymor22/tm-vec (release 1.0.2 ships `tmvec-build-database` and `tmvec-search` instead)
  - Use for: fast pre-screening, large-scale structure comparisons, vector-based search

## Quick reference

### When to use each tool

| Task | Tool | Reason |
|------|------|--------|
| Fast structure pre-screening (embedding) | TM-Vec | Vector-based search; seconds across millions of proteins |
| Fast monomer pre-screening (structure) | ESMFold | Lowest VRAM; lower accuracy — triage only |
| Default structure + complex + affinity | Boltz-2 | MIT license; CUDA; complexes and ligands |
| Deeper MSA than Boltz-2 builds | ColabFold + MMseqs2-GPU | GPU MSA search for AF2-style runs |
| Detailed structure search | Foldseek 10 (`--gpu 1`) | High sensitivity, GPU-accelerated structural alignment |
| Structure clustering | Foldseek | Built-in clustering algorithms |

### Installation Quick Start

Install everything into the project's Pixi environment and pin versions:

```bash
# tm-vec (maintained fork, pinned to a commit)
pixi add --pypi "tmvec @ git+https://github.com/valentynbez/tmvec.git@6bdf11adff9884cff54e4f69927d40edebc80038"

# foldseek
pixi add foldseek

# colabfold
# See LocalColabFold: https://github.com/YoshitakaMo/localcolabfold

# boltz
pixi add --pypi "boltz[cuda]"
```

## Typical Workflow

### Structure-Based Annotation Pipeline

1. **Fast pre-screening** (optional, for large datasets)
   - Use tm-vec to quickly filter candidates
   - Reduces search space for detailed analysis

2. **Structure prediction**
   - Default: Boltz-2 (structure, complex, and binding affinity)
   - Wider MSA needed: ColabFold with MMseqs2-GPU backend
   - Triage only: ESMFold

3. **Detailed structure search**
   - Use Foldseek 10 (`--gpu 1` on Turing+ GPUs) against PDB, AlphaFoldDB, or custom databases
   - High-sensitivity mode for distant homologs
   - Fast mode for close homologs

4. **Clustering** (for large result sets)
   - Use foldseek easy-cluster to group similar structures
   - Identify representative structures for annotation

## Performance Considerations

### Speed Comparison (approximate)
- **tm-vec**: Fastest (vector search, seconds for millions)
- **foldseek**: Fast (structure alignment, minutes for large DBs)
- **colabfold**: Moderate (structure prediction, minutes to hours)
- **boltz**: Moderate to slow (complex prediction with affinity)

### Resource Requirements

| Tool | RAM | GPU | Storage |
|------|-----|-----|---------|
| tm-vec | Low-Moderate | Optional | Low (embeddings) |
| foldseek | Moderate-High* | Optional | Moderate (databases) |
| colabfold | Moderate | Recommended | High (~940GB for local DBs) |
| boltz | Moderate | Recommended | Moderate |

*foldseek RAM can be reduced with `--sort-by-structure-bits 0`

## Additional Resources

### Reference Databases

**Foldseek/Structure Search:**
- AlphaFoldDB (AFDB50): ~54M structures
- PDB: Experimental structures
- Custom databases from predicted structures

**TM-vec:**
- CATH domains database
- SWISS-PROT sequences (pre-embedded)

## Support and Issues

- Tool-specific issues: Report to respective GitHub repositories
- Skill implementation: See main skill documentation in `../SKILL.md`
