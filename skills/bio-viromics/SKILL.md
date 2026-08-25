---
name: bio-viromics
description: Detect, quality-control, and classify viral contigs. Use when identifying viruses in assemblies, checking viral completeness and contamination, or assigning viral taxonomy.
---

# Bio Viromics

Detect, classify, and QC viral contigs.

## Instructions

Tool guides and versions: [docs/README.md](docs/README.md).

1. Validate the pinned resource manifest and assemble the complete comparative evidence and reasoning bundle:

   ```bash
   uv run --script skills/bio-viromics/scripts/build_viromics_evidence.py \
     viral_metrics.tsv --resources resources.json --hypotheses hypotheses.tsv \
     --reflections reflections.tsv --comparative-dir comparison/ \
     --out results/bio-viromics
   ```

   The driver checksum-verifies geNomad, CheckV, GVClass, and vConTACT3 database resources; requires at least five hypotheses including a technical/null explanation; requires initial, intermediate, and final reflections; and persists marker, family-copy, synteny, ncRNA, and genome-frontier evidence under `schemas/evidence-bundle.schema.json`. Database resources may be files or directories. Set `kind` to `directory` and record the deterministic tree SHA-256 for installed database directories.
2. Start from `/tracking-taxonomy-updates` QuickClade domain routing when assemblies, MAGs, genomes, or contigs have not already been screened. Viral, virus-like, mixed, or low-confidence contigs enter this skill; bacterial/archaeal and eukaryotic rows stay on their domain-specific routes unless later evidence contradicts the triage.
3. Run virus detection with geNomad v1.8+ (use as primary plasmid-and-virus classifier).
4. Run CheckV v1.0.1 for completeness, contamination, and host-removal QC.
5. Infer the likely viral group from QuickClade, detection output, taxonomy hints, genome statistics, and marker/similarity evidence.
6. Search the literature for that viral group and write a short analysis playbook: typical reference sets, markers, comparative analyses, genome features, plots, and outlier signals used by scientists studying that group.
7. Choose taxonomy, clustering, phylogenetic, and comparative methods from the playbook:
   - For bacteriophage and prokaryotic-virus gene-sharing taxonomy: vConTACT3 v3.0 (hierarchical genus-to-order assignment, >95% ICTV agreement; supersedes vConTACT2).
   - For Nucleocytoviricota / giant viruses: gvclass v1.0 for genus-level classification combined with marker-gene phylogenies of NCLDV core genes.
   - For RNA viruses, ssDNA viruses, or other groups not well-served by vConTACT3: use group-specific markers, phylogenomics, and protein-family approaches from the literature playbook rather than forcing a phage-oriented workflow.
8. For prokaryotic-virus discovery, VirSorter2 v2.2.4 is a complementary detector to geNomad; combine with CheckV QC to remove false positives.
9. For each viral genome or high-quality viral contig, call genes and annotate proteins when needed, then inspect the annotation set according to the playbook rather than a fixed global feature list.
10. Compare each query viral genome to the literature-supported reference set. Report what matches expectations, what is missing, what is expanded, what is query-specific, and which patterns are likely artifacts.
11. **Genome-size frontier** — for each query, compute where the genome size and gene count sit within the distribution of close relatives AND the literature-reported extremes for the inferred viral group. State percentile, distance from the group median, and whether the query approaches or exceeds known record-class sizes (cite the paper that defines that record). This applies even when the query is mid-distribution — the placement itself is the finding.
12. Produce an interesting-findings table and order it deterministically from `genome_size_frontier.tsv`. Sort by `record_class` in the order `above_literature_max`, `within_known_range`; then by `distance_from_median` descending, with blank or non-numeric values last; then by `genome` ascending. If no strong discovery candidates are found, state that explicitly and list the literature-derived checks performed.

## Input Requirements

Prerequisites:
- Tools declared in the project's pinned Pixi environment. See `docs/README.md` for expected tools.
- Reference DB root: set `BIO_DB_ROOT` to the project or site-local database directory.
- Input contigs are available.
Inputs:
- contigs.fasta
- results/taxonomy/domain_routing.tsv when available

## Output

- results/bio-viromics/viral_contigs.fasta
- results/bio-viromics/domain_routing_review.tsv
- results/bio-viromics/checkv_results/
- results/bio-viromics/group_comparison_results/
- results/bio-viromics/analysis_playbook.md
- results/bio-viromics/viral_taxonomy.tsv
- results/bio-viromics/comparison_baseline.tsv
- results/bio-viromics/closest_relatives.tsv
- results/bio-viromics/viral_discovery_candidates.tsv
- results/bio-viromics/viral_feature_inventory.tsv
- results/bio-viromics/genome_size_frontier.tsv
- results/bio-viromics/viromics_report.md
- results/bio-viromics/logs/
- stdout: the last line is one JSON envelope `{ok, skill, out, manifest, warnings}` (driver stdout contract in AGENTS.md)
- Artifact contract: [schemas/evidence-bundle.schema.json](schemas/evidence-bundle.schema.json)

## Quality Gates

- [ ] CheckV quality thresholds meet project standards.
- [ ] Resource versions and database checksums are recorded and verified before classification.
- [ ] Marker, family-copy, synteny, and ncRNA artifacts refer to the same query/reference set and are linked to explicit hypothesis revisions.
- [ ] Contamination flags are below thresholds.
- [ ] On failure: retry with alternative parameters; if still failing, record in report and exit non-zero.
- [ ] Verify contigs.fasta is non-empty.
- [ ] QuickClade domain-routing evidence was reviewed for assembly/MAG/genome inputs, or the absence of a prior screen is corrected before final classification.
- [ ] Verify viral reference DBs exist under the reference root.
- [ ] Literature-derived analysis playbook names the inferred viral group, cited sources, standard analyses, and chosen/skipped methods.
- [ ] Chosen comparison method is appropriate for the inferred viral group; phage-oriented tools are not used for non-phage groups without literature support.
- [ ] Discovery scan covers the feature classes and outlier dimensions identified in the playbook.
- [ ] Closest-relative or reference-set context is reported for every high-quality viral genome where references are available.
- [ ] `genome_size_frontier.tsv` places each query in the size/gene-count distribution of close relatives and the literature-defined group extremes, with cited references.
- [ ] Report includes candidate discoveries with evidence, confidence, relative comparison, and follow-up checks, or a credible negative finding.

## Non-Goals

- No host assignment beyond the evidence the run produced. Without host-linked signal from the chosen tools, the host stays unassigned.
- No completeness or contamination claims without CheckV; detector output alone does not grade a viral genome.
- No lifecycle calls (lytic, lysogenic, chronic) from sequence alone.
- No phage-oriented taxonomy for groups the literature playbook does not support, and no classification while database checksums are unverified.
