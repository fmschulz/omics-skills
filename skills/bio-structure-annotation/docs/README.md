# Tool Documentation

Updated: 2026-02-01

## Overview

This directory contains practical usage guides for structure prediction and annotation tools. Each guide includes installation instructions, command-line flags, common usage patterns, and performance tips.

## Tools

### Structure Prediction

- **[boltz](boltz.md)** - Biomolecular interaction prediction with binding affinity estimation
  - GitHub: https://github.com/jwohlwend/boltz
  - Use for: Protein-ligand complexes, affinity screening, drug discovery

- **[colabfold](colabfold.md)** - Fast AlphaFold2/RoseTTAFold with optimized MSA generation
  - GitHub: https://github.com/sokrypton/ColabFold
  - Use for: Protein structure prediction, complexes, accessible GPU computing

### Structure Search & Annotation

- **[foldseek](foldseek.md)** - Fast protein structure search using 3Di structural alphabet
  - GitHub: https://github.com/steineggerlab/foldseek
  - Use for: Structure similarity search, clustering, large-scale database searches

- **[tm-vec](tm-vec.md)** - Transformer-based structure embedding for rapid similarity search
  - GitHub: https://github.com/tymor22/tm-vec
  - Use for: Fast pre-screening, large-scale structure comparisons, vector-based search

## Quick Reference

### When to Use Each Tool

| Task | Tool | Reason |
|------|------|--------|
| Fast structure pre-screening | tm-vec | Vector-based search is fastest |
| Detailed structure search | foldseek | High sensitivity, structural alignment |
| Protein structure prediction | colabfold | Accessible, well-established, fast MSA |
| Protein-ligand affinity | boltz | Specialized for binding predictions |
| Complex structure prediction | colabfold or boltz | Both support multi-chain systems |
| Structure clustering | foldseek | Built-in clustering algorithms |

### Installation Quick Start

```bash
# tm-vec
conda create -n tmvec faiss-cpu python=3.9 -c pytorch
conda activate tmvec
pip install tm-vec

# foldseek
conda install -c conda-forge -c bioconda foldseek

# colabfold
# See LocalColabFold: https://github.com/YoshitakaMo/localcolabfold

# boltz
pip install boltz[cuda] -U
```

## Typical Workflow

### Structure-Based Annotation Pipeline

1. **Fast pre-screening** (optional, for large datasets)
   - Use tm-vec to quickly filter candidates
   - Reduces search space for detailed analysis

2. **Structure prediction**
   - Use colabfold for general protein structure prediction
   - Use boltz if ligand binding or affinity is important

3. **Detailed structure search**
   - Use foldseek against PDB, AlphaFoldDB, or custom databases
   - High sensitivity mode for distant homologs
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

### Papers and Citations

See `../bio-skills-references.md` for complete citations and methodology details.

## Support and Issues

- Tool-specific issues: Report to respective GitHub repositories
- Skill implementation: See main skill documentation in `../SKILL.md`
