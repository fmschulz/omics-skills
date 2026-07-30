---
name: bio-fasta-database-curator
description: Curate and validate FASTA or FAA databases. Use when standardizing headers, merging references, deduplicating sequences, converting GenBank files, or preparing BLAST, MMseqs2, and HMM inputs.
---

# FASTA Database Curator

## Overview

Automate the curation and standardization of biological sequence databases. This skill handles the tedious work of processing FASTA/FAA files, ensuring consistent header formats, removing duplicates, and preparing databases for downstream analysis.

Supplementary version-grounded tool notes: [tools.md](tools.md).

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
| Run the bundled curator | `uv run --script scripts/curate_fasta.py input.fasta --output curated.fasta --prefix REF --deduplicate both` |

## Instructions

Use `scripts/curate_fasta.py` for routine FASTA curation. It parses raw headers
before any library can truncate them, uses SHA-256 sequence digests, refuses
empty inputs and existing outputs, and writes both a header mapping and a JSON
deduplication report. Keep the snippets below for custom transformations only.

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

### Step 2: Curate with the Bundled Script

The script standardizes headers, merges multiple inputs, deduplicates, and writes the mapping and report in one pass:

```bash
uv run --no-project python scripts/curate_fasta.py \
  input1.fasta input2.fasta \
  --output curated.fasta \
  --mapping header_mapping.tsv \
  --report dedup_report.json \
  --prefix REF \
  --deduplicate both        # id | sequence | both
```

Write custom Biopython transformations only when a rule falls outside the script's flags, and keep the original-to-new ID mapping in that case too.

### Step 3: Generate Statistics and Validate

Use SeqKit (versions and more commands in [tools.md](tools.md)) for statistics, then verify parseability, alphabet, and the prefix distribution in one pass:

```bash
seqkit stats -a curated.fasta               # counts, length distribution, sequence type
seqkit grep -nrp " " curated.fasta | head   # must return nothing: no whitespace in headers
uv run --with biopython python3 - <<'EOF'   # parse end-to-end, flag invalid residues, count prefixes
from Bio import SeqIO
from collections import Counter
valid = set("ACDEFGHIKLMNPQRSTVWYXBZJUO*-")  # adjust to ACGTUN*- for nucleotide databases
prefixes, bad = Counter(), []
n = 0
for rec in SeqIO.parse("curated.fasta", "fasta"):
    n += 1
    prefixes[rec.id.split("|")[0] if "|" in rec.id else "none"] += 1
    extra = set(str(rec.seq).upper()) - valid
    if extra:
        bad.append((rec.id, "".join(sorted(extra))))
print(f"records: {n}")
print("prefix counts:", dict(prefixes))
print("invalid residues:", bad if bad else "none")
EOF
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
seqkit seq -w 0 multi.fasta > single.fasta
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

- Define a taxonomy prefix scheme and stick to it (e.g. `VP|` virophages, `PLV|` polinton-like viruses, `NCLDV|` NCLDVs, `MIRUS|` Mirus viruses).
- Keep the header mapping and deduplication report with the database so every transformation stays auditable.
- Re-run statistics after processing and compare against the pre-curation counts.

## Examples

```bash
uv run --script scripts/curate_fasta.py \
  fixtures/mixed-headers.fasta \
  --output curated.fasta \
  --prefix REF \
  --deduplicate both
```

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
   - No whitespace in headers OK
   - All sequences non-empty OK
   - Consistent format OK

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
