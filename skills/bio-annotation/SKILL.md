---
name: bio-annotation
description: Annotate genes or proteins and infer taxonomy from sequence homology. Use when assigning functions, domains, or taxonomic labels to genomes, contigs, or protein sets.
---

# Bio Annotation

Functional annotation and taxonomy inference from sequence homology.

## Instructions

1. Read `docs/README.md` and the relevant tool guides before running anything.
2. Normalize tool outputs and generate the complete comparison bundle with the schema-backed driver:

   ```bash
   uv run --script skills/bio-annotation/scripts/build_annotation_artifacts.py \
     raw_annotations.tsv --genomes genomes.tsv --markers marker_catalog.tsv \
     --out results/bio-annotation
   ```

   The driver refuses a non-empty destination, enforces globally unique protein identifiers, writes normalized Parquet tables, adds explicit absent-marker rows, and computes query-specific/missing/expanded/contracted families against the reference median. The artifact contract is in `schemas/artifacts.schema.json`.
3. When a nucleotide assembly, MAG, genome, or contig FASTA is available, run `/tracking-taxonomy-updates` first for the BBTools-container QuickClade `percontig` domain screen. Use that routing table to choose the right taxonomy/QC path before interpreting protein annotations.
4. For InterProScan, read `docs/interproscan-usage.md` and validate the exact CLI with `--help` or `--version`. Current stable is v5.77-108.0; InterProScan 6 (Nextflow-based) is a forward-looking migration target.
5. Run InterProScan for domain/family annotation.
6. Run eggNOG-mapper v2.1.13+ for orthology-based annotation.
7. Run sequence-vs-database search and resolve taxonomy with TaxonKit v0.20.0+ (required for the March 2025 NCBI rank update that replaces "superkingdom" with "domain" and adds "realm" for viruses).
   Backend choice (DIAMOND, clustered nr, MMseqs2-GPU): see [docs/README.md](docs/README.md#sequence-search-backends).
8. For domain-specific taxonomy after QuickClade:
   - Bacteria/Archaea -> run GTDB-Tk when genome/MAG-level sequence is available and cross-check NCBI/DIAMOND lineage assignments.
   - Viral/phage -> route to `/bio-viromics`; use PHROG/NCVOG markers and vConTACT3 only for phage/prokaryotic-virus contexts.
   - Giant-virus/Nucleocytoviricota -> route to `/bio-viromics` with GVClass and NCLDV marker-gene phylogeny.
   - Eukaryota -> use EukCC for MAG/genome QC and lineage context; avoid CheckM/GTDB-Tk assumptions.
9. For group-appropriate marker families, run HMM searches against the relevant profile libraries (Pfam, TIGRFAM, COG/arCOG, PHROG/NCVOG for viruses, eukaryotic ribosomal/structural HMMs when applicable). Use `pyhmmer` (Python bindings around HMMER 3.4 with native SIMD and batch-friendly APIs) by default; fall back to the HMMER CLI (`hmmsearch` / `hmmscan`) when an upstream tool requires it. The choice of profile libraries is derived from the literature-derived playbook for the inferred group.
10. Build an annotation-wide feature inventory by genome/contig and by gene family/domain/pathway.
11. **Marker-gene census** — from the literature-derived playbook, list the diagnostic marker / machinery categories for the inferred group (e.g., replication, transcription, translation-related such as ribosomal proteins and translation factors, packaging, capsid/structural, chromatin/SMC/topoisomerase, host-interaction). For EACH query genome and each comparison-set genome supplied, record presence and copy number per category. Save as `marker_census.tsv` (columns: genome, category, family_id, family_name, copy_number, evidence_source, e_value, notes). Expected-but-absent markers are first-class rows, not silent omissions.
12. **Per-family copy-number matrix** — build a Pfam/InterPro/HMM-family × genome integer matrix covering queries AND the supplied relatives. Persist as `family_copy_number_matrix.parquet`. Compute per-family fold change vs the relative median; flag query-specific families, missing-expected families, expansions, and contractions in `family_expansion_candidates.tsv`.
13. For exploratory work, read the literature-derived analysis playbook for the inferred organism or virus group before deciding what to flag.
14. Mine the inventory for discovery candidates relative to that playbook: expected features, missing expected features, rare or expanded families, unusual combinations, annotation/taxonomy conflicts, and high-value unknowns.
15. For specialized inputs such as viruses, organelles, symbionts, pathogens, or poorly characterized lineages, use the feature classes and outlier dimensions reported in the relevant literature rather than a fixed global checklist.
16. Order `discovery_candidates.tsv` deterministically before reporting. Sort by `status` in the order `query_specific`, `missing_expected`, `expanded`, `contracted`; then by `fold_change` descending, with `inf` first and blank or non-numeric values last; then by `genome` and `family_id` ascending. Report the top rows in that order and keep the full table.

## Input Requirements

Prerequisites:
- Tools declared in the project's pinned Pixi environment. See `docs/README.md` for expected tools.
- Reference DB root: set `BIO_DB_ROOT` to the project or site-local database directory.
- Input FASTA and reference DBs are readable.
Inputs:
- proteins.faa (FASTA protein sequences).
- reference_db/ (eggNOG, InterPro, DIAMOND databases + taxdump).

## Output

- results/bio-annotation/annotations.parquet
- results/bio-annotation/domain_routing.tsv
- results/bio-annotation/taxonomy.parquet
- results/bio-annotation/feature_inventory.parquet
- results/bio-annotation/marker_census.tsv
- results/bio-annotation/family_copy_number_matrix.parquet
- results/bio-annotation/family_expansion_candidates.tsv
- results/bio-annotation/discovery_candidates.tsv
- results/bio-annotation/annotation_report.md
- results/bio-annotation/logs/
- stdout: the last line is one JSON envelope `{ok, skill, out, manifest, warnings}` (driver stdout contract in AGENTS.md)
- Artifact contract: [schemas/artifacts.schema.json](schemas/artifacts.schema.json)

## Quality Gates

- [ ] Annotation hit rate and taxonomy rank coverage meet project thresholds.
- [ ] On failure: retry with alternative parameters; if still failing, record in report and exit non-zero.
- [ ] Verify proteins.faa is non-empty and amino acid encoded.
- [ ] Verify proteins.faa does not contain `*` stop symbols before InterProScan, or strip them deliberately.
- [ ] QuickClade domain routing was used when nucleotide assemblies/genomes were available, or the protein-only reason for skipping it is recorded.
- [ ] Verify InterProScan output options are valid: use `-b` or `-d`, never both together.
- [ ] Verify packaged InterProScan installs have been initialized with `python3 setup.py -f interproscan.properties` when required.
- [ ] Verify required InterProScan helper binaries are resolvable, especially `ps_scan.pl`, `pfscan`, and `pfsearch`.
- [ ] Run a short debug-queue `sbatch` smoke test on 1-2 proteins before submitting a large cluster job; do not compute on the login node.
- [ ] Verify required reference DBs exist under the reference root.
- [ ] Domain-specific taxonomy tools match the route: GTDB-Tk for Bacteria/Archaea, `/bio-viromics` plus vConTACT3/GVClass as appropriate for viruses, and EukCC for Eukaryota.
- [ ] Feature inventory summarizes all annotated and unannotated proteins, not only top hits.
- [ ] The normalized bundle is produced in a fresh directory and matches `schemas/artifacts.schema.json`; protein identifiers are globally unique.
- [ ] `marker_census.tsv` covers every literature-derived marker category for the inferred group with explicit zero rows for absent markers.
- [ ] `family_copy_number_matrix.parquet` includes the query AND the supplied relatives, and `family_expansion_candidates.tsv` flags query-specific, missing-expected, expanded, and contracted families with fold-change vs the relative median.
- [ ] Discovery candidates include evidence fields: gene/protein ID, annotation source, confidence, why notable, and recommended validation.
- [ ] Discovery candidates are justified against the literature-derived playbook and comparison baseline, not only by generic keyword matches.

## Non-Goals

- No causal or phenotype claims from homology alone. An annotation transfer is a hypothesis about function, not a demonstration of it.
- No taxonomy for nucleotide assemblies, MAGs, or contigs outside the QuickClade route and its domain-specific follow-up (GTDB-Tk, EukCC, `/bio-viromics`).
- No reference database downloads or builds. The databases under `$BIO_DB_ROOT` are an input; report a missing database instead of fetching it.
- No structure-based inference. High-value unknowns go to `/bio-structure-annotation`.

## Troubleshooting

**Issue**: InterProScan fails immediately with CLI or runtime setup errors
**Solution**: Check `docs/interproscan-usage.md` for mutually exclusive output flags, `*` stripping, one-time `setup.py` initialization, and ProSite `PATH` requirements.
