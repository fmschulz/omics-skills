# OrthoMCL Usage Guide

## Official Documentation
- Website: https://orthomcl.org/orthomcl/
- User Guide: https://orthomcl.org/common/downloads/software/v2.0/UserGuide.txt
- Paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC3196566/
- Tutorial: https://darencard.net/blog/2018-01-12-orthomcl-tutorial/
- GitHub Pipeline: https://github.com/apetkau/orthomcl-pipeline

## Installation

### OrthoMCL Pipeline (Recommended)
```bash
# Automated pipeline wrapper (easier to use)
git clone https://github.com/apetkau/orthomcl-pipeline.git
cd orthomcl-pipeline

# Install dependencies via conda
conda install -c bioconda orthomcl mcl blast

# Or use Docker
docker pull quay.io/biocontainers/orthomcl
```

### Manual OrthoMCL Installation
```bash
# Download software
wget https://orthomcl.org/common/downloads/software/v2.0/orthomclSoftware-v2.0.9.tar.gz
tar -xzf orthomclSoftware-v2.0.9.tar.gz

# Install dependencies
# - Perl (with DBI::mysql module)
# - MySQL or Oracle database
# - MCL clustering software
# - BLAST+

# Install MCL
wget https://micans.org/mcl/src/mcl-latest.tar.gz
tar -xzf mcl-latest.tar.gz
cd mcl-*
./configure
make
make install
```

### Database Setup (Required)
```bash
# Install MySQL
sudo apt-get install mysql-server

# Create OrthoMCL database
mysql -u root -p
CREATE DATABASE orthomcl;
CREATE USER 'orthomcl'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON orthomcl.* TO 'orthomcl'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# Install database schema
orthomclInstallSchema orthomcl.config
```

## Key Command-Line Programs

### Core OrthoMCL Programs
All programs begin with `orthomcl` and print help with no arguments:

- `orthomclAdjustFasta` - Format protein FASTA files for OrthoMCL
- `orthomclFilterFasta` - Filter poor quality proteins
- `orthomclBlastParser` - Parse BLAST output
- `orthomclLoadBlast` - Load BLAST results into database
- `orthomclPairs` - Compute ortholog pairs
- `orthomclDumpPairsFiles` - Export pairs for MCL
- `orthomclMclToGroups` - Convert MCL clusters to orthogroups
- `orthomclInstallSchema` - Set up database schema

### OrthoMCL Pipeline Commands
```bash
orthomcl-pipeline -i INPUT_DIR -o OUTPUT_DIR -m CONFIG [OPTIONS]
```

**Key Options:**
- `-i|--input-dir` - Directory containing input FASTA files
- `-o|--output-dir` - Output directory
- `-m|--orthomcl-config` - OrthoMCL configuration file
- `--nocompliant` - Skip FASTA compliance check
- `--yes` - Auto-accept all prompts
- `-s|--scheduler` - Job scheduler (fork, sge, slurm)
- `-c|--cpus` - Number of CPUs for parallelization

## Configuration File

### orthomcl.config Template
```ini
# Database connection
dbVendor=mysql
dbConnectString=dbi:mysql:orthomcl:localhost:3306
dbLogin=orthomcl
dbPassword=password

# Similarity parameters
similarityCutoff=1e-5
percentMatchCutoff=50
percentIdentityCutoff=30

# MCL parameters
evalueExponentCutoff=-5
percentMatchCutoff=50
oracleIndexTblSpc=NONE
```

**Key Parameters:**
- `similarityCutoff` - E-value threshold for BLAST (default: 1e-5)
- `percentMatchCutoff` - Minimum alignment coverage % (default: 50%)
- `percentIdentityCutoff` - Minimum sequence identity % (default: 30%)
- `evalueExponentCutoff` - E-value exponent for scoring (default: -5)
- `inflation` - MCL inflation parameter (typically 1.5-3.0)

## Common Usage Examples

### Using OrthoMCL Pipeline (Recommended)

#### Basic Analysis
```bash
# Prepare input directory with FASTA files
mkdir input_fastas
cp genome1.faa genome2.faa genome3.faa input_fastas/

# Create config file
orthomcl-pipeline --setup

# Run complete pipeline
orthomcl-pipeline -i input_fastas/ \
                  -o orthomcl_results/ \
                  -m orthomcl.config \
                  --yes
```

#### Custom Parameters
```bash
# Higher stringency (90% identity, 80% coverage)
# Edit orthomcl.config:
# percentIdentityCutoff=90
# percentMatchCutoff=80

orthomcl-pipeline -i input_fastas/ \
                  -o stringent_results/ \
                  -m orthomcl_stringent.config \
                  -c 16
```

#### Cluster Execution
```bash
# Run on SLURM cluster
orthomcl-pipeline -i input_fastas/ \
                  -o cluster_results/ \
                  -m orthomcl.config \
                  -s slurm \
                  -c 64
```

### Manual OrthoMCL Workflow

#### Step 1: Format FASTA Files
```bash
# Adjust FASTA headers (add species tags)
orthomclAdjustFasta genome1 genome1.faa 1
orthomclAdjustFasta genome2 genome2.faa 2
orthomclAdjustFasta genome3 genome3.faa 3

# Creates: genome1.fasta, genome2.fasta, genome3.fasta
# Headers: >genome1|protein001
```

#### Step 2: Filter Proteins
```bash
# Combine all adjusted FASTA files
cat *.fasta > all_proteins.fasta

# Filter poor quality proteins
orthomclFilterFasta compliantFasta/ 10 20

# Creates:
# - goodProteins.fasta (high quality)
# - poorProteins.fasta (filtered out)
```

#### Step 3: All-vs-All BLAST
```bash
# Create BLAST database
makeblastdb -in goodProteins.fasta \
            -dbtype prot \
            -out goodProteins

# Run BLAST search
blastp -query goodProteins.fasta \
       -db goodProteins \
       -out all_vs_all.blast \
       -evalue 1e-5 \
       -outfmt 6 \
       -num_threads 16
```

#### Step 4: Load BLAST Results
```bash
# Parse BLAST output
orthomclBlastParser all_vs_all.blast compliantFasta/ >> similarSequences.txt

# Load into database
orthomclLoadBlast orthomcl.config similarSequences.txt
```

#### Step 5: Compute Pairs
```bash
# Find ortholog/paralog pairs
orthomclPairs orthomcl.config orthomcl_pairs.log cleanup=no

# Export pairs for MCL
orthomclDumpPairsFiles orthomcl.config
```

#### Step 6: MCL Clustering
```bash
# Run MCL clustering
mcl mclInput --abc -I 1.5 -o mclOutput

# I parameter: inflation (1.5-3.0)
# Lower = larger clusters, Higher = smaller clusters
```

#### Step 7: Convert to Orthogroups
```bash
# Convert MCL output to orthogroup format
orthomclMclToGroups OG 1000 < mclOutput > orthogroups.txt

# OG = prefix for orthogroup IDs
# 1000 = starting number
```

## Input/Output Formats

### Input Requirements

**FASTA Files:**
- One FASTA file per genome/species
- Protein sequences (amino acids)
- Must be "compliant" (pass quality filters)

**Compliant FASTA Format:**
```
>genome1|protein001
MTHKQVLVGADGVGKSAL...
>genome1|protein002
MRVLVVGAGGVGKSALT...
```

### Output Files

#### orthogroups.txt (from orthomclMclToGroups)
```
OG1000: genome1|prot001 genome2|prot101 genome3|prot201
OG1001: genome1|prot002 genome1|prot003 genome2|prot102
OG1002: genome2|prot103 genome3|prot202 genome3|prot203
```

**Format:**
- Each line = one orthogroup
- Format: `OGID: gene1 gene2 gene3 ...`
- Genes from same genome = paralogs

#### OrthoMCL Pipeline Output
```
orthomcl_results/
├── compliantFasta/           # Formatted FASTA files
├── all_vs_all.blast          # BLAST results
├── orthogroups.txt           # Orthogroup assignments
├── orthogroups_stats.txt     # Statistics summary
├── pan_genome.txt            # Pan-genome gene list
└── core_genome.txt           # Core genome genes
```

### Converting to Matrix Format

```python
import pandas as pd
from collections import defaultdict

# Parse orthogroups.txt
orthogroups = {}
with open('orthogroups.txt') as f:
    for line in f:
        og_id, genes = line.strip().split(': ')
        orthogroups[og_id] = genes.split()

# Build presence/absence matrix
genomes = set()
og_data = defaultdict(lambda: defaultdict(list))

for og_id, genes in orthogroups.items():
    for gene in genes:
        genome = gene.split('|')[0]
        genomes.add(genome)
        og_data[og_id][genome].append(gene)

# Create DataFrame
matrix_data = []
for og_id in orthogroups.keys():
    row = {'Orthogroup': og_id}
    for genome in sorted(genomes):
        genes = og_data[og_id].get(genome, [])
        row[genome] = ','.join(genes) if genes else ''
    matrix_data.append(row)

df = pd.DataFrame(matrix_data)
df.to_csv('orthogroups_matrix.tsv', sep='\t', index=False)

# Binary presence/absence
presence = df.copy()
for col in presence.columns[1:]:
    presence[col] = (presence[col] != '').astype(int)
```

## Performance Tips

### Speed Optimization

**Use Diamond Instead of BLAST:**
```bash
# Diamond is 100-10,000x faster than BLAST
diamond makedb --in goodProteins.fasta -d goodProteins

diamond blastp --query goodProteins.fasta \
               --db goodProteins \
               --out all_vs_all.diamond \
               --outfmt 6 \
               --threads 32 \
               --evalue 1e-5

# Use with orthomclBlastParser (same format)
```

**Parallelize BLAST:**
```bash
# Split FASTA into chunks
split -n l/16 goodProteins.fasta chunk_

# Run BLAST in parallel on each chunk
for chunk in chunk_*; do
  blastp -query $chunk -db goodProteins \
         -out ${chunk}.blast -outfmt 6 \
         -evalue 1e-5 -num_threads 4 &
done
wait

# Combine results
cat chunk_*.blast > all_vs_all.blast
```

**Database Optimization:**
```sql
-- Add indexes to MySQL database
CREATE INDEX idx_query ON SimilarSequences(query_id);
CREATE INDEX idx_subject ON SimilarSequences(subject_id);
```

### Memory Management

**MCL Memory Usage:**
```bash
# MCL can use lots of RAM for large datasets
# Monitor memory and adjust system limits if needed

# For very large datasets, increase swap space
# or run on high-memory node
```

**Database Memory:**
```sql
-- Optimize MySQL for large BLAST tables
SET GLOBAL innodb_buffer_pool_size = 8G;
SET GLOBAL max_allowed_packet = 1G;
```

## Parameter Recommendations

### Same Species (Strain-Level)
```ini
# High stringency for close relatives
percentIdentityCutoff=95
percentMatchCutoff=90
similarityCutoff=1e-10
# MCL inflation: 1.5
```

### Same Genus (Species-Level)
```ini
# Moderate stringency
percentIdentityCutoff=70
percentMatchCutoff=70
similarityCutoff=1e-7
# MCL inflation: 2.0
```

### Distant Relatives (Cross-Genus)
```ini
# Relaxed stringency
percentIdentityCutoff=30
percentMatchCutoff=50
similarityCutoff=1e-5
# MCL inflation: 2.5-3.0
```

### MCL Inflation Parameter
- **1.2-1.5**: Larger orthogroups (under-splitting, faster)
- **2.0**: Balanced (default for most applications)
- **3.0-4.0**: Smaller orthogroups (over-splitting, conservative)

## Troubleshooting

### Database Connection Errors
```bash
# Test MySQL connection
mysql -u orthomcl -p orthomcl

# Verify schema installation
orthomclInstallSchema orthomcl.config

# Check user permissions
GRANT ALL PRIVILEGES ON orthomcl.* TO 'orthomcl'@'localhost';
```

### FASTA Compliance Errors
```bash
# Common issues:
# - Headers too long (>60 chars after |)
# - Non-standard amino acids
# - Duplicate IDs

# Fix with orthomclAdjustFasta
orthomclAdjustFasta genome1 genome1.faa 1

# Or manually edit headers
# Format: >speciesTag|proteinID
```

### Too Few/Many Orthogroups
- **Too few**: Increase MCL inflation (3.0-4.0)
- **Too many**: Decrease MCL inflation (1.5-2.0)
- **No orthologs**: Lower identity/coverage cutoffs

### BLAST Parsing Errors
```bash
# Ensure BLAST format is tab-delimited (-outfmt 6)
# Check for complete BLAST output (no truncation)

# Re-run BLAST if necessary
blastp -query goodProteins.fasta \
       -db goodProteins \
       -out all_vs_all.blast \
       -outfmt 6 \
       -evalue 1e-5
```

### Out of Memory (MCL)
```bash
# Use smaller inflation parameter
mcl mclInput --abc -I 1.5 -o mclOutput

# Or split into smaller batches
# Process subsets of genomes separately
```

## Key Features

### OrthoMCL Advantages
- **Reciprocal Best Hits**: Gold standard for ortholog detection
- **MCL Clustering**: Robust graph-based approach
- **Paralog Discrimination**: Identifies in-paralogs vs out-paralogs
- **Database Integration**: Structured storage for large-scale analysis
- **Well-Established**: Widely used and cited (>10,000 citations)

### Limitations
- **Database Requirement**: Needs MySQL/Oracle setup
- **Installation Complexity**: More dependencies than alternatives
- **Speed**: Slower than MMseqs2 or Diamond-based tools
- **Maintenance**: Less actively developed than newer tools

### Comparison with Other Tools
- **vs OrthoFinder**: Less phylogenetic detail, no gene trees
- **vs ProteinOrtho**: More accurate but more complex setup
- **vs MMseqs2**: More rigorous ortholog definition, slower

## Benchmarks
- **Scalability**: Tested on 100+ genomes
- **Database Size**: Can handle millions of BLAST hits
- **Runtime**: ~1-24 hours depending on dataset size and hardware
- **Accuracy**: High specificity for true orthologs

## Alternative: OrthoMCL-DB Online
For small datasets, use the online version:
- Website: https://orthomcl.org/orthomcl/
- Upload protein sequences
- No local installation required
- Limited to smaller datasets
