---
name: bio-fasta-database-curator
description: Curate and validate FASTA or FAA databases. Use when standardizing headers, merging or deduplicating references, converting GenBank, or preparing BLAST, MMseqs2, or HMM inputs.
disable-model-invocation: true
---

# FASTA Database Curator

Curate FASTA/FAA reference databases: standardize headers, merge files, remove duplicates, and validate the result for BLAST, DIAMOND, MMseqs2, or HMMER. Every transformation leaves a header mapping and a deduplication report. Shared pipeline rules: read `~/.agents/skills/omics-pipeline/SKILL.md` first (in a plugin install, `../omics-pipeline/SKILL.md` from this file).

Database-building commands (`makeblastdb`, `diamond makedb`, `mmseqs createdb`, `hmmpress`) and the versions they were checked against: [tools.md](tools.md).

## Header format

Use pipe-separated fields with a consistent source prefix, `>PREFIX|ACCESSION|DESCRIPTION`:

```
>VP|Mavirus_MCP|Major_capsid_protein_[Virophage]
>PLV|NC_021333_1|Polinton-like_virus_hypothetical_protein
>NCLDV|YP_009173877.1|DNA_polymerase_[Marseilleviridae]
```

Fix one prefix scheme and keep it (`VP|` virophages, `PLV|` polinton-like viruses, `NCLDV|` NCLDVs, `MIRUS|` Mirus viruses).

`scripts/curate_fasta.py` keeps the whole raw header, replaces each whitespace run and each character outside `A-Za-z0-9_.|:-` with `_`, collapses repeated `_`, and prepends `PREFIX|` when `--prefix` is set:

```
>seq 1 alpha protein          ->  >REF|seq_1_alpha_protein
>NC_021333.1 hypothetical     ->  >REF|NC_021333.1_hypothetical
```

To split accession and description into separate pipe fields, use a custom rule and keep its mapping table too.

BLAST `makeblastdb -parse_seqids` reads `|` as NCBI seq-id syntax and fails on custom prefixes such as `VP|...` ("Could not construct seq-id"). Build pipe-delimited databases without `-parse_seqids`. DIAMOND, MMseqs2, and HMMER keep the full first word of the header.

## Instructions

1. Inspect the input before you change it: record count, sample headers, whitespace, and length distribution (`seqkit stats -a`).
2. Curate with the bundled script. It parses raw headers before any library can truncate them, uppercases sequences, uses SHA-256 sequence digests, refuses empty inputs, empty records, and existing outputs, and writes a header mapping and a JSON deduplication report. A retained record whose curated ID repeats an earlier one gets a `|record_N` suffix.

   ```bash
   uv run --script ~/.agents/skills/bio-fasta-database-curator/scripts/curate_fasta.py \
     input1.fasta input2.fasta \
     --output curated.fasta \
     --mapping header_mapping.tsv \
     --report dedup_report.json \
     --prefix REF \
     --deduplicate both        # none | id | sequence | both
   ```

   Without `--mapping` and `--report`, the script writes `curated.fasta.mapping.tsv` and `curated.fasta.report.json` next to the output. For a rule outside the script's flags, write a custom transformation and keep the original-to-new ID mapping.
3. GenBank input: convert the CDS translations to FASTA with Biopython `SeqIO` first, with headers `locus_tag|product` and whitespace in the product replaced by `_`, then run the script.
4. Validate the output with SeqKit:

   ```bash
   seqkit stats -a -T curated.fasta                                # counts, lengths, sequence type, GC(%)
   seqkit seq -t protein --validate-seq curated.fasta > /dev/null  # nonzero exit on an invalid residue; -t dna for nucleotides
   seqkit grep -nrp " " curated.fasta | head                       # must return nothing: no whitespace in headers
   ```

## Input Requirements

- One or more FASTA, FAA, FNA, FFN, or GenBank files.
- The header convention, prefix policy, and duplicate-removal rule (by ID, by sequence, or both).
- Downstream tool constraints, such as BLAST, DIAMOND, MMseqs2, HMMER, or pyhmmer header behavior.

## Output

- Curated FASTA/FAA database with stable identifiers.
- Header mapping table from original IDs to curated IDs, and a deduplication report with retained and removed records.
- Validation notes for any skipped transformations or unresolved IDs.

## Quality Gates

- [ ] Every output header is unique and contains no whitespace.
- [ ] The ID mapping is written before any destructive transformation.
- [ ] The curated database parses end to end, and record counts before and after match the deduplication report (input = retained + removed).
