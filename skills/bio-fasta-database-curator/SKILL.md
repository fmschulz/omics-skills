---
name: bio-fasta-database-curator
description: "Curate, validate, and standardize FASTA/FAA sequence databases: standardize headers, merge databases, remove duplicates, convert GenBank to FASTA, and generate statistics. Use when preparing reference databases for HMM searches, MMseqs2, BLAST, and other bioinformatics workflows."
---

# FASTA Database Curator

## Overview

Automate the curation and standardization of biological sequence databases. This skill handles the tedious work of processing FASTA/FAA files, ensuring consistent header formats, removing duplicates, and preparing databases for downstream analysis.

**Key Capabilities:**
- Header format standardization (pipe separators, prefixes)
- Duplicate detection and removal (by sequence or ID)
- Format conversion (GenBank → FASTA, multi-line → single-line)
- Database merging with conflict resolution
- Statistics generation (counts, lengths, taxonomy, GC content)
- Validation (no whitespace in headers, proper formatting)
- Taxonomy label extraction and standardization

## When to Use This Skill

Use this skill when:
- User needs to standardize sequence headers
- User wants to merge multiple FASTA files
- User needs to remove duplicate sequences
- User is preparing a database for HMM/BLAST/MMseqs2
- User wants database statistics and quality metrics
- User needs to convert between sequence formats

## Header Format Standards

### Recommended Format

Use pipe-separated fields with consistent prefixes:

```
>PREFIX|ACCESSION|DESCRIPTION
SEQUENCE...
```

**Examples:**
```
>VP|Mavirus_MCP|Major capsid protein [Virophage]
>PLV|NC_021333_1|Polinton-like virus hypothetical protein
>NCLDV|YP_009173877.1|DNA polymerase [Marseilleviridae]
```

### Common Transformations

```python
# Remove whitespace from headers
old: ">VP_MCP Mavirus major capsid protein"
new: ">VP_MCP|Mavirus_major_capsid_protein"

# Add taxonomy prefix
old: ">NC_021333.1 hypothetical protein"
new: ">PLV|NC_021333.1|hypothetical_protein"

# Standardize separators
old: ">seq1 [organism=Virus] protein"
new: ">seq1|Virus|protein"
```

## Quick Reference

| Task | Action |
|------|--------|
| Inspect database | Count records, sample headers, check whitespace and length distribution before changing anything. |
| Standardize headers | Define deterministic transformation rules and preserve original-to-new ID mapping. |
| Merge or deduplicate | Decide whether duplicates are removed by ID, sequence, or both, then report what changed. |
| Validate output | Re-count records, verify FASTA syntax, and write database statistics. |

## Instructions

### Step 1: Analyze Input Database

First, understand what you're working with:

```bash
# Count sequences
grep -c "^>" database.fasta

# Sample headers (first 20)
grep "^>" database.fasta | head -20

# Check for problematic characters
grep "^>" database.fasta | grep -E "[\t ]" | head -10

# Sequence length distribution
awk '/^>/ {if (seq) print length(seq); seq=""} !/^>/ {seq=seq$0} END {print length(seq)}' database.fasta | sort -n | uniq -c
```

### Step 2: Define Transformation Rules

Based on the source database, define rules:

```python
# Example transformation rules
rules = {
    "header_separator": "|",           # Use pipe as field separator
    "prefix": "VP",                    # Add prefix to all sequences
    "remove_whitespace": True,         # Replace spaces with underscores
    "fields_to_keep": ["accession", "description"],
    "taxonomy_source": "description",  # Extract taxonomy from description
}
```

### Step 3: Process Sequences

```python
from Bio import SeqIO
import re

def standardize_header(header: str, rules: dict) -> str:
    """Standardize a FASTA header according to rules."""
    # Remove > prefix
    header = header.lstrip(">")

    # Split on common separators
    parts = re.split(r'[\s\|]+', header, maxsplit=2)

    # Apply prefix
    if rules.get("prefix"):
        parts[0] = f"{rules['prefix']}|{parts[0]}"

    # Remove whitespace from all parts
    if rules.get("remove_whitespace"):
        parts = [p.replace(" ", "_") for p in parts]

    # Rejoin with standard separator
    sep = rules.get("header_separator", "|")
    return sep.join(parts)

def process_database(input_path: str, output_path: str, rules: dict):
    """Process a FASTA database with standardization rules."""
    with open(output_path, 'w') as out:
        for record in SeqIO.parse(input_path, "fasta"):
            new_id = standardize_header(record.description, rules)
            out.write(f">{new_id}\n{str(record.seq)}\n")
```

### Step 4: Remove Duplicates

```python
def deduplicate_by_sequence(input_path: str, output_path: str):
    """Remove sequences with identical sequences, keeping first occurrence."""
    seen_seqs = set()
    with open(output_path, 'w') as out:
        for record in SeqIO.parse(input_path, "fasta"):
            seq_hash = hash(str(record.seq).upper())
            if seq_hash not in seen_seqs:
                seen_seqs.add(seq_hash)
                out.write(f">{record.description}\n{str(record.seq)}\n")
    return len(seen_seqs)

def deduplicate_by_id(input_path: str, output_path: str):
    """Remove sequences with duplicate IDs, keeping first occurrence."""
    seen_ids = set()
    with open(output_path, 'w') as out:
        for record in SeqIO.parse(input_path, "fasta"):
            if record.id not in seen_ids:
                seen_ids.add(record.id)
                out.write(f">{record.description}\n{str(record.seq)}\n")
    return len(seen_ids)
```

### Step 5: Merge Databases

```python
def merge_databases(input_paths: list, output_path: str,
                   deduplicate: bool = True):
    """Merge multiple FASTA files into one."""
    all_records = []
    seen_ids = set()

    for path in input_paths:
        for record in SeqIO.parse(path, "fasta"):
            if deduplicate and record.id in seen_ids:
                continue
            seen_ids.add(record.id)
            all_records.append(record)

    with open(output_path, 'w') as out:
        for record in all_records:
            out.write(f">{record.description}\n{str(record.seq)}\n")

    return len(all_records)
```

### Step 6: Generate Statistics

```python
def generate_stats(input_path: str) -> dict:
    """Generate comprehensive database statistics."""
    from collections import Counter

    stats = {
        "total_sequences": 0,
        "total_residues": 0,
        "lengths": [],
        "prefixes": Counter(),
        "gc_content": [],  # For nucleotide
    }

    for record in SeqIO.parse(input_path, "fasta"):
        stats["total_sequences"] += 1
        seq_len = len(record.seq)
        stats["total_residues"] += seq_len
        stats["lengths"].append(seq_len)

        # Extract prefix
        prefix = record.id.split("|")[0] if "|" in record.id else "none"
        stats["prefixes"][prefix] += 1

        # GC content for nucleotides
        seq_upper = str(record.seq).upper()
        if set(seq_upper) <= set("ATGCN"):
            gc = (seq_upper.count("G") + seq_upper.count("C")) / len(seq_upper)
            stats["gc_content"].append(gc)

    # Calculate summary statistics
    lengths = stats["lengths"]
    stats["min_length"] = min(lengths)
    stats["max_length"] = max(lengths)
    stats["mean_length"] = sum(lengths) / len(lengths)
    stats["median_length"] = sorted(lengths)[len(lengths)//2]

    return stats

def format_stats_report(stats: dict, db_name: str) -> str:
    """Format statistics as markdown report."""
    report = f"""# Database Statistics: {db_name}

## Summary
- **Total sequences:** {stats['total_sequences']:,}
- **Total residues:** {stats['total_residues']:,}

## Sequence Lengths
- **Minimum:** {stats['min_length']:,}
- **Maximum:** {stats['max_length']:,}
- **Mean:** {stats['mean_length']:.1f}
- **Median:** {stats['median_length']:,}

## Prefix Distribution
| Prefix | Count | Percentage |
|--------|-------|------------|
"""
    total = stats['total_sequences']
    for prefix, count in stats['prefixes'].most_common():
        pct = count / total * 100
        report += f"| {prefix} | {count:,} | {pct:.1f}% |\n"

    return report
```

### Step 7: Validate Database

```python
def validate_database(input_path: str) -> list:
    """Validate database and return list of issues."""
    issues = []

    for i, record in enumerate(SeqIO.parse(input_path, "fasta"), 1):
        # Check for whitespace in header
        if " " in record.id or "\t" in record.id:
            issues.append(f"Line {i}: Whitespace in ID '{record.id}'")

        # Check for empty sequences
        if len(record.seq) == 0:
            issues.append(f"Line {i}: Empty sequence for '{record.id}'")

        # Check for invalid characters (protein)
        valid_aa = set("ACDEFGHIKLMNPQRSTVWXY*-")
        invalid = set(str(record.seq).upper()) - valid_aa
        if invalid:
            issues.append(f"Line {i}: Invalid characters {invalid} in '{record.id}'")

        # Check header format
        if "|" not in record.description:
            issues.append(f"Line {i}: Non-standard header format for '{record.id}'")

    return issues
```

## Input Requirements

- One or more FASTA, FAA, FNA, FFN, or GenBank files.
- Desired header convention, prefix policy, and duplicate-removal rule.
- Taxonomy labels or accession metadata when headers need biological grouping.
- Downstream tool constraints, such as BLAST, DIAMOND, MMseqs2, HMMER, or pyhmmer header behavior.

## Output

- Curated FASTA/FAA database with stable identifiers.
- Header mapping table from original IDs to curated IDs.
- Deduplication report with retained and removed records.
- Summary statistics for record count, length distribution, sequence alphabet, prefix/taxonomy counts, and GC content when nucleotide sequences are used.
- Validation notes documenting any skipped transformations or unresolved IDs.

## Quality Gates

- [ ] Every output header is unique and contains no whitespace.
- [ ] Original-to-curated ID mapping is written before destructive transformations.
- [ ] Duplicate policy is explicit: by ID, by sequence, or by both.
- [ ] FASTA parser can read the curated database end-to-end.
- [ ] Record counts before and after curation match the deduplication and filtering report.

## Format Conversions

### GenBank to FASTA

```python
from Bio import SeqIO

def genbank_to_fasta(input_gb: str, output_fasta: str):
    """Convert GenBank format to FASTA."""
    records = SeqIO.parse(input_gb, "genbank")
    count = SeqIO.write(records, output_fasta, "fasta")
    return count
```

### Multi-line to Single-line FASTA

```bash
# Using awk
awk '/^>/ {if (seq) print seq; print; seq=""} !/^>/ {seq=seq$0} END {print seq}' multi.fasta > single.fasta
```

### Extract CDS from GenBank

```python
def extract_cds_proteins(input_gb: str, output_faa: str):
    """Extract CDS translations from GenBank file."""
    with open(output_faa, 'w') as out:
        for record in SeqIO.parse(input_gb, "genbank"):
            for feature in record.features:
                if feature.type == "CDS":
                    if "translation" in feature.qualifiers:
                        protein = feature.qualifiers["translation"][0]
                        locus = feature.qualifiers.get("locus_tag", ["unknown"])[0]
                        product = feature.qualifiers.get("product", ["unknown"])[0]
                        out.write(f">{locus}|{product}\n{protein}\n")
```

## Best Practices

### 1. Always Backup Originals
```bash
cp original.fasta original.fasta.bak
```

### 2. Validate Before Processing
Check header formats and sequence content before bulk operations.

### 3. Use Consistent Prefixes
Define a taxonomy prefix scheme and stick to it:
- `VP_` for virophages
- `PLV_` for polinton-like viruses
- `NCLDV_` for NCLDVs
- `MIRUS_` for Mirus viruses

### 4. Document Transformations
Keep a log of all transformations applied to the database.

### 5. Generate Statistics After Processing
Always verify the output database matches expectations.

## Examples

```
User: "Standardize the headers in virophage_raw.fasta and remove duplicates"

1. Analyze input:
   - 1,869 sequences
   - Headers have spaces and inconsistent formats
   - Some duplicate accessions

2. Define rules:
   - Add VP| prefix
   - Replace spaces with underscores
   - Use pipe separator

3. Process and deduplicate:
   - Standardized 1,869 headers
   - Removed 23 duplicates
   - Final: 1,846 unique sequences

4. Validate output:
   - No whitespace in headers ✓
   - All sequences non-empty ✓
   - Consistent format ✓

5. Generate stats report
```

## Troubleshooting

### Whitespace in Headers
**Problem:** BLAST/MMseqs2 truncate at first whitespace
**Solution:** Replace spaces with underscores or pipes

### Duplicate IDs
**Problem:** Same accession from different sources
**Solution:** Add source prefix to disambiguate

### Invalid Characters
**Problem:** Non-standard amino acid codes
**Solution:** Replace with X or remove sequences

### Mixed Case Sequences
**Problem:** Inconsistent case in sequences
**Solution:** Standardize to uppercase
