---
name: bio-fasta-database-curator
description: Curate and validate FASTA or FAA databases. Use when standardizing headers, merging or deduplicating references, converting GenBank, or preparing BLAST, MMseqs2, or HMM inputs.
---

# FASTA Database Curator

Curate FASTA/FAA reference databases: standardize headers, merge files, remove duplicates, and validate the result for BLAST, DIAMOND, MMseqs2, or HMMER. Every transformation leaves a header mapping and a deduplication report.

Supplementary version-grounded tool notes: [tools.md](tools.md).

## Header Format Standards

### Recommended Format

Use pipe-separated fields with a consistent source prefix:

```
>PREFIX|ACCESSION|DESCRIPTION
SEQUENCE...
```

**Examples:**
```
>VP|Mavirus_MCP|Major_capsid_protein_[Virophage]
>PLV|NC_021333_1|Polinton-like_virus_hypothetical_protein
>NCLDV|YP_009173877.1|DNA_polymerase_[Marseilleviridae]
```

### What the bundled script does

`scripts/curate_fasta.py` keeps the whole raw header, replaces each whitespace run and each character outside `A-Za-z0-9_.|:-` with `_`, collapses repeated `_`, and prepends `PREFIX|` when `--prefix` is set:

```
>seq 1 alpha protein          ->  >REF|seq_1_alpha_protein
>NC_021333.1 hypothetical     ->  >REF|NC_021333.1_hypothetical
```

Split accession and description into separate pipe fields with a custom rule, and keep the mapping table for it as well.

BLAST `makeblastdb -parse_seqids` reads `|` as NCBI seq-id syntax and fails on custom prefixes such as `VP|...` ("Could not construct seq-id"). Build pipe-delimited databases without `-parse_seqids`. DIAMOND, MMseqs2, and HMMER keep the full first word of the header.

## Quick Reference

| Task | Action |
|------|--------|
| Inspect database | Count records, sample headers, check whitespace and length distribution before changing anything. |
| Standardize headers | Define deterministic transformation rules and preserve original-to-new ID mapping. |
| Merge or deduplicate | Decide whether duplicates are removed by ID, sequence, or both, then report what changed. |
| Validate output | Re-count records, verify FASTA syntax, and write database statistics. |
| Run the bundled curator | `uv run --script skills/bio-fasta-database-curator/scripts/curate_fasta.py input.fasta --output curated.fasta --prefix REF --deduplicate both` |
| Build search databases | Commands for `makeblastdb`, `diamond makedb`, `mmseqs createdb`, and `hmmpress` in [tools.md](tools.md). |

## Instructions

Use `scripts/curate_fasta.py` for routine FASTA curation. It parses raw headers
before any library can truncate them, uppercases sequences, uses SHA-256
sequence digests, refuses empty inputs, empty records, and existing outputs,
and writes a header mapping and a JSON deduplication report. A retained record
whose curated ID repeats an earlier one gets a `|record_N` suffix. Keep the
snippets below for custom transformations only.

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
uv run --script skills/bio-fasta-database-curator/scripts/curate_fasta.py \
  input1.fasta input2.fasta \
  --output curated.fasta \
  --mapping header_mapping.tsv \
  --report dedup_report.json \
  --prefix REF \
  --deduplicate both        # none | id | sequence | both
```

Without `--mapping` and `--report`, the script writes `curated.fasta.mapping.tsv` and `curated.fasta.report.json` next to the output.

Write custom Biopython transformations only when a rule falls outside the script's flags, and keep the original-to-new ID mapping in that case too.

### Step 3: Generate Statistics and Validate

Use SeqKit (versions and more commands in [tools.md](tools.md)) to parse every record, check the alphabet, and summarize; count prefixes from the headers:

```bash
seqkit stats -a -T curated.fasta              # counts, length distribution, sequence type, GC(%)
seqkit seq -t protein --validate-seq curated.fasta > /dev/null   # nonzero exit on an invalid residue; -t dna for nucleotides
seqkit grep -nrp " " curated.fasta | head     # must return nothing: no whitespace in headers
grep '^>' curated.fasta | cut -c2- | cut -d'|' -f1 | sort | uniq -c   # records per prefix
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
                        product = "_".join(product.split())  # no whitespace in IDs
                        out.write(f">{locus}|{product}\n{protein}\n")
```

## Best Practices

- Define a taxonomy prefix scheme and stick to it (e.g. `VP|` virophages, `PLV|` polinton-like viruses, `NCLDV|` NCLDVs, `MIRUS|` Mirus viruses).
- Keep the header mapping and deduplication report with the database so every transformation stays auditable.
- Re-run statistics after processing and compare against the pre-curation counts.

## Examples

```bash
uv run --script skills/bio-fasta-database-curator/scripts/curate_fasta.py \
  fixtures/mixed-headers.fasta \
  --output curated.fasta \
  --prefix REF \
  --deduplicate both
```

```
User: "Standardize the headers in virophage_raw.fasta and remove duplicates"

1. Analyze input: count records, sample headers, find whitespace and duplicate accessions.
2. Define rules: `VP|` prefix, whitespace to underscores, deduplicate by ID and sequence.
3. Run curate_fasta.py with --prefix VP --deduplicate both.
4. Validate: record counts match the report (input = retained + removed),
   no whitespace in headers, every record parses and is non-empty.
5. Report statistics from seqkit stats -a and the deduplication report.
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
