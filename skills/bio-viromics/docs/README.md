# Tool Documentation

Last verified: 2026-10-01
Tool version/release checked: geNomad v1.12.0 / DB v1.9; CheckV v1.1.1 / DB v1.5; vConTACT3 3.2.4 (bioconda 3.1.6); GVClass v2.0.3 / resources v2.0.0
Official docs/manual: See linked per-tool guides in this directory.
Release/source: See linked per-tool guides in this directory.

## Overview

Usage guides for the core tools in the bio-viromics skill: installation, verified command-line options, examples, and how each tool fits the workflow.

## Available Tools

### [geNomad](genomad-usage.md)
Version: 1.12.0

Identifies virus and plasmid sequences in nucleotide FASTA, assigns ICTV taxonomy to viruses, and annotates genes.

- **Official docs**: https://portal.nersc.gov/genomad/
- **Release/source**: https://github.com/apcamargo/genomad/releases/tag/v1.12.0
- **Use case**: Initial viral detection from assemblies

### [CheckV](checkv-usage.md)
Version: 1.1.1

Estimates completeness of viral genomes, identifies closed genomes, and trims host regions from proviruses.

- **Official docs**: https://bitbucket.org/berkeleylab/checkv
- **Database archive**: https://portal.nersc.gov/CheckV/
- **Use case**: Quality control and completeness estimation

### [vConTACT3](vcontact3-usage.md)
Version: 3.2.4 source tag (latest on Bitbucket); bioconda ships 3.1.6

Clusters viral genomes with gene-sharing networks and assigns hierarchical taxonomy.

- **Official docs**: https://vcontact3.readthedocs.io/
- **Release/source**: https://bitbucket.org/MAVERICLab/vcontact3/commits/tag/3.2.4
- **Use case**: Prokaryotic-virus clustering and taxonomy

### [GVClass](gvclass-usage.md)
Version: v2.0.3 software; v2.0.0 runtime resource bundle

Assigns taxonomy to Nucleocytoviricota, Mirusviricota, and Preplasmiviricota genomes by per-marker phylogenetic placement and reports completeness and contamination estimates.

- **Official docs**: https://NeLLi-team.github.io/gvclass/
- **Release/source**: https://github.com/NeLLi-team/gvclass/releases/tag/v2.0.3
- **Publication**: Pitot et al. (2024) *npj Viruses* https://doi.org/10.1038/s44298-024-00069-7
- **Use case**: Giant-virus classification and quality

## Typical Workflow Integration

0. **Domain triage** (QuickClade via `/tracking-taxonomy-updates`)
   - Input: assembled contigs, genomes, MAGs, or bin directories
   - Output: per-contig domain routing table; viral and virus-like rows continue here
1. **Viral detection** (geNomad)
   - Input: assembled contigs
   - Output: candidate viral sequences
2. **Quality control** (CheckV)
   - Input: viral sequences from geNomad
   - Output: quality tiers and completeness estimates
3. **Clustering and taxonomy** (vConTACT3), for prokaryotic viruses
   - Input: high- and medium-quality genomes from CheckV
   - Output: genome clusters and taxonomic assignments
4. **Giant-virus analysis** (GVClass), for NCLDV, Mirusviricota, and PPV candidates
   - Input: bins or contigs of 30 kb or more (50 kb preferred)
   - Output: giant-virus taxonomy and quality metrics

## Quick Reference

| Tool | Primary function | Key output |
|------|------------------|------------|
| geNomad | Viral detection | `<prefix>_summary/<prefix>_virus.fna` |
| CheckV | Quality assessment | `quality_summary.tsv` |
| vConTACT3 | Clustering and taxonomy | `final_assignments.csv` |
| GVClass | Giant-virus classification | `gvclass_summary.tsv` |

## Installation Overview

Add the tools to the project's Pixi environment. GVClass runs from its own Pixi checkout or the Apptainer wrapper:

```bash
pixi add genomad checkv
pixi add "python>=3.10,<3.12" vcontact3   # needs Python 3.10 or 3.11; bioconda ships 3.1.6

# GVClass (Apptainer wrapper with the database built in)
wget https://raw.githubusercontent.com/NeLLi-team/gvclass/main/gvclass-a
chmod +x gvclass-a
```

## Additional Resources

- Skill specification: [../SKILL.md](../SKILL.md)
