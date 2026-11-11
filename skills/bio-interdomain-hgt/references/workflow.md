# Interdomain HGT workflow, Steps 1-4 and 6-8

Read this after Step 0 of `SKILL.md`. Step 0 (database gate) and Step 5 (context guard) stay in `SKILL.md` because they are the steps most often skipped. Run the steps in order and capture outputs and provenance at each one. Run every search and tree step with an explicit thread count (`diamond --threads`, `iqtree3 -T`, `mafft --thread`).

### Step 1: Frame the query and register hypotheses
- Infer the query's domain and lineage first (the domain routing table; `/bio-viromics` GVClass for giant viruses).
- Register the six standard working hypotheses, which include technical nulls (the driver needs at least five distinct IDs, one of them `technical` or `null`):
  1. genuine donor -> recipient HGT
  2. genuine recipient -> donor HGT / endogenization
  3. **assembly contamination** (a donor contig co-assembled into a recipient genome)
  4. **deep homology / convergence** (ancient shared genes, not transfer)
  5. **reference-sampling bias** (hits track database depth)
  6. **virus <-> virus transfer** (a frequent confounder of apparent host-derived viral genes)

### Step 2: Forward search (query <-> comparison collection)
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

### Step 3: Reciprocal classification against the arbiter
- `diamond blastp` the query proteins vs the comprehensive arbiter -> for each query
  protein, the best-hit DOMAIN and lineage (donor-derived vs query-core vs ORFan).
  Use a bitscore margin (e.g. best class must beat the next by >=10%) and coalesce
  empty-class scores to 0 before comparison (a `series.max()` on an empty group is
  NaN, and `NaN or 0` stays NaN; guard with `pd.notna`).
- For candidate recipient loci, reverse-search vs the arbiter -> best-hit domain.
- A reciprocal best hit = the query protein and the recipient locus are mutual best
  hits, with the arbiter confirming the partner domain.

### Step 4: Direction inference
- recipient <- donor (e.g. host -> virus): the query gene's best arbiter hit is the
  OTHER domain (e.g. eukaryote) and it nests within that clade.
- donor -> recipient (e.g. virus -> host / endogenization): a recipient-genome locus
  best-matches the query's domain across the whole arbiter AND sits in
  recipient-dominated genomic context (Step 5).
- Leave deep-homology / tied cases as `ambiguous` for the phylogeny to polarize.

### Step 5: Genomic-context contamination guard

See `SKILL.md`.

### Step 6: Deep homology vs recent transfer
- Ancient shared genes sit at LOW identity; recent HGT sits HIGH. Bound the expensive
  context + phylogeny steps to high-identity candidates (state the cutoff and log how
  many were dropped). Do not treat every conserved-core hit as HGT.

### Step 7: Per-gene phylogenetic confirmation (required for confirmed calls)
- For each top candidate, gather homologs ACROSS ALL DOMAINS from the arbiter (one
  search returning subject sequences, e.g. DIAMOND `full_sseq`), taxon-balanced and
  dereplicated; align (MAFFT) -> trim (trimAl) -> tree (IQ-TREE with ultrafast
  bootstrap, fixed seed), for example
  `iqtree3 -s aln.faa -m MFP -B 1000 --seed 1729 -keep-ident -T 4`. Pass
  `-keep-ident` so the focal tip is not collapsed; make tip names unique to avoid
  duplicate-taxon failures. Give the driver the support of the nesting node on a
  0-1 scale: convert UFBoot 0-100 to 0-1 (UFBoot 95 becomes 0.95) before the
  gate. The [phylogenomics page](../../omics-pipeline/references/phylogenomics.md)
  covers the trees.
- Confirmed when the focal sequence nests inside the EXPECTED donor/recipient clade
  with support. Including donor + other-virus + recipient homologs is exactly what
  separates genuine host <-> virus transfer from virus <-> virus transfer.

### Step 8: Integrate, contextualize, report
- Lineage x function matrix; transfer-direction tallies; **normalize per-lineage
  counts by collection sampling depth** (control for reference bias before claiming a
  lineage is enriched).
- Literature context (`/polars-dovmed`) for the inferred group.
- Produce an interesting-findings table (evidence, confidence, comparison baseline,
  follow-up test) ordered deterministically from `hgt_candidates.tsv`: `status` first
  (`confirmed`, then `candidate`, then `rejected`), then `bitscore` descending with
  blank or non-numeric values last, then `query_protein` and `recipient_locus` ascending.
