---
name: bio-annotation
description: Annotate proteins with functions, domains, and homology-based taxonomy. Use when assigning functional or taxonomic labels to proteins from genomes, contigs, or MAGs.
disable-model-invocation: true
---

# Bio Annotation

Functional annotation and taxonomy inference from sequence homology.

Shared pipeline rules: read `~/.agents/skills/omics-pipeline/SKILL.md` first (in a plugin install, `../omics-pipeline/SKILL.md` from this file).

## Instructions

1. Read [docs/README.md](docs/README.md) for the tool choice and its pitfalls before running anything.
2. Normalize tool outputs and generate the complete comparison bundle with the schema-backed driver. `RUN_DIR` is the run directory that `bioinformatics-project` defines (`results/<date>_<name>/`):

   ```bash
   uv run --script ~/.agents/skills/bio-annotation/scripts/build_annotation_artifacts.py \
     raw_annotations.tsv --genomes genomes.tsv --markers marker_catalog.tsv \
     --out "$RUN_DIR/annotation"
   ```

   `raw_annotations.tsv` is one row per protein and family hit with columns `genome, protein_id, family_id, family_name, category, e_value, annotation, taxonomy, confidence`, merged by you from the tool outputs below. `genomes.tsv` has `genome, role (query|reference), domain, route, protein_count`, where `protein_count` is the total number of proteins of the genome, with or without a hit (it sets `unannotated_count`, and the run fails when it is missing or lower than the proteins in `raw_annotations.tsv`); `marker_catalog.tsv` has `category, family_id, family_name, expected`, where `expected` is `yes` or `no`. `fixtures/` holds a runnable example. The driver refuses a non-empty destination, rejects any `role` other than `query` or `reference`, validates all inputs before it writes a file (a failed run leaves the destination empty, so you can rerun into it), enforces globally unique protein identifiers, writes normalized Parquet tables, adds explicit absent-marker rows (an absent marker with `expected` `yes` is noted in `notes`, and the final envelope lists each one in `warnings`), and computes query-specific/missing/expanded/contracted families against the reference median. The artifact contract is in `schemas/artifacts.schema.json`.
3. Take the domain route for each genome from the router's routing table before interpreting protein annotations. Domain-specific taxonomy follows the route: GTDB-Tk for Bacteria and Archaea (cross-check NCBI/DIAMOND lineages), `bio-viromics` for viruses (PHROG/NCVOG markers and vConTACT3 only for phage and prokaryotic-virus contexts; GVClass and NCLDV marker phylogeny for giant viruses), EukCC for Eukaryota without CheckM or GTDB-Tk assumptions.
4. For InterProScan, validate the exact CLI with `--help` or `--version`. InterProScan 5 and the Nextflow-based InterProScan 6 both have current releases (see [docs/README.md](docs/README.md#interproscan-domains)). Pin one release and one InterPro data release per project.
5. Run InterProScan for domain and family annotation.
6. Run eggNOG-mapper v2 for orthology-based annotation. v3.0.0 is in beta; use it only when the project pins it deliberately.
7. Run sequence-vs-database search and resolve taxonomy with TaxonKit v0.20.0+ (required for the March 2025 NCBI rank update that replaces "superkingdom" with "domain" and adds "realm" for viruses). Backend choice (DIAMOND, clustered nr, MMseqs2-GPU): see [docs/README.md](docs/README.md#sequence-search-backends).
8. For group-appropriate marker families, run HMM searches against the relevant profile libraries (Pfam, TIGRFAM, COG/arCOG, PHROG/NCVOG for viruses, eukaryotic ribosomal and structural HMMs when applicable). Use `pyhmmer` (Python bindings around HMMER 3.4 with native SIMD and batch-friendly APIs) by default; fall back to the HMMER CLI (`hmmsearch` / `hmmscan`) when an upstream tool requires it. The profile libraries come from the literature-derived playbook for the inferred group.
9. Build an annotation-wide feature inventory by genome or contig and by gene family, domain and pathway.
10. **Marker-gene census** (the driver writes it from your hits): for each diagnostic marker or machinery category of the inferred group (for example replication, transcription, translation-related, packaging, capsid/structural, chromatin/SMC/topoisomerase, host-interaction), record presence and copy number for each query genome and each comparison genome as `marker_census.tsv` with columns `genome, category, family_id, family_name, copy_number, evidence_source, e_value, notes, expected`. Expected-but-absent markers are rows, not silent omissions.
11. **Per-family copy-number matrix**: a Pfam/InterPro/HMM-family by genome integer matrix covering the query and the supplied relatives, persisted as `family_copy_number_matrix.parquet`. Compute per-family fold change against the relative median, and flag query-specific, missing-expected, expanded and contracted families in `family_expansion_candidates.tsv`.
12. Mine the inventory for discovery candidates against the literature-derived playbook: missing expected features, rare or expanded families, unusual combinations, annotation/taxonomy conflicts, high-value unknowns.
13. `query_specific` requires the family to be absent from every reference. When the reference median is 0 but at least one reference carries the family, the status is `present_in_reference_minority` with an empty `fold_change`: report it as a signal, never as a discovery.
14. Order `family_expansion_candidates.tsv` deterministically before reporting. Sort by `status` in the order `query_specific`, `missing_expected`, `expanded`, `contracted`, `present_in_reference_minority`; then by `fold_change` descending, with `inf` first and blank or non-numeric values last; then by `genome` and `family_id` ascending. Report the top rows in that order and keep the full table.

## Input Requirements

- Tools from the project's pinned pixi environment (`docs/README.md`); `BIO_DB_ROOT` set to the database directory.
- `proteins.faa` (FASTA protein sequences) and `reference_db/` (eggNOG, InterPro, DIAMOND databases and taxdump).
- For the driver: `raw_annotations.tsv`, `genomes.tsv` (at least one query and one reference), and `marker_catalog.tsv` with the columns in step 2.

## Output

The driver writes every file below except the agent-authored report and `logs/`, and also writes `run_manifest.json`. All files sit in the stage directory under the run directory that `bioinformatics-project` defines (`results/<date>_<name>/<stage>/`, stage `annotation`).

- annotations.parquet
- domain_routing.tsv (the driver's normalized copy of the genome routes, not the QuickClade table)
- taxonomy.parquet
- feature_inventory.parquet
- marker_census.tsv
- family_copy_number_matrix.parquet
- family_expansion_candidates.tsv
- annotation_report.md (agent-authored)
- logs/
- Artifact contract: [schemas/artifacts.schema.json](schemas/artifacts.schema.json)

## Quality Gates

- [ ] `proteins.faa` is non-empty, amino acid encoded, and free of `*` stop symbols before InterProScan (or they are stripped deliberately).
- [ ] InterProScan output options use `-b` or `-d`, never both. Packaged installs are initialized with `python3 setup.py -f interproscan.properties` when required, and the helper binaries `ps_scan.pl`, `pfscan` and `pfsearch` resolve.
- [ ] A short smoke test on 1-2 proteins passes before a large cluster job (`hpc-slurm` for submission).
- [ ] The reference databases exist under `BIO_DB_ROOT`.
- [ ] The normalized bundle is produced in a fresh directory, matches `schemas/artifacts.schema.json`, and has globally unique protein identifiers.
- [ ] `marker_census.tsv` covers every literature-derived marker category for the inferred group, with explicit zero rows for absent markers; each expected marker the envelope lists in `warnings` appears in the report as a result.
- [ ] `family_copy_number_matrix.parquet` includes the query and the supplied relatives, and `family_expansion_candidates.tsv` carries fold change against the relative median.
- [ ] Reported discovery candidates (step 12) carry gene or protein ID, annotation source, confidence, why notable, and recommended validation.

## Non-Goals

- No causal or phenotype claims from homology alone. An annotation transfer is a hypothesis about function, not a demonstration of it.
- No taxonomy for nucleotide assemblies, MAGs, or contigs outside the QuickClade route and its domain-specific follow-up.
- No reference database downloads or builds. The databases under `$BIO_DB_ROOT` are an input; report a missing database instead of fetching it.
- No structure-based inference. High-value unknowns go to the [structure page](../omics-pipeline/references/structure.md).
