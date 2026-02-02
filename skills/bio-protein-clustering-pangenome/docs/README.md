# Tool Documentation

Updated: 2026-02-01

This directory contains practical usage guides for protein clustering and pangenome analysis tools.

## Available Tools

### Primary Clustering Tools

| Tool | Best For | Speed | Documentation |
|------|----------|-------|---------------|
| **MMseqs2** | Large datasets (>500 genomes) | Very Fast | [mmseqs2.md](mmseqs2.md) |
| **ProteinOrtho** | Medium datasets (50-500 genomes) | Fast | [proteinortho.md](proteinortho.md) |
| **OrthoFinder** | Phylogenetic analysis, gene trees | Medium | [orthofinder.md](orthofinder.md) |
| **OrthoMCL** | Rigorous ortholog detection | Slow | [orthomcl.md](orthomcl.md) |

### Quick Selection Guide

**Choose based on your needs:**

- **Speed is priority** → MMseqs2 (linear-time clustering)
- **Phylogenetic trees needed** → OrthoFinder (gene trees + species tree)
- **Balanced accuracy/speed** → ProteinOrtho (graph-based RBH)
- **Maximum rigor** → OrthoMCL (database-backed, well-established)
- **Very large scale (>1000 genomes)** → MMseqs2 easy-linclust
- **Synteny analysis** → ProteinOrtho with PoFF extension

## Tool Comparison

### Features

| Feature | MMseqs2 | ProteinOrtho | OrthoFinder | OrthoMCL |
|---------|---------|--------------|-------------|----------|
| Installation | Easy | Easy | Easy | Complex |
| Dependencies | Minimal | Minimal | Moderate | High (MySQL) |
| Scalability | Excellent | Good | Good | Moderate |
| Gene Trees | No | No | Yes | No |
| Synteny Support | No | Yes | No | No |
| Paralog Detection | Basic | Good | Excellent | Good |
| Speed (1000 genomes) | Hours | Days | Days | Weeks |

### Typical Runtimes

**Dataset: 100 bacterial genomes, ~300k proteins, 16 CPU cores**

| Tool | Approximate Runtime |
|------|---------------------|
| MMseqs2 (easy-linclust) | 10-30 minutes |
| MMseqs2 (easy-cluster) | 1-3 hours |
| ProteinOrtho (Diamond) | 2-6 hours |
| OrthoFinder (Diamond) | 4-12 hours |
| OrthoFinder (MSA mode) | 12-48 hours |
| OrthoMCL | 6-24 hours |

## Documentation Contents

Each tool guide includes:

1. **Official Documentation Links**
   - GitHub/website
   - Papers and manuals

2. **Installation Instructions**
   - Conda/Bioconda (recommended)
   - Docker containers
   - Manual installation

3. **Key Command-Line Flags**
   - Clustering parameters
   - Performance options
   - Output configuration

4. **Common Usage Examples**
   - Basic clustering
   - Pangenome analysis
   - Performance optimization

5. **Input/Output Formats**
   - FASTA requirements
   - Output file descriptions
   - Parsing examples (Python)

6. **Performance Tips**
   - Speed vs accuracy trade-offs
   - Memory management
   - Parameter recommendations

7. **Troubleshooting**
   - Common errors
   - Solutions and workarounds

## Common Workflow

### 1. Basic Pangenome Analysis

```bash
# Fast clustering for presence/absence matrix
mmseqs easy-cluster proteins.faa orthogroups tmp \
    --min-seq-id 0.9 \
    -c 0.8 \
    --threads 16
```

### 2. Phylogenomic Analysis

```bash
# Comprehensive analysis with gene trees
orthofinder -f protein_fastas/ \
    -S diamond \
    -M msa \
    -t 32

# Extract single-copy orthologs for phylogeny
# Results in: Orthogroups_SingleCopyOrthologues.txt
```

### 3. Large-Scale Metagenomics

```bash
# Incremental approach for 1000+ MAGs
orthofinder -f CoreMAGs_50/ -n Core -S mmseqs -t 64
orthofinder --core Results_Core/ --assign AllMAGs/ -t 64
```

## Parameter Guidelines

### Taxonomic Distance vs Parameters

| Comparison Level | Identity (%) | Coverage (%) | E-value |
|------------------|--------------|--------------|---------|
| Same strain | 95-100 | 90-95 | 1e-10 |
| Same species | 85-95 | 80-90 | 1e-7 |
| Same genus | 70-85 | 70-80 | 1e-5 |
| Same family | 50-70 | 60-70 | 1e-5 |
| Cross-family | 30-50 | 50-60 | 1e-3 |

### Tool-Specific Recommendations

#### MMseqs2
- **Closely related (>95% identity)**: `easy-linclust` with `-s 1.0`
- **Moderate divergence (70-95%)**: `easy-cluster` with `-s 4.0`
- **Distant homologs (<70%)**: `easy-cluster` with `-s 7.0`

#### ProteinOrtho
- **Same species**: `-identity=95 -cov=90 -p=diamond`
- **Same genus**: `-identity=70 -cov=70 -p=diamond`
- **With synteny**: `-synteny` (requires GFF files)

#### OrthoFinder
- **Fast orthogroups**: `-S diamond -og`
- **Phylogenomics**: `-S diamond -M msa`
- **Large-scale (>100 species)**: Core + assign workflow

#### OrthoMCL
- **Same species**: `identity=95, match=90, inflation=1.5`
- **Same genus**: `identity=70, match=70, inflation=2.0`
- **Distant**: `identity=30, match=50, inflation=3.0`

## Output Analysis

### Converting to Presence/Absence Matrix

All tools output orthogroup assignments that can be converted to binary matrices for downstream analysis.

**Common format:**
```
Orthogroup    genome1    genome2    genome3
OG0000001     gene001    gene101    gene201
OG0000002     gene002    *          gene202
```

**Python parsing example:**
```python
import pandas as pd

# Read orthogroup table
og = pd.read_csv('orthogroups.tsv', sep='\t', index_col=0)

# Create binary presence/absence matrix
presence = og.notna().astype(int)

# Calculate core/accessory/cloud
n_genomes = len(og.columns)
freq = presence.sum(axis=1) / n_genomes

core = og[freq >= 0.99]        # ≥99% of genomes
accessory = og[(freq >= 0.15) & (freq < 0.99)]  # 15-99%
cloud = og[freq < 0.15]        # <15%
```

## Additional Resources

### Pangenome Pipelines
- **GET_HOMOLOGUES**: Comprehensive bacterial pangenome analysis
- **Roary**: Fast prokaryotic pangenome pipeline
- **PEPPAN**: Accurate reconstruction with paralog scoring
- **Anvi'o**: Integrated pangenomics with visualization
- **RIBAP**: Core genome annotation beyond species level

### References
See [../SKILL.md](../SKILL.md) for comprehensive references and concepts.

## Getting Help

1. **Check tool documentation** in this directory
2. **Review SKILL.md** for pangenome concepts
3. **Search Biostars** for community solutions
4. **GitHub Issues** for tool-specific problems

## Contributing

To update documentation:
1. Verify information against official sources
2. Test commands on sample datasets
3. Include practical examples
4. Keep concise and focused on common use cases
