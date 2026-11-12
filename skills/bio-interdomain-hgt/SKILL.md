---
name: bio-interdomain-hgt
description: Detect and polarize interdomain horizontal gene transfer with reciprocal hits, genomic context, and gene trees. Use for virus-host gene exchange, endogenous viral elements, or donor direction.
disable-model-invocation: true
---

# Bio Interdomain HGT

Detect, polarize, and confirm horizontal gene transfer between a query genome
(virus, MAG, isolate, or bin) and other domains of life. Built for the common
asymmetric case where the query is well annotated but the comparison set is
genome-only (proteins missing). Pairs with `/bio-annotation` (homology/taxonomy),
the [phylogenomics page](../omics-pipeline/references/phylogenomics.md)
(trees), and `/bio-viromics` (viral classification). Shared pipeline
rules: read `~/.agents/skills/omics-pipeline/SKILL.md` first (in a plugin install,
`../omics-pipeline/SKILL.md` from this file).

## Instructions

Run the steps in order; capture outputs and provenance at each step. Steps 0
(database gate) and 5 (frame-aware context guard on eukaryotic DNA) are the ones
most often skipped and most often responsible for wrong conclusions. They are
below. Steps 1-4 and 6-8 (hypotheses, forward search, reciprocal classification,
direction, deep homology, gene trees, integration) are in
[references/workflow.md](references/workflow.md); read it after Step 0.

Give every search and tree step an explicit thread count (`diamond --threads`,
`iqtree3 -T`, `mafft --thread`).

After Steps 0-7 have produced their normalized TSVs, apply the evidence gates with
the driver. `RUN_DIR` is the run directory that `bioinformatics-project` defines
(`results/<date>_<name>/`):

```bash
uv run --script ~/.agents/skills/bio-interdomain-hgt/scripts/run_hgt_evidence.py \
  forward_hits.tsv --arbiter-hits arbiter_hits.tsv --reciprocal reciprocal.tsv \
  --context context.tsv --trees trees.tsv --sampling-depth sampling_depth.tsv \
  --databases databases.json --hypotheses hypotheses.tsv --reflections reflections.tsv \
  --query-domain ncldv --out "$RUN_DIR/interdomain-hgt"
```

The driver checksum-verifies the arbiter, lineage labels, and comparison collection
listed in `databases.json`, applies the gates below, normalizes confirmed candidates
by lineage sampling depth, and writes `run_manifest.json` under
[schemas/hgt-evidence.schema.json](schemas/hgt-evidence.schema.json). Input
contracts (tab-separated, exact column order) are in `fixtures/`; the gates are:

| Gate | Pass rule in the driver |
|------|-------------------------|
| Homology | query and subject coverage >= 0.5 and e-value <= 1e-5 |
| Reciprocal best hit | `forward_rank` and `reverse_rank` both 1 |
| Direction | query's best arbiter domain equals the recipient domain: `recipient_to_query`; recipient locus best-matches `--query-domain`: `query_to_recipient`; otherwise `ambiguous`. With `--min-identity`, a forward hit whose `identity` is lower is `ambiguous` too |
| Context | `recipient_domain_fraction` >= 0.6; eukaryotic recipients also need `method` `diamond_blastx` |
| Phylogeny | `nesting_clade` equals `expected_clade` and `support` >= 0.9 on a 0-1 scale |

A row is `confirmed` only when all gates pass and the direction is not ambiguous,
`candidate` when homology passes but another gate fails, and `rejected` otherwise.
`--min-identity PERCENT` (0 to 100, default off) marks deep-homology candidates: a
forward hit with `identity` below it gets direction `ambiguous`, so it cannot be
`confirmed`. `ambiguity_reason` in `hgt_candidates.tsv` is non-empty for every `ambiguous` row and says why (arbiter domains, identity, or both). With `--min-identity`, an `identity` that is not a finite percent from 0 to 100 stops the run. The run
manifest records the value as `min_identity` (`null` when off). Domain labels use
the arbiter vocabulary `eukaryota`, `bacteria`, `archaea`, `ncldv`, `phage`,
`organelle`. `--query-domain`, `hit_domain` and `recipient_domain` must be one of them, and a
`support` outside 0-1 (for example 95 instead of 0.95) stops the run with the error envelope.
Hypotheses need five distinct
IDs with one `technical` or `null` row; reflections must cover the gates `database`,
`forward`, `reciprocal`, `context`, `phylogeny`, `final` in that order.

### Step 0: Database availability gate (DO THIS FIRST; never hardcode paths)

HGT calls are only as good as the reference. Resolve the site/project DB root from
`$BIO_DB_ROOT` (or ask); never bake absolute paths into the analysis. Verify that
BOTH of the following exist before any search; if one is missing, build it or STOP.

1. A **comprehensive multi-domain reciprocal-arbiter proteome**: a single protein
   search database (DIAMOND `.dmnd` or MMseqs2) that contains eukaryotes + bacteria
   + archaea + viruses (including NCLDV/giant viruses and phages) + organelles,
   with a parallel `genome_id -> lineage` labels table. This one database is what
   makes "best-hit taxon", and therefore transfer direction, meaningful.
   - Building blocks: EukProt, GTDB, NCBI nr/RefSeq, IMG/VR, a giant-virus proteome
     (GVDB / gvclass-style), organelle RefSeq.
   - Check: list `$BIO_DB_ROOT` for an existing combined-proteome `.dmnd` + labels.
   - If absent: build it with standard tools such as `seqkit` (prefix every header by
     domain, e.g. `EUK__`, `BAC__`, `ARC__`, `NCLDV__`, `PHAGE__`, `ORG__`; deduplicate;
     keep a mapping table; then `diamond makedb`). The six prefixes map to the driver's
     six labels ([docs/database-availability.md](docs/database-availability.md)). A
     clustered build (clusterednr / MMseqs2-reduced) is much faster at comparable
     sensitivity; prefer it.
   - A euk-only or virus-only arbiter CANNOT polarize transfer. Confirm it spans
     every candidate donor domain.
2. A **per-domain genome/proteome collection** for the comparison side (e.g. a
   eukaryote genome catalog such as EukProt/MMETSP/NCBI/Mycocosm; a viral genome
   catalog such as IMG/VR/RefSeq). Prefer one with a queryable metadata table
   (per-genome taxonomy + completeness + contamination) so hits can be quality-flagged.
   - Record whether the collection ships PROTEINS or only NUCLEOTIDES; this decides
     the forward-search tool in Step 2.

Record DB name / version / date / path-relative-to-root and per-genome counts in
the run log. If a required comprehensive DB is missing and cannot be built, say so
explicitly; do not silently substitute a non-comprehensive database.

### Step 5: Genomic-context contamination guard
- Require the recipient locus to sit on a contig dominated by the RECIPIENT domain
  (flanking genes best-match the recipient); otherwise flag as contamination or a
  free donor contig (e.g. a mis-binned NCLDV contig inside a protist MAG).
- **CRITICAL on eukaryotic genome assemblies**: do NOT call genes with a prokaryotic
  caller (Prodigal/pyrodigal): introns fragment euk genes, so the locus ORF comes
  back short and unclassifiable (in one project ~94% of loci came back blank). Instead
  use frame-aware, intron-tolerant `diamond blastx` of the locus +/- flank window vs
  the arbiter (`--range-culling --top 10 -F 15`); each HSP is a gene, classified by
  subject domain, giving both the locus origin and the flanking-gene domain mix.
  Optionally cross-check with geNomad ("is this contig viral").
- Transcriptome assemblies are ~one spliced transcript per contig, so the flanking
  context signal is weak; rely more on reciprocity + phylogeny there.

## Performance gotchas (hard-won)
- `diamond blastx --sensitive` against a 100M+ protein arbiter hit 8-hour wall-clock
  limits with empty output in practice. Use default sensitivity for domain
  classification; reserve `--sensitive` for small or divergent focal sets.
- A clustered arbiter (clusterednr / MMseqs2-reduced) runs much faster; on a CUDA
  GPU node, MMseqs2-GPU `easy-taxonomy --gpu` is an alternative.
- Batch work: load `hpc-slurm` (shared rule 6 in the `omics-pipeline` skill). Shard by
  size and recover stragglers at finer granularity, not by re-running everything.

## Input Requirements

- The two Step 0 databases under `$BIO_DB_ROOT` (recipe: [docs/database-availability.md](docs/database-availability.md)).
- Query proteins (`.faa`), query contigs (`.fna`), optional query domain annotations.
- Tools (diamond, mafft, trimal, iqtree, geNomad, taxonkit, seqkit) and versions: [docs/README.md](docs/README.md).

## Output

Driver outputs under the run directory that `bioinformatics-project` defines (`results/<date>_<name>/<stage>/`):
- `hgt_candidates.tsv`: per hit, best arbiter domains, RBH, direction, context, phylogeny, status, and the reason for an `ambiguous` direction
- `query_protein_origin.tsv`: donor-derived vs query-core per query protein
- `lineage_sampling_normalization.tsv`: confirmed candidates per 100 sampled genomes
- `phylogeny_evidence.tsv`, `hypothesis_register.tsv`, `gate_reflections.tsv`
- `run_manifest.json`, validated against [schemas/hgt-evidence.schema.json](schemas/hgt-evidence.schema.json)

Workflow outputs, written by the agent:
- (agent-authored) `forward_hits.tsv`, `lineage_function_matrix.tsv`
- (agent-authored) `phylogeny/<gene>/`: alignment, tree, and nesting call
- (agent-authored) `hgt_report.md`, `logs/`

## Quality Gates

- [ ] The arbiter spans ALL candidate donor domains; every database checksum is verified before candidate scoring.
- [ ] Each gate has a persisted reflection; candidate status comes from the gates, never from manual assignment.
- [ ] Every candidate carries id%, query and subject coverage, e-value, bitscore, and both reciprocal best hits.
- [ ] The deep-homology cutoff (`--min-identity`, or the reason there is none) is stated and the count of `ambiguous` candidates is logged.
- [ ] The virus<->virus alternative is tested in the all-domain tree, not assumed away.
- [ ] Contamination-prone hits (recipient genome with high assembly contamination, or donor-dominated contig) are flagged, not silently kept.

## Non-Goals

- No confirmed transfer direction without both a reciprocal best hit and phylogenetic nesting in the expected clade. Tied and deep-homology cases stay `ambiguous`.
- No HGT call from single-domain hits. An arbiter that does not span every candidate donor domain cannot polarize anything.
- No dating of transfer events. Identity separates recent from ancient; it does not give an age.
- No lineage-enrichment claim before per-lineage counts are normalized by collection sampling depth.
