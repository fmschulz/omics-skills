---
name: bio-viromics
description: Detect, QC, and classify viral contigs with geNomad, CheckV, vConTACT3, and GVClass. Use when finding viruses in assemblies, grading viral genomes, or assigning phage or giant-virus taxonomy.
---

# Bio Viromics

Detect, quality-check, and classify viral contigs, then compare each viral genome against a literature-derived reference set.

## Instructions

Tool guides, versions, and verified flags: [docs/README.md](docs/README.md).

Run geNomad, CheckV, GVClass, and vConTACT3 on a workstation or compute node, never on a login node. Pass an explicit thread count to each tool (`-t`). Without it, geNomad and CheckV use every CPU available to the process, and vConTACT3 uses every CPU on the host, even inside a smaller Slurm allocation. On HPC, submit through `sbatch` with CPUs matched to that thread count and follow the site's account and partition rules.

1. Start from `/tracking-taxonomy-updates` QuickClade domain routing when assemblies, MAGs, genomes, or contigs have not been screened. Viral, virus-like, mixed, or low-confidence contigs enter this skill; bacterial, archaeal, and eukaryotic rows stay on their domain routes unless later evidence contradicts the triage.
2. Detect viruses with geNomad v1.12.0 (database v1.9) as the primary virus and plasmid classifier: `genomad end-to-end -t <n> contigs.fna out/ genomad_db`. For prokaryotic-virus discovery, VirSorter2 v2.2.4 is a complementary detector; combine either detector with CheckV QC to remove false positives.
3. Run CheckV v1.1.1 with database v1.5 for completeness, contamination, and host-region trimming: `checkv end_to_end viral.fna out/ -d checkv-db-v1.5 -t <n>`.
4. Infer the likely viral group from QuickClade, geNomad taxonomy, genome statistics, and marker or similarity evidence.
5. Search the literature for that group (`/polars-dovmed`) and write `analysis_playbook.md`: typical reference sets, markers, comparative analyses, genome features, plots, and outlier signals used by people who study the group.
6. Choose taxonomy, clustering, phylogenetic, and comparative methods from the playbook:
   - Bacteriophages and other prokaryotic viruses: vConTACT3 gene-sharing networks for genus-to-order assignment. vConTACT3 replaces vConTACT2. The upstream source tag is 3.2.4; bioconda ships 3.1.6. Record the version you ran.
   - Nucleocytoviricota, Mirusviricota, and Preplasmiviricota: GVClass v2.0.3 with resource bundle v2.0.0, plus marker-gene phylogenies of core genes through `/bio-phylogenomics`.
   - RNA viruses, ssDNA viruses, and other groups that vConTACT3 does not cover well: group-specific markers, phylogenomics, and protein-family methods from the playbook. Do not force a phage-oriented workflow on them.
7. For each viral genome or high-quality viral contig, call genes and annotate proteins when needed (`/bio-gene-calling`, `/bio-annotation`), then inspect the annotation set according to the playbook rather than a fixed feature list.
8. Compare each query to the literature-supported reference set on the comparative axes in the repository AGENTS.md: marker census, per-family copy number, conserved neighborhoods, and ncRNA census. Write `marker_census.tsv`, `family_copy_number_comparison.tsv`, `conserved_neighborhoods.tsv`, and `ncRNA_census.tsv` to one comparison directory. Report what matches expectations, what is missing, expanded, or query-specific, and which patterns are likely artifacts.
9. Genome-size frontier: place each query's genome size and gene count in the distribution of close relatives and the literature-reported extremes for the group. State the percentile, the distance from the group median, and whether the query exceeds the known record size, and cite the paper that defines the record. A mid-distribution placement is still a result.
10. Assemble the evidence bundle. The driver checksum-verifies the geNomad, CheckV, GVClass, and vConTACT3 database resources, checks the hypothesis register and reflections, copies the four comparative tables, and computes `genome_size_frontier.tsv`:

    ```bash
    uv run --script skills/bio-viromics/scripts/build_viromics_evidence.py \
      viral_metrics.tsv --resources resources.json --hypotheses hypotheses.tsv \
      --reflections reflections.tsv --comparative-dir comparison/ \
      --out results/bio-viromics/evidence
    ```

    Input contracts (tab-separated, exact column order; fixtures under `fixtures/`):
    - `viral_metrics.tsv`: `genome role group genome_size gene_count literature_min literature_max literature_doi`; `role` is `query` or `reference`, and each query needs at least two references of the same `group`.
    - `hypotheses.tsv`: `hypothesis_id hypothesis type status evidence revision_stage`; at least five distinct IDs and at least one row of `type` `technical` or `null`.
    - `reflections.tsv`: `stage observed qc_status hypotheses_gained hypotheses_lost alternatives next_check literature_id`; the first stage is `initial`, a `final` stage is present, at least four stages in total, and `qc_status` is `passed`, `failed`, or `conditional`.
    - `resources.json`: schema `1.0` with exactly `genomad`, `checkv`, `gvclass`, `vcontact3` and their `_db` entries, each with `version` and `sha256`. Database entries also carry `path` and `kind` (`file`, or `directory` with the deterministic tree SHA-256 the driver computes).

    The driver computes the frontier from genome size only and sets `record_class` to `above_literature_max` or `within_known_range`. Add gene-count placement in the report.
11. Write the interesting-findings table ordered from `genome_size_frontier.tsv`: `record_class` in the order `above_literature_max`, `within_known_range`; then `distance_from_median` descending, with blank or non-numeric values last; then `genome` ascending. If no strong discovery candidate is found, state that and list the literature-derived checks performed.

## Input Requirements

Prerequisites:
- Tools pinned in the project's Pixi environment; see [docs/README.md](docs/README.md).
- `BIO_DB_ROOT` set to the project or site database directory that holds the geNomad, CheckV, GVClass, and vConTACT3 databases.

Inputs:
- `contigs.fasta` (non-empty)
- `results/taxonomy/domain_routing.tsv` when available

## Output

Driver outputs under `results/bio-viromics/evidence/`:
- `marker_census.tsv`, `family_copy_number_comparison.tsv`, `conserved_neighborhoods.tsv`, `ncRNA_census.tsv`
- `hypothesis_register.tsv`, `intermediate_reflections.tsv`
- `genome_size_frontier.tsv`
- `run_manifest.json`, validated against [schemas/evidence-bundle.schema.json](schemas/evidence-bundle.schema.json)
- stdout: the last line is one JSON envelope `{ok, skill, out, manifest, warnings}` (driver stdout contract in AGENTS.md)

Workflow outputs under `results/bio-viromics/`, written by the agent:
- (agent-authored) `viral_contigs.fasta`, `checkv_results/`, `viral_taxonomy.tsv`
- (agent-authored) `domain_routing_review.tsv`, `analysis_playbook.md`
- (agent-authored) `comparison_baseline.tsv`, `closest_relatives.tsv`, `group_comparison_results/`
- (agent-authored) `viral_feature_inventory.tsv`, `viral_discovery_candidates.tsv`
- (agent-authored) `viromics_report.md`, `logs/`

## Quality Gates

- [ ] `contigs.fasta` is non-empty and the viral databases exist under `BIO_DB_ROOT`.
- [ ] QuickClade domain routing was reviewed for assembly, MAG, or genome inputs, or the missing screen was run before final classification.
- [ ] Resource versions and database checksums are recorded and verified before classification.
- [ ] CheckV quality tiers and contamination meet the project thresholds; unmet thresholds are reported as results.
- [ ] The playbook names the inferred viral group, cited sources, standard analyses, and chosen and skipped methods.
- [ ] The comparison method fits the inferred group; phage-oriented tools are not used for other groups without literature support.
- [ ] Marker, family-copy, neighborhood, and ncRNA tables use the same query and reference set and are linked to hypothesis revisions.
- [ ] Every high-quality viral genome with available references has closest-relative or reference-set context.
- [ ] `genome_size_frontier.tsv` places each query against close relatives and cited literature extremes.
- [ ] The report lists candidate discoveries with evidence, confidence, comparison baseline, and follow-up checks, or a credible negative finding.
- [ ] On execution failure, logs are kept and the failed command is reported; a retry follows a diagnosis and records the changed parameters. Parameters are never tuned only to pass a gate.

## Non-Goals

- No host assignment beyond the evidence the run produced. Without host-linked signal from the chosen tools, the host stays unassigned.
- No completeness or contamination claims without CheckV (or GVClass for giant viruses); detector output alone does not grade a viral genome.
- No lifecycle calls (lytic, lysogenic, chronic) from sequence alone.
- No phage-oriented taxonomy for groups the playbook does not support, and no classification while database checksums are unverified.
