# Download Genomes by Taxonomy

Query Lakehouse for genome metadata, get NCBI accessions, download from GenBank.

## Use Case
Find all genomes for a bacterial family and download FASTA/GFF/protein files from NCBI.

## Key Tables
- `"gold-db-2 postgresql".gold.project` - Sequencing projects
- `"gold-db-2 postgresql".gold.organism_v2` - Organism taxonomy
- `"gold-db-2 postgresql".gold.ncbi_assembly` - NCBI assembly accessions
- `"gold-db-2 postgresql".gold.study` - Ecosystem/environment info

## SQL Pattern

### Step 1: Find Genomes with NCBI Accessions
```sql
SELECT DISTINCT
    p.gold_id,
    p.project_name,
    o.organism_name,
    o.genus,
    o.family,
    o.ncbi_taxon_id,
    a.ncbi_assembly_accession,
    a.assembly_level,
    a.genome_size,
    a.gc_percent,
    a.contig_count
FROM "gold-db-2 postgresql".gold.project p
LEFT JOIN "gold-db-2 postgresql".gold.organism_v2 o ON p.organism_id = o.organism_id
LEFT JOIN "gold-db-2 postgresql".gold.ncbi_assembly a ON p.project_id = a.project_id
WHERE o.family LIKE '%Midichloriaceae%'
  AND p.is_public = 'Yes'
  AND a.ncbi_assembly_accession IS NOT NULL
ORDER BY a.assembly_level, a.genome_size DESC
LIMIT 100
```

### Step 2: Get Ecosystem/Environment Info
```sql
SELECT
    p.gold_id,
    p.project_name,
    s.ecosystem,
    s.ecosystem_category,
    s.ecosystem_type,
    s.ecosystem_subtype,
    s.specific_ecosystem
FROM "gold-db-2 postgresql".gold.project p
JOIN "gold-db-2 postgresql".gold.study s ON p.master_study_id = s.study_id
WHERE p.gold_id IN ('Gp0006663', 'Gp0484838', 'Gp0763694')
```

## Pitfalls & Solutions

### 1. Sequences Not in Lakehouse
**Problem:** Lakehouse has metadata but NOT genome sequences.

**Solution:** Use NCBI accessions to download from GenBank:
```bash
# Install NCBI datasets CLI
pixi add ncbi-datasets-cli

# Download genomes
datasets download genome accession GCA_000219355.1 GCA_003072485.1 \
    --include genome,gff3,protein --filename genomes.zip

# Extract
unzip genomes.zip -d genomes/
```

### 2. Ecosystem in Study, Not Project
**Problem:** `project.ecosystem` doesn't exist or is empty.

**Solution:** Join to study table via `master_study_id`:
```sql
JOIN "gold-db-2 postgresql".gold.study s ON p.master_study_id = s.study_id
WHERE s.ecosystem IS NOT NULL
```

### 3. Filter by Assembly Level
Prefer complete genomes over drafts:
```sql
WHERE a.assembly_level = 'Complete Genome'
-- or
ORDER BY CASE a.assembly_level
    WHEN 'Complete Genome' THEN 1
    WHEN 'Chromosome' THEN 2
    WHEN 'Scaffold' THEN 3
    WHEN 'Contig' THEN 4
    ELSE 5
END
```

## Download Commands

### Single Genome
```bash
datasets download genome accession GCA_000219355.1 \
    --include genome,gff3,protein \
    --filename genome.zip
```

### Multiple Genomes
```bash
# From file
echo "GCA_000219355.1
GCA_003072485.1
GCA_029981845.1" > accessions.txt

datasets download genome accession --inputfile accessions.txt \
    --include genome,gff3,protein \
    --filename genomes.zip
```

### Genome + Annotations
```bash
datasets download genome accession GCA_000219355.1 \
    --include genome,gff3,protein,cds,rna \
    --filename full_annotation.zip
```

## Variations

### By Genus Pattern
```sql
WHERE o.organism_name LIKE '%Rickettsia%'
  OR o.genus = 'Rickettsia'
```

### With Bioproject Info
```sql
SELECT p.gold_id, p.ncbi_bioproject_accession, a.ncbi_assembly_accession
FROM "gold-db-2 postgresql".gold.project p
JOIN "gold-db-2 postgresql".gold.ncbi_assembly a ON p.project_id = a.project_id
WHERE p.ncbi_bioproject_accession IS NOT NULL
```

## Python Usage (optional)
See `download_genomes_by_taxonomy.py` for automated workflow.
