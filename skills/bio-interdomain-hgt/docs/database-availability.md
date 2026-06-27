# Database availability & build recipe (path-agnostic)

Last verified: 2026-06-27
Tool version/release checked: DIAMOND v2.2.x, MMseqs2 (linclust/cluster), geNomad v1.8+
Official docs/manual: https://github.com/bbuchfink/diamond/wiki
Release/source: https://github.com/bbuchfink/diamond/releases

HGT polarity is only meaningful if the reciprocal arbiter can see EVERY candidate
donor domain. Always resolve paths relative to `$BIO_DB_ROOT`; never hardcode
site-specific absolute paths into the analysis or the report.

## 1. The reciprocal-arbiter proteome (required)

One protein search database that spans all domains, with a lineage labels table.

Required properties:
- Contains eukaryotes, bacteria, archaea, and viruses (DNA viruses incl.
  NCLDV/giant viruses, and phages), plus organelle references (plastid/mito).
- Headers carry a domain/source prefix so origin is recoverable from the subject id,
  e.g. `EUK__<genome>|<locus>`, `BAC__...`, `ARC__...`, `NCLDV__...`, `PHAGE__...`,
  `VP__...` (virophage), `PLASTID__...`, `MITO__...`.
- A sibling labels file maps `genome_id` -> pipe-delimited lineage
  (`DOMAIN|phylum|class|...|species`).

Availability check (adapt to local layout):
```bash
: "${BIO_DB_ROOT:?set BIO_DB_ROOT}"
# look for a combined multi-domain proteome diamond db + labels
find "$BIO_DB_ROOT" -maxdepth 3 \( -iname '*combined*proteome*.dmnd' -o -iname '*nr*.dmnd' \) 2>/dev/null
find "$BIO_DB_ROOT" -maxdepth 3 -iname '*labels*.tsv' 2>/dev/null
# confirm domain coverage from the labels prefixes (must show EUK, BAC, ARC, and viral)
cut -f1 <labels.tsv> | sed 's/__.*//' | sort | uniq -c
```
Decision: if a single DB does not span all domains, it CANNOT polarize transfer.
Build a combined one rather than running per-domain searches that can't be compared.

Build (if absent), via `/bio-fasta-database-curator`:
```bash
# 1) collect domain proteomes (EukProt, GTDB, IMG/VR, giant-virus proteome, organelle RefSeq)
# 2) prefix headers by domain/source; concatenate
# 3) (recommended) cluster to reduce size at ~equal sensitivity (MMseqs2 linclust/cluster)
# 4) diamond makedb --in combined_proteome.faa --db combined_proteome.dmnd
# 5) write genome_id<TAB>lineage labels.tsv from each source's taxonomy
```
A clustered build (clusterednr / MMseqs2-reduced) is strongly preferred — full nr or
a 100M+ unreduced proteome makes blastx of many windows prohibitively slow.

## 2. The comparison genome/proteome collection (required)

The "other side" of the comparison (e.g. a eukaryote genome catalog when the query
is a virus). Prefer a collection with a queryable metadata table.

Check for:
- Sequences: `sequences/fna/*.fna.gz` (nucleotides) and/or `faa/*.faa.gz` (proteins).
  Note which is present — if proteins are missing for most genomes, the forward
  search MUST be blastx on the nucleotides.
- Metadata: a table (DuckDB/parquet/TSV) keyed by a stable genome id (matching the
  fasta basenames) with taxonomy, completeness, and contamination per genome. Use it
  to (a) attach lineage for the pattern analysis and (b) flag hits from
  high-contamination assemblies.

Availability check:
```bash
ls "$BIO_DB_ROOT"/*/sequences/{fna,faa} 2>/dev/null | head
# confirm fasta basenames join to the metadata key before trusting lineage joins
```

## 3. geNomad db (optional, for the context cross-check)
```bash
ls "$BIO_DB_ROOT"/genomad_db 2>/dev/null   # else: genomad download-database
```

## Record in the run log
DB names, versions, dates, paths-relative-to-`$BIO_DB_ROOT`, per-domain genome and
protein counts, and whether the arbiter was clustered. Reproducibility depends on it.
