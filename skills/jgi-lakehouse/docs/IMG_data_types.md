# IMG Genome & Metagenome Data Types

Note: numbers are as of February 13, 2026, but will change in the future with new data addition

## Overview

The IMG (Integrated Microbial Genomes) database contains **286,759 genomic sequences** organized into two major categories:
- **196,379 isolate genomes** from cultured organisms or single-cell amplified genomes (SAGs)
- **90,380 metagenomes** from environmental samples

This guide helps you identify which IMG data types match your research needs and how to query them efficiently.

---

## Quick Reference: Data Types by Analysis Project Type

### **Isolate Genomes** (from pure cultures or single-cell samples)

| Type | Count | Description | Best For |
|------|-------|-------------|----------|
| **Genome Analysis (Isolate)** | 150,515 | Traditional single-organism genomes | Comparative genomics, metabolic pathway analysis |
| **Single Cell Analysis (screened)** | 3,281 | Quality-checked single-cell amplified genomes (SAGs) | Single-cell studies, rare organisms |
| **Single Cell Analysis (unscreened)** | 11,427 | Raw SAGs without quality filtering | Screening for contamination |

### **Metagenome-Derived Isolates (MAGs & Specialized Extractions)**

| Type | Count | Description | Best For |
|------|-------|-------------|----------|
| **Metagenome-Assembled Genome (MAG)** | 26,260 | High-quality reconstructed genomes from metagenomes | Uncultured organisms, ecosystem diversity |
| **Metagenome - Single Particle Sort (SPS)** | 13,098 | Genomes from sorted cells (flow cytometry) | Cell-sorted populations, specific microbial groups |
| **Metagenome - Cell Enrichment** | 4,850 | Genomes from enriched microbial cultures | Target-specific isolation |
| **Metagenome - Low Complexity** | 7,221 | Genomes from simple, well-defined communities | Biofilms, pure co-cultures, bioreactors |
| **Metagenome - SIP** (Stable Isotope Probing) | 1,374 | Genomes from isotope-labeled organisms | Functional ecology, metabolic activity tracking |

### **Metagenomes** (whole community samples)

| Type | Count | Description | Best For |
|------|-------|-------------|----------|
| **Metagenome Analysis** | 49,939 | Standard environmental metagenomes | Community composition, functional potential |
| **Metatranscriptome Analysis** | 12,758 | RNA-based gene expression from communities | Active metabolism, functional profiling |
| **Combined Assembly** | 1,057 | Multi-sample co-assemblies | Cross-sample comparison, rare genes |
| **Combined Assembly SIP Metagenome** | 209 | Co-assembled SIP metagenomes | Isotope-labeled ecosystem studies |
| **Metagenome - Co-Culture** | 31 | Defined mixed culture metagenomes | Synthetic communities, interactions |

### **Specialized Types**

| Type | Count | Description |
|------|-------|-------------|
| **Metagenome-Extracted Genome** | 12 | Individual genomes extracted from metagenome datasets |
| **Combined Assembly Single Cell (screened)** | 22 | Co-assembled SAGs with QC |
| **Combined Assembly Single Cell (unscreened)** | 14 | Raw co-assembled SAGs |

---

## Filtering by Genome Type

IMG uses two genome type categories that cross-cut the analysis project types:

```sql
SELECT genome_type, COUNT(*) cnt
FROM "img-db-2 postgresql".img_core_v400.taxon
GROUP BY genome_type
```

### **Genome Type = 'isolate'** (196,379 records)
- Pure single-organism assemblies
- Includes: traditional isolates, MAGs, SAGs, enrichments
- Best for: single-organism analyses

### **Genome Type = 'metagenome'** (90,380 records)
- Whole-community assemblies
- Includes: standard metagenomes, metatranscriptomes, combined assemblies
- Best for: community-level analyses

---

## Common Query Patterns

### 1. Find Traditional Isolate Genomes

```sql
SELECT taxon_oid, taxon_display_name, domain, phylum, genus, species
FROM "img-db-2 postgresql".img_core_v400.taxon
WHERE analysis_project_type = 'Genome Analysis (Isolate)'
  AND is_public = 'Yes'
LIMIT 100
```

### 2. Find Metagenome-Assembled Genomes (MAGs)

```sql
SELECT taxon_oid, taxon_display_name, domain, phylum, genus
FROM "img-db-2 postgresql".img_core_v400.taxon
WHERE analysis_project_type = 'Metagenome-Assembled Genome'
  AND is_public = 'Yes'
LIMIT 100
```

### 3. Find All Metagenomes (Environmental Samples)

```sql
SELECT taxon_oid, taxon_display_name, analysis_project_type
FROM "img-db-2 postgresql".img_core_v400.taxon
WHERE genome_type = 'metagenome'
  AND is_public = 'Yes'
LIMIT 100
```

### 4. Find Single-Cell Amplified Genomes (SAGs)

```sql
SELECT taxon_oid, taxon_display_name, analysis_project_type
FROM "img-db-2 postgresql".img_core_v400.taxon
WHERE analysis_project_type IN (
    'Single Cell Analysis (screened)',
    'Single Cell Analysis (unscreened)'
  )
  AND is_public = 'Yes'
LIMIT 100
```

### 5. Find RNA-Based Community Studies

```sql
SELECT taxon_oid, taxon_display_name
FROM "img-db-2 postgresql".img_core_v400.taxon
WHERE analysis_project_type = 'Metatranscriptome Analysis'
  AND is_public = 'Yes'
LIMIT 100
```

### 6. Find Specific Enrichment Studies

```sql
SELECT taxon_oid, taxon_display_name, analysis_project_type
FROM "img-db-2 postgresql".img_core_v400.taxon
WHERE analysis_project_type = 'Metagenome - Cell Enrichment'
  AND is_public = 'Yes'
LIMIT 100
```

### 7. Find Specific Isotope-Labeled Studies (SIP)

```sql
SELECT taxon_oid, taxon_display_name, analysis_project_type
FROM "img-db-2 postgresql".img_core_v400.taxon
WHERE analysis_project_type IN (
    'Metagenome - SIP',
    'Combined Assembly SIP Metagenome'
  )
  AND is_public = 'Yes'
LIMIT 100
```

### 8. Count Genomes by All Analysis Types

```sql
SELECT analysis_project_type, COUNT(*) cnt
FROM "img-db-2 postgresql".img_core_v400.taxon
WHERE is_public = 'Yes'
GROUP BY analysis_project_type
ORDER BY cnt DESC
```

### 9. Find Finished Genomes of a Specific Phylum

```sql
SELECT taxon_oid, taxon_display_name, analysis_project_type, seq_status
FROM "img-db-2 postgresql".img_core_v400.taxon
WHERE phylum = 'Proteobacteria'
  AND seq_status = 'Finished'
  AND analysis_project_type = 'Genome Analysis (Isolate)'
  AND is_public = 'Yes'
LIMIT 100
```

### 10. Find High-Quality Metagenome-Assembled Genomes

```sql
SELECT taxon_oid, taxon_display_name, completion, genome_completion
FROM "img-db-2 postgresql".img_core_v400.taxon
WHERE analysis_project_type = 'Metagenome-Assembled Genome'
  AND genome_completion >= 80  -- >= 80% complete
  AND is_public = 'Yes'
LIMIT 100
```

---

## Data Type Selection Guide

### **Choose "Genome Analysis (Isolate)" if you:**
- Want well-curated, single-organism genomes
- Need taxonomically reliable data
- Are doing comparative genomics
- Require highest annotation quality
- **Row count: 150,515** (most abundant type)

### **Choose MAGs (Metagenome-Assembled Genome) if you:**
- Study uncultured organisms
- Want microbial diversity from environmental samples
- Accept reconstructed genomes from metagenomics
- Need organisms not available in pure culture
- **Row count: 26,260**

### **Choose Metatranscriptomes if you:**
- Study active gene expression
- Differentiate between potential and actual metabolism
- Work with RNA-based community profiling
- Analyze functional activity in environments
- **Row count: 12,758**

### **Choose Metagenomes if you:**
- Study whole microbial community composition
- Analyze metabolic potential of ecosystems
- Look for rare organisms or functions
- Want unbiased environmental sampling
- **Row count: 49,939** (largest metagenome category)

### **Choose Single-Cell SAGs if you:**
- Study rare or unculturable microorganisms
- Examine individual cell genomes
- Have ultra-low-abundance organisms
- **Row count: 14,708** (combined screened + unscreened)

### **Choose Enrichment/SIP Genomes if you:**
- Work on specific microbial groups or functions
- Track isotope incorporation (SIP)
- Study sorted cell populations
- Analyze low-complexity communities
- **Row count: 6,074 + 1,374 = 7,448**

---

## Data Type Statistics (as of Feb 2026)

```
Total genomes in IMG: 286,759

By Genome Type:
  • Isolate genomes:     196,379 (68.5%)
  • Metagenomes:          90,380 (31.5%)

Top 5 Analysis Project Types:
  1. Genome Analysis (Isolate)        150,515 (52.5%)
  2. Metagenome Analysis               49,939 (17.4%)
  3. Metagenome-Assembled Genome       26,260 (9.2%)
  4. Metagenome - Single Particle Sort 13,098 (4.6%)
  5. Metatranscriptome Analysis        12,758 (4.4%)
```

---

## Accessing Genome Files

Once you've identified the genomes you want, use the `taxon_oid` field to download files from the JGI filesystem:

```bash
# Genome packages are located at:
/clusterfs/jgi/img_merfs-ro/img_web/img_web_data/download/{taxon_oid}.tar.gz

# Example: Download and extract MAG
cp /clusterfs/jgi/img_merfs-ro/img_web/img_web_data/download/2601500125.tar.gz .
tar -xzf 2601500125.tar.gz

# Extracted files include:
#   - {taxon_oid}.fna          (genome assembly)
#   - {taxon_oid}.genes.faa    (protein sequences)
#   - {taxon_oid}.genes.fna    (gene sequences)
#   - {taxon_oid}.gff          (annotations)
#   - {taxon_oid}.cog.tab.txt  (COG annotations)
#   - {taxon_oid}.pfam.tab.txt (Pfam annotations)
#   - {taxon_oid}.ko.tab.txt   (KEGG KO annotations)
```

See the [examples](../examples/) folder for automated download scripts.

---

## Important Notes

1. **Not all genomes are public**: Filter by `is_public = 'Yes'` for public datasets
2. **Sequence status varies**: Use `seq_status = 'Finished'` for complete genomes
3. **Genome completion**: Check `genome_completion` field (% estimated completion)
4. **Gene content**: Use the `gene` table to query annotations within genomes
5. **High-quality filters**: Some analyses use `high_quality_flag` for QC'd genomes
6. **Cross-references**: Link to GOLD projects via `sequencing_gold_id` or `study_gold_id`

---

## Related Documentation

- [data-catalog.md](data-catalog.md) - Full table inventory
- [sql-quick-reference.md](sql-quick-reference.md) - SQL syntax guide
- [examples/](../examples/) - Download and analysis scripts
