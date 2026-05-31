# Supplementary Tool Guide

Last verified: 2026-05-30
Tool version/release checked: SeqKit v2.13.0; MMseqs2 18-8cc5c; NCBI BLAST+ 2.17.0+; Biopython 1.87; DIAMOND v2.2.1; HMMER v3.4; pyhmmer 0.12.0
Official docs/manual: https://bioinf.shenwei.me/seqkit/; https://mmseqs.com/latest/userguide.pdf; https://www.ncbi.nlm.nih.gov/books/NBK279690/; https://blast.ncbi.nlm.nih.gov/doc/blast-help/downloadblastdata.html; https://biopython.org/wiki/Documentation; https://github.com/bbuchfink/diamond; https://hmmer.org/documentation.html; https://pyhmmer.readthedocs.io/
Release/source: https://github.com/shenwei356/seqkit/releases/tag/v2.13.0; https://github.com/soedinglab/MMseqs2/releases/tag/18-8cc5c; https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/; https://biopython.org/wiki/Download; https://github.com/bbuchfink/diamond/releases/tag/v2.2.1; https://hmmer.org/; https://github.com/althonos/pyhmmer/releases/tag/v0.12.0

Use this page for version-grounded command examples when curating FASTA/FAA databases for BLAST, DIAMOND, MMseqs2, HMMER, or Python-based checks.

## Version Summary

| Tool | Version checked | Use in this skill |
|---|---:|---|
| SeqKit | v2.13.0 | FASTA/FASTQ inspection, normalization, statistics |
| MMseqs2 | 18-8cc5c | sequence database creation, clustering/search prep |
| NCBI BLAST+ | 2.17.0+ | `makeblastdb` for BLAST-compatible databases |
| Biopython | 1.87 | scripted FASTA/GenBank parsing and writing |
| DIAMOND | v2.2.1 | BLAST-compatible protein database creation/search |
| HMMER | v3.4 | profile HMM database indexing/search compatibility |
| pyhmmer | 0.12.0 | Python-native HMMER-compatible sequence/profile handling |

## Commands

### Inspect and normalize FASTA with SeqKit

```bash
seqkit stats -a database.faa
seqkit seq -w 0 database.faa > database.singleline.faa
seqkit grep -nrp " " database.faa | head
```

### Build MMseqs2 databases

```bash
mmseqs createdb proteins.faa mmseqs/proteins_db
mmseqs createindex mmseqs/proteins_db tmp
```

### Build BLAST+ databases

```bash
makeblastdb -in proteins.faa -dbtype prot -parse_seqids \
  -out blast/proteins
```

For nucleotide FASTA:

```bash
makeblastdb -in contigs.fna -dbtype nucl -parse_seqids \
  -out blast/contigs
```

### Build DIAMOND databases

```bash
diamond makedb --in proteins.faa -d diamond/proteins
```

### Prepare HMMER profile databases

```bash
hmmpress markers.hmm
hmmscan --cpu 8 --tblout hits.tbl markers.hmm proteins.faa
```

### Scripted FASTA/GenBank conversion with Biopython

```python
from Bio import SeqIO

with open("records.fna", "w") as out:
    SeqIO.write(SeqIO.parse("records.gb", "genbank"), out, "fasta")
```

## Provenance To Record

- Tool name and exact version from `--version` or package metadata.
- Source FASTA/FAA/GenBank file paths, checksums, and download URLs.
- Header transformation rules and original-to-new ID mapping path.
- Deduplication key (`id`, normalized sequence, checksum, or both).
- Downstream database command line and output prefix.
