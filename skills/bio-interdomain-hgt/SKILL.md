---
name: bio-interdomain-hgt
description: Detect and polarize interdomain horizontal gene transfer (virus <-> eukaryote/bacteria/archaea, and cross-cellular HGT) using reciprocal best hits, transfer-direction inference, a genomic-context contamination guard, and per-gene phylogenetic confirmation. Use when asked about HGT, lateral gene transfer, gene flow between domains, virus-host gene exchange, endogenous viral elements, or host-derived / host-acquired genes.
---

# Bio Interdomain HGT

Detect, polarize, and confirm horizontal gene transfer between a query genome
(virus, MAG, isolate, or bin) and other domains of life. Built for the common
asymmetric case where the query is well annotated but the comparison set is
genome-only (proteins missing). Pairs with `/bio-annotation` (homology/taxonomy),
`/bio-phylogenomics` (trees), `/bio-viromics` (viral classification), and
`/bio-fasta-database-curator` (building the arbiter database).

## Instructions

Run the steps in order; capture outputs and provenance at each step. Steps 0
(database gate) and 5 (frame-aware context guard on eukaryotic DNA) are the ones
most often skipped and most often responsible for wrong conclusions.

### Step 0 — Database availability gate (DO THIS FIRST; never hardcode paths)

HGT calls are only as good as the reference. Resolve the site/project DB root from
`$BIO_DB_ROOT` (or ask) — never bake absolute paths into the analysis. Verify that
BOTH of the following exist before any search; if one is missing, build it or STOP.

1. A **comprehensive multi-domain reciprocal-arbiter proteome**: a single protein
   search database (DIAMOND `.dmnd` or MMseqs2) that contains eukaryotes + bacteria
   + archaea + viruses (including NCLDV/giant viruses and phages) + organelles,
   with a parallel `genome_id -> lineage` labels table. This one database is what
   makes "best-hit taxon" — and therefore transfer direction — meaningful.
   - Building blocks: EukProt, GTDB, NCBI nr/RefSeq, IMG/VR, a giant-virus proteome
     (GVDB / gvclass-style), organelle RefSeq.
   - Check: list `$BIO_DB_ROOT` for an existing combined-proteome `.dmnd` + labels.
   - If absent: build it with `/bio-fasta-database-curator` (prefix every header by
     domain, e.g. `EUK__`, `BAC__`, `ARC__`, `NCLDV__`, `PHAGE__`, then
     `diamond makedb`). A clustered build (clusterednr / MMseqs2-reduced) is much
     faster at comparable sensitivity — prefer it.
   - A euk-only or virus-only arbiter CANNOT polarize transfer. Confirm it spans
     every candidate donor domain.
2. A **per-domain genome/proteome collection** for the comparison side (e.g. a
   eukaryote genome catalog such as EukProt/MMETSP/NCBI/Mycocosm; a viral genome
   catalog such as IMG/VR/RefSeq). Prefer one with a queryable metadata table
   (per-genome taxonomy + completeness + contamination) so hits can be quality-flagged.
   - Record whether the collection ships PROTEINS or only NUCLEOTIDES — this decides
     the forward-search tool in Step 2.

Record DB name / version / date / path-relative-to-root and per-genome counts in
the run log. If a required comprehensive DB is missing and cannot be built, say so
explicitly — do not silently substitute a non-comprehensive database.

### Step 1 — Frame the query and register hypotheses
- Infer the query's domain/lineage first (`/tracking-taxonomy-updates` QuickClade
  `percontig`; `/bio-viromics` GVClass for giant viruses).
- Register >=5 working hypotheses, including technical nulls:
  1. genuine donor -> recipient HGT; 2. genuine recipient -> donor HGT /
  endogenization; 3. **assembly contamination** (a donor contig co-assembled into a
  recipient genome); 4. **deep homology / convergence** (ancient shared genes, not
  transfer); 5. **reference-sampling bias** (hits track database depth); 6.
  **virus <-> virus transfer** (a frequent confounder of apparent host-derived
  viral genes).

### Step 2 — Forward search (query <-> comparison collection)
- If the comparison collection has PROTEINS: `diamond blastp` (query proteins as the
  small db, or vice versa).
- If proteins are MISSING for most of the collection: `diamond blastx` of the
  comparison NUCLEOTIDE genomes (6-frame) vs the query proteins (tiny db). For
  genome-length queries use `-F 15 --range-culling --top 10` so multiple genes per
  contig are reported.
- Scale: shard the collection across a SLURM array, bin-packed by cumulative size so
  no shard is dominated by one giant genome; set `--time` to cover the largest single
  genome; write a resume-safe per-shard `.done` sentinel.
- Thresholds: e-value <=1e-5, subject coverage >=0.5, plus identity/bitscore floors.
  Record id%, query AND subject coverage, e-value, bitscore for every hit.

### Step 3 — Reciprocal classification against the arbiter
- `diamond blastp` the query proteins vs the comprehensive arbiter -> for each query
  protein, the best-hit DOMAIN and lineage (donor-derived vs query-core vs ORFan).
  Use a bitscore margin (e.g. best class must beat the next by >=10%) and coalesce
  empty-class scores to 0 before comparison (a `series.max()` on an empty group is
  NaN, and `NaN or 0` stays NaN — guard with `pd.notna`).
- For candidate recipient loci, reverse-search vs the arbiter -> best-hit domain.
- A reciprocal best hit = the query protein and the recipient locus are mutual best
  hits, with the arbiter confirming the partner domain.

### Step 4 — Direction inference
- recipient <- donor (e.g. host -> virus): the query gene's best arbiter hit is the
  OTHER domain (e.g. eukaryote) and it nests within that clade.
- donor -> recipient (e.g. virus -> host / endogenization): a recipient-genome locus
  best-matches the query's domain across the whole arbiter AND sits in
  recipient-dominated genomic context (Step 5).
- Leave deep-homology / tied cases as `ambiguous` for the phylogeny to polarize.

### Step 5 — Genomic-context contamination guard
- Require the recipient locus to sit on a contig dominated by the RECIPIENT domain
  (flanking genes best-match the recipient); otherwise flag as contamination or a
  free donor contig (e.g. a mis-binned NCLDV contig inside a protist MAG).
- **CRITICAL on eukaryotic genome assemblies**: do NOT call genes with a prokaryotic
  caller (Prodigal/pyrodigal) — introns fragment euk genes, so the locus ORF comes
  back short and unclassifiable (validated: ~94% blank with gene-calling). Instead
  use frame-aware, intron-tolerant `diamond blastx` of the locus +/- flank window vs
  the arbiter (`--range-culling --top 10 -F 15`); each HSP is a gene, classified by
  subject domain, giving both the locus origin and the flanking-gene domain mix.
  Optionally cross-check with geNomad ("is this contig viral").
- Transcriptome assemblies are ~one spliced transcript per contig, so the flanking
  context signal is weak — rely more on reciprocity + phylogeny there.

### Step 6 — Deep homology vs recent transfer
- Ancient shared genes sit at LOW identity; recent HGT sits HIGH. Bound the expensive
  context + phylogeny steps to high-identity candidates (state the cutoff and log how
  many were dropped). Do not treat every conserved-core hit as HGT.

### Step 7 — Per-gene phylogenetic confirmation (gold standard)
- For each top candidate, gather homologs ACROSS ALL DOMAINS from the arbiter (one
  search returning subject sequences, e.g. DIAMOND `full_sseq`), taxon-balanced and
  dereplicated; align (MAFFT) -> trim (trimAl) -> tree (IQ-TREE with ultrafast
  bootstrap, fixed seed). Pass `-keep-ident` so the focal tip is not collapsed; make
  tip names unique to avoid duplicate-taxon failures.
- Confirmed when the focal sequence nests inside the EXPECTED donor/recipient clade
  with support. Including donor + other-virus + recipient homologs is exactly what
  separates genuine host <-> virus transfer from virus <-> virus transfer.

### Step 8 — Integrate, contextualize, report
- Lineage x function matrix; transfer-direction tallies; **normalize per-lineage
  counts by collection sampling depth** (control for reference bias before claiming a
  lineage is enriched).
- Literature context (`/polars-dovmed`, `/biorxiv-search`) for the inferred group;
  see `summaries/` for entry-point references.
- Produce an interesting-findings table: evidence, confidence, comparison baseline,
  follow-up test.

## Quick Reference

| Task | Action |
|------|--------|
| Check DBs | Confirm a comprehensive multi-domain arbiter + per-domain collection under `$BIO_DB_ROOT` (Step 0). |
| Forward search | blastp if comparison has proteins; blastx (6-frame) if genome-only. |
| Polarize | Reciprocal best hit + arbiter best-hit domain -> direction. |
| Guard | Frame-aware blastx context on euk DNA; geNomad cross-check. |
| Confirm | All-domain homolog tree; focal must nest in expected clade. |
| Tool docs | `docs/README.md`; DB recipe in `docs/database-availability.md`. |

## Input Requirements
- `$BIO_DB_ROOT` set; comprehensive multi-domain arbiter `.dmnd` + labels; a
  per-domain comparison collection (proteins or nucleotides) with metadata.
- Query proteins (`.faa`); query contigs (`.fna`); optional query domain annotations.
- Tools: diamond, mafft, trimal, iqtree, geNomad, taxonkit, seqkit (see `docs/README.md`).

## Output
- results/bio-interdomain-hgt/forward_hits.tsv
- results/bio-interdomain-hgt/query_protein_origin.tsv  (donor-derived vs query-core)
- results/bio-interdomain-hgt/hgt_candidates.tsv         (per locus: RBH, direction, context, confidence)
- results/bio-interdomain-hgt/lineage_function_matrix.tsv
- results/bio-interdomain-hgt/phylogeny/<gene>/          (alignment, tree, nesting call)
- results/bio-interdomain-hgt/hgt_report.md + logs/

## Examples

### Example 1: Giant virus (NCLDV) query vs a eukaryote genome collection (proteins missing)
```text
Goal: HGT between an NCLDV MAG (524 proteins) and ~5,000 protist genomes.
Step 0: confirm a combined euk+bac+arc+viral+organelle arbiter .dmnd + labels under $BIO_DB_ROOT.
        protist collection ships NUCLEOTIDES only -> forward search = blastx.
Step 2: diamond blastx protist genomes (6-frame) vs the 524 viral proteins, sharded on SLURM.
Step 3: diamond blastp the 524 viral proteins vs the arbiter -> host-derived (best hit EUK) vs viral-core (best hit NCLDV).
Step 5: for high-id (>=70%) recipient loci, diamond blastx the +/-5kb window vs the arbiter (NOT pyrodigal) -> euk-dominated context?
Step 7: per-gene tree with EUK + NCLDV + other-virus homologs -> viral gene nests in a green-algal clade => host->virus HGT confirmed.
Outcome: a lineage x function HGT matrix + phylogeny-confirmed transfers, with virus<->virus alternatives ruled out.
```

### Example 2: Bacterium query vs archaeal + eukaryotic collections
```text
Same workflow; the arbiter must still contain ALL domains so a bacterial gene that
best-matches archaea (donor) can be polarized against eukaryotic and viral alternatives.
```

## Quality Gates
- [ ] Comprehensive multi-domain arbiter confirmed present (or built) and spans ALL candidate donor domains.
- [ ] Forward search direction chosen by protein availability (blastp vs blastx); coverage computed against the protein length.
- [ ] Every candidate carries id%, query+subject coverage, e-value, bitscore, and both reciprocal best hits.
- [ ] Recipient context guard used a frame-aware method on eukaryotic DNA (NOT prokaryotic gene-calling).
- [ ] Deep-homology vs recent-transfer cutoff stated; dropped count logged.
- [ ] Phylogeny includes all-domain homologs; the virus<->virus alternative is explicitly tested, not assumed away.
- [ ] Per-lineage counts normalized for reference sampling depth before enrichment claims.
- [ ] Contamination-prone hits (recipient genome with high assembly contamination, or donor-dominated contig) flagged, not silently kept.

## Performance gotchas (hard-won)
- `diamond blastx --sensitive` vs a 100M+ protein arbiter is far too slow at scale
  (multi-hour 8h timeouts, empty output). Use DEFAULT sensitivity for domain
  classification; reserve `--sensitive` for small or divergent focal sets only.
- A clustered arbiter (clusterednr / MMseqs2-reduced) is dramatically faster; on a
  CUDA GPU node, MMseqs2-GPU `easy-taxonomy --gpu` is an alternative.
- SLURM: bin-pack by size; resume-safe `.done` sentinels; raise array throttle only
  into idle capacity; a watcher's "queue is empty" check must tolerate transient
  empty `squeue` (controller socket timeouts) — require two consecutive empty reads
  before resubmitting, or you will fire duplicate arrays. Recover stragglers at finer
  granularity + longer `--time`, not by re-running everything.

## Troubleshooting
**Issue**: host_origin / recipient-locus class is blank for most loci on genome assemblies.
**Solution**: you are gene-calling eukaryotic DNA with a prokaryotic caller; switch to frame-aware `diamond blastx` of the locus window (Step 5).

**Issue**: context-guard / reverse search times out at the wall clock with little output.
**Solution**: drop `--sensitive` to default, shrink the flank window, and re-shard finely; the 121M-protein arbiter is the cost driver.

**Issue**: apparent host-derived viral genes that may actually be virus-to-virus transfers.
**Solution**: include NCLDV + other-virus + cellular homologs in the per-gene tree and require nesting in the expected clade (Step 7).
