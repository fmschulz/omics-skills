# Tool Documentation

Last verified: 2026-05-30
Tool version/release checked: OrthoFinder v3.1.5; MMseqs2 v18-8cc5c; ProteinOrtho v6.3.6
Official docs/manual: See linked per-tool guides in this directory.
Release/source: See linked per-tool guides in this directory.

This directory contains practical usage guides for protein clustering and pangenome analysis tools.

## Available Tools

### Primary clustering tools

| Tool | Best for | Speed | Documentation |
|------|----------|-------|---------------|
| **OrthoFinder v3.1.5** | Default orthology inference, gene + species trees | Medium | [orthofinder.md](orthofinder.md) |
| **MMseqs2 v18-8cc5c** | Sequence clustering and search backbones; very large datasets | Very fast | [mmseqs2.md](mmseqs2.md) |
| **ProteinOrtho v6.3.6** | Large pangenomes where OrthoFinder is RAM-limited | Fast | [proteinortho.md](proteinortho.md) |

### Quick selection guide

- Default orthology inference up to a few hundred genomes -> **OrthoFinder v3.1.5** (v3 accuracy/scaling improvements; current source: https://github.com/OrthoFinder/OrthoFinder/releases/tag/v3.1.5).
- Very large pangenomes where OrthoFinder is too RAM-heavy -> **ProteinOrtho v6.3.6** (graph-based RBH; PoFF extension adds synteny support; source: https://gitlab.com/paulklemm_PHD/proteinortho/-/releases/v6.3.6).
- Sequence clustering at any scale -> **MMseqs2 v18-8cc5c** (`easy-cluster` or `easy-linclust`; docs: https://github.com/soedinglab/MMseqs2/wiki and https://github.com/soedinglab/MMseqs2/releases/tag/18-8cc5c). GPU search first appeared in v16. Use `--gpu` only with a GPU-enabled build and a command that exposes the flag; Turing GPUs are supported and Ampere-or-newer GPUs provide the full-speed path.
- Synteny across many genomes → run alongside `ntSynt` or MCScanX (see SKILL.md).

> **Retired:** OrthoMCL has been dropped from this workflow. Existing pipelines should migrate to OrthoFinder v3.

## Tool comparison

### Features

| Feature | MMseqs2 | ProteinOrtho | OrthoFinder |
|---------|---------|--------------|-------------|
| Installation | Easy | Easy | Easy |
| Dependencies | Minimal | Minimal | Moderate |
| Scalability | Excellent (GPU optional) | Good | Good |
| Gene trees | No | No | Yes |
| Synteny support | No | Yes (PoFF) | No |
| Paralog detection | Basic | Good | Excellent |
| Speed (1000 genomes) | Hours | Days | Days |

### Typical runtimes

**Dataset: 100 bacterial genomes, ~300k proteins, 16 CPU cores**

| Tool | Approximate runtime |
|------|---------------------|
| MMseqs2 (easy-linclust) | 10–30 minutes |
| MMseqs2 (easy-cluster) | 1–3 hours |
| ProteinOrtho (DIAMOND) | 2–6 hours |
| OrthoFinder v3 (DIAMOND) | 3–10 hours |
| OrthoFinder v3 (MSA mode) | 10–40 hours |

## Documentation Contents

Each tool guide includes:

1. **Official Documentation Links**
   - GitHub/website
   - Papers and manuals

2. **Installation Instructions**
   - Pinned Pixi project environment
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
# Start from one protein FASTA per genome and a complete genomes.tsv manifest.
# If MMseqs2 needs a combined FASTA, create protein_to_genome.tsv before concatenation.
mmseqs easy-cluster combined_proteins.faa orthogroups tmp \
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
- **Closely related (>95% identity)**: `easy-linclust`
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

# Read an external orthogroup table. Treat both blank cells and literal '*'
# placeholders as absence.
og = pd.read_csv(
    'orthogroups.tsv',
    sep='\t',
    index_col=0,
    na_values=['', '*'],
    keep_default_na=True,
)

# Count comma-delimited protein IDs, then derive presence/absence.
def copy_count(cell):
    if pd.isna(cell) or not str(cell).strip() or str(cell).strip() == '*':
        return 0
    return len([protein for protein in str(cell).split(',') if protein.strip()])

copy_number = og.apply(lambda column: column.map(copy_count))
presence = (copy_number > 0).astype(int)

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
See [../references.md](../references.md) for comprehensive references and concepts.

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
