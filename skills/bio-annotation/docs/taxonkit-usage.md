# TaxonKit Usage Guide

Last verified: 2026-05-30
Tool version/release checked: TaxonKit v0.20.0
Official docs/manual: https://bioinf.shenwei.me/taxonkit/usage/
Release/source: https://github.com/shenwei356/taxonkit/releases/tag/v0.20.0

## Overview

TaxonKit is a practical and efficient command-line toolkit for comprehensive manipulation of NCBI Taxonomy data. It is implemented in Go and provides cross-platform support with fast performance.

## Official Documentation

- Official Website: https://bioinf.shenwei.me/taxonkit/
- GitHub Repository: https://github.com/shenwei356/taxonkit
- Usage Documentation: https://bioinf.shenwei.me/taxonkit/usage/
- Releases: https://github.com/shenwei356/taxonkit/releases
- Citation: https://doi.org/10.1016/j.jgg.2021.03.006 (Journal of Genetics and Genomics 2021)

## Installation

### Binary Download
```bash
# Download from GitHub releases
wget https://github.com/shenwei356/taxonkit/releases/download/v0.20.0/taxonkit_linux_amd64.tar.gz
tar -zxvf taxonkit_linux_amd64.tar.gz
```

### Pixi
```bash
pixi add taxonkit
```

### Go Install
```bash
go install github.com/shenwei356/taxonkit@latest
```

## Database Setup

### Download NCBI Taxonomy Data
```bash
# Download taxdump
wget ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz
tar -zxvf taxdump.tar.gz

# Create data directory
mkdir -p ~/.taxonkit

# Copy required files
cp names.dmp nodes.dmp delnodes.dmp merged.dmp ~/.taxonkit/
```

### Custom Data Directory
```bash
# Set environment variable
export TAXONKIT_DB=/path/to/taxdump

# Or use --data-dir flag
taxonkit --data-dir /path/to/taxdump <command>
```

## Key Commands

### lineage - Query Taxonomic Lineage
```bash
# Get lineage for TaxIDs
echo "9606" | taxonkit lineage
# Output: 9606    cellular organisms;Eukaryota;Opisthokonta;Metazoa;...

# With taxonomic names
echo "9606" | taxonkit lineage -n
```

### reformat2 - Reformat Lineage
```bash
# Domain-aware seven-rank format
echo "9606" | taxonkit lineage | \
  taxonkit reformat2 \
    -f "{domain|acellular root|superkingdom};{phylum};{class};{order};{family};{genus};{species}"
# Output: 9606    ...    Eukaryota;Chordata;Mammalia;Primates;Hominidae;Homo;Homo sapiens

# Custom format
echo "9606" | taxonkit lineage | \
  taxonkit reformat2 -f "{domain|acellular root|superkingdom};{phylum};{genus};{species}"
```

### name2taxid - Convert Names to TaxIDs
```bash
# Convert scientific names to TaxIDs
echo "Homo sapiens" | taxonkit name2taxid
# Output: Homo sapiens    9606

# From file
taxonkit name2taxid species_names.txt -o species_taxids.txt
```

### list - List Taxonomic Subtrees
```bash
# List all descendants of a TaxID
taxonkit list --ids 9606

# With taxonomic names and indentation
taxonkit list --ids 9606 -n -r --indent "  "
```

### filter - Filter TaxIDs by Rank Range
```bash
# Filter at genus rank and below
cat taxids.txt | taxonkit filter -L genus

# Filter at specific rank
cat taxids.txt | taxonkit filter -E species

# Filter between ranks
cat taxids.txt | taxonkit filter -L genus -H species
```

### lca - Compute Lowest Common Ancestor
```bash
# Compute LCA for multiple TaxIDs
echo "9606,9597" | taxonkit lca
# Output: LCA of 9606,9597: 9604 (Hominidae)
```

## Key Command-Line Options

### Global Options
- `--data-dir` - Directory containing NCBI taxonomy files (default: ~/.taxonkit)
- `--threads (-j)` - Number of CPUs (default: 4)
- `--out-file (-o)` - Output file (default: stdout)
- `--verbose` - Print verbose information
- `--line-buffered` - Use line buffering for immediate output

### Lineage Options
- `-n, --show-name` - Show scientific name
- `-r, --show-rank` - Show taxonomic rank
- `-t, --show-lineage-taxids` - Append the lineage as TaxIDs
- `-R, --show-lineage-ranks` - Append the rank of every lineage level
- `-c, --show-status-code` - Show status code before the lineage
- `-L, --no-lineage` - Omit the lineage (names or ranks only)

### Reformat Options
`reformat2` accepts TaxIDs only (field set with `-I`, default 1):
- `-f, --format` - Output format with full rank names; `{a|b}` takes the first rank present, which handles the March 2025 NCBI change from `superkingdom` to `domain` and `acellular root`
- `-r, --miss-rank-repl` - Replacement for missing ranks
- `-R, --miss-taxid-repl` - Replacement for missing TaxIDs
- `-t, --show-lineage-taxids` - Append the TaxIDs of the reformatted lineage
- `-T, --trim` - Do not fill missing ranks below the rank of the current node

Classic `reformat` keeps `-F, --fill-miss-rank` and `-P, --add-prefix`; `reformat2` has neither.

### Name2taxid Options
- `-s, --sci-name` - Only search scientific names
- `-r, --show-rank` - Show taxonomic rank

### List Options
- `-i, --ids` - Comma-separated TaxIDs
- `-n, --show-name` - Show scientific names
- `-r, --show-rank` - Show taxonomic ranks
- `--indent` - Indent string for tree display

### Filter Options
- `-E, --equal-to` - Filter at specific rank
- `-L, --lower-than` - Keep TaxIDs with rank lower than the given rank (the rank itself is excluded)
- `-H, --higher-than` - Keep TaxIDs with rank higher than the given rank (the rank itself is excluded)
- `-N, --discard-noranks` - Discard TaxIDs whose rank has no order
- `-n, --save-predictable-norank` - With `-L`, keep unranked TaxIDs whose closest ranked ancestor is below the cutoff

## Common Usage Examples

### Resolve taxonomy from DIAMOND output
```bash
# Extract TaxIDs from DIAMOND results run with
# --outfmt 6 qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore staxids
cut -f13 diamond_results.tsv | \
  taxonkit lineage -n -r | \
  taxonkit reformat2 \
    -f "{domain|acellular root|superkingdom};{phylum};{class};{order};{family};{genus};{species}" > taxonomy.tsv
```

### Get full lineage with names
```bash
echo "562" | taxonkit lineage -n -r -R
# Escherichia coli with its full lineage, its rank, and the rank of every lineage level
```

### Convert list of species names
```bash
cat species_list.txt | \
  taxonkit name2taxid | \
  taxonkit lineage | \
  taxonkit reformat2 \
    -f "{domain|acellular root|superkingdom};{phylum};{class};{order};{family};{genus};{species}" > species_taxonomy.tsv
```

### Keep TaxIDs below genus
```bash
cat all_taxids.txt | \
  taxonkit filter -L genus | \
  taxonkit lineage -n -r > genus_and_species.tsv
```

### Create taxonomic summary
```bash
# Get all bacterial species
echo "2" | taxonkit list --ids 2 | \
  taxonkit filter -E species | \
  taxonkit lineage -n -r > bacteria_species.tsv
```

### LCA for sequence clusters
```bash
# Find common ancestor for TaxIDs in a cluster
echo "9606,9597,9598" | taxonkit lca -d ","
```

## Input/Output Formats

### Input
- **TaxIDs**: Plain text, one per line or comma-separated
- **Names**: Scientific names, one per line
- **Stdin**: Pipeline-friendly, accepts piped input

### Output
- **Tab-separated**: Default output format
- **Custom delimiters**: Configurable with `-d`
- **Formatted lineage**: Seven-rank format or custom

## Reformat Format String

Use `reformat2` for current NCBI taxonomy because v0.20.0 handles the March
2025 rank update from `superkingdom` to `domain` and adds viral `realm`.
Classic `reformat` with short placeholders (`{k};{p};...`) is retained for
legacy seven-rank output.

Example formats:
```bash
# Domain-aware seven-rank output
-f "{domain|acellular root|superkingdom};{phylum};{class};{order};{family};{genus};{species}"

# With rank prefixes
-f "{domain};{phylum};{class};{order};{family};{genus};{species}" -P

# Custom separator
-f "{domain|acellular root|superkingdom}|{phylum}|{class}|{order}|{family}|{genus}|{species}"
```

## Performance Tips

1. **Use appropriate thread count**: Set `-j` to available CPU cores
2. **Keep data local**: Place taxdump in fast storage (SSD)
3. **Use line buffering**: Add `--line-buffered` for real-time output in pipelines
4. **Batch processing**: Process multiple TaxIDs together rather than one at a time
5. **Cache lookups**: TaxonKit caches taxonomy data in memory for fast repeated queries
6. **Pre-filter TaxIDs**: Remove duplicates before processing to avoid redundant lookups
7. **Use specific commands**: Use `filter` before `lineage` to reduce processing

## Workflow Integration

### DIAMOND + TaxonKit Pipeline
```bash
# Run DIAMOND with taxonomy.
# Prefer clusterednr.dmnd over full nr.dmnd when available (check $BIO_DB_ROOT
# first; build from a clustered nr FASTA if missing) — far faster, comparable
# taxonomy assignment quality for typical annotation tasks.
diamond blastp --query proteins.faa --db clusterednr.dmnd \
  --out results.tsv --outfmt 6 qseqid sseqid staxids evalue bitscore \
  --threads 32

# Extract and resolve taxonomy
cut -f3 results.tsv | \
  taxonkit lineage -n -r | \
  taxonkit reformat2 \
    -f "{domain|acellular root|superkingdom};{phylum};{class};{order};{family};{genus};{species}" | \
  paste results.tsv - > results_with_taxonomy.tsv
```

DIAMOND tabular output has no header unless one is added explicitly. Do not drop
the first line before TaxonKit, or the first hit and its taxonomy row will be
lost.

### Create taxonomic summary report
```bash
# Count sequences per phylum
cut -f3 results.tsv | \
  taxonkit lineage | \
  taxonkit reformat2 -f "{phylum}" | \
  cut -f3 | \
  sort | uniq -c | \
  sort -rn > phylum_counts.txt
```

### Handle missing TaxIDs
```bash
# Fill missing ranks with "unclassified"
echo "12345" | \
  taxonkit lineage | \
  taxonkit reformat2 \
    -f "{domain|acellular root|superkingdom};{phylum};{class};{order};{family};{genus};{species}" \
    -r "unclassified"
```

## Troubleshooting

### Update taxonomy database
```bash
# Download latest taxdump
cd ~/.taxonkit
wget ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz
tar -zxvf taxdump.tar.gz --overwrite
```

### Handle merged/deleted TaxIDs
```bash
# TaxonKit automatically handles merged and deleted TaxIDs
# using merged.dmp and delnodes.dmp
```

### Check TaxonKit version
```bash
taxonkit version
```

## Version Information

This documentation was verified against TaxonKit v0.20.0 and the official usage documentation/release notes on 2026-05-30.
