---
name: bio-protein-clustering-pangenome
description: Cluster proteins into orthogroups and build pangenome matrices. Use when comparing gene-family presence, absence, expansion, contraction, or core and accessory content across genomes.
---

# Bio Protein Clustering Pangenome

Cluster proteins into orthogroups and derive pangenome matrices.

## Instructions

Tool guides and versions: [docs/README.md](docs/README.md).

1. After clustering, build and validate the complete small-to-large comparison bundle with:

   ```bash
   uv run --script skills/bio-protein-clustering-pangenome/scripts/build_pangenome_artifacts.py \
     orthogroups.tsv --genomes genomes.tsv --marker-catalog marker_catalog.tsv \
     --marker-hits marker_hits.tsv --ncrna ncRNA_census.tsv \
     --out results/bio-protein-clustering-pangenome
   ```

   The driver requires globally unique protein IDs, at least two reference genomes for a defensible median, and a fresh output directory. It persists marker and ncRNA censuses alongside copy-number, presence/absence, family-comparison, genome-frontier, and conserved-neighborhood artifacts. `fixtures/` is a runnable three-genome contract test.
2. Cluster proteins. Choose the tool by dataset size and goal:
   - Default for orthology inference up to a few hundred genomes: **OrthoFinder v3.1.5** (supports MSA-based gene trees; supersedes OrthoFinder v2 and OrthoMCL workflows).
   - Very large pangenomes where OrthoFinder is too RAM-heavy: **ProteinOrtho v6.3.6**.
   - Sequence clustering (not strict orthology) and similarity-search backbones: **MMseqs2 v18-8cc5c**. GPU search requires MMseqs2 v16 or newer plus a GPU-enabled build on CUDA Turing-or-newer hardware; full-speed kernels require Ampere or newer. Enable `--gpu` only for commands that expose it and record the CPU/GPU build used.
3. Build presence/absence matrix AND an integer copy-number matrix (orthogroup × genome) covering the query AND the close relatives produced by `/bio-phylogenomics`.
4. Compute core/accessory/cloud/singleton partitions.
5. Identify single-copy orthologs for phylogenetic analysis.
6. Discriminate paralogs from orthologs in multi-copy gene families.
7. Calculate pangenome statistics (completeness, orthogroup occupancy).
8. When a query genome or genome set is under study, use the literature-derived analysis playbook to choose an appropriate comparison baseline: closest relatives, a broader clade, environmental references, or a negative/control set.
9. **Genome-property frontier table** — produce `relative_genome_metrics.tsv` with one row per (query + relative) and columns for genome size, contig count, N50, gene count, coding density, GC, tRNA count, rRNA count, and any group-relevant property. Add a column that places the query in the relative distribution (percentile, min/median/max, "record-class" tag) and a column citing the literature reference defining the group's known range.
10. **Synteny / conserved neighborhoods** — for each pair (query, relative) compute conserved gene neighborhoods (e.g., ≥2 collinear orthologs). Tool selection:
   - Pairwise / classical: MCScanX (*Nature Protocols* 2024 updated protocol).
   - Multi-genome at scale (>2 assemblies, up to >3 Gbp, >15% divergence): **ntSynt** (*BMC Biology* 2025, DOI: 10.1186/s12915-025-02455-w) — alignment-free minimizer-graph approach; does not detect duplications.
   - Strain-level work where duplication detection matters: SibeliaZ.
   Save results as `conserved_neighborhoods.tsv` with columns: query_block_id, relative, relative_block_id, members (ortholog IDs), intergenic_spacing_query, intergenic_spacing_relative, spacing_ratio, notes. Flag conserved gene pairs and unusual spacing/expansions.
11. Identify discovery-relevant differences defined by the playbook, including query-specific families, missing expected families, expansions/contractions, unusual sharing patterns, and high-value unknowns. Persist as `family_copy_number_comparison.tsv` (query vs relative-median fold change per family) — coordinated with `bio-annotation`'s family matrix.
12. Annotate candidate orthogroups with `/bio-annotation`; for high-value unknowns, route representatives to `/bio-structure-annotation` when structure-based inference is appropriate.
13. Produce a comparison summary that separates conserved lineage features from unusual or query-specific features and states the baseline used. The summary must report ALL of: genome-property frontier, marker-category presence/copy, family expansions/contractions, synteny conservation/breakage, and ncRNA counts side-by-side with relatives.

## Quick Reference

| Task | Action |
|------|--------|
| References | See `references.md`. |

## Input Requirements

Prerequisites:
- Tools are installed in the project's pinned Pixi environment. Commit `pixi.toml` and `pixi.lock`, and run tools through `pixi run` so the lockfile records exact builds. See `docs/README.md` for expected tools.
- Protein FASTA inputs are available as one non-empty file per genome or species. OrthoFinder uses each filename as a taxon identifier, so filenames must be unique and stable.
Inputs:
- `protein_fastas/` with one amino-acid FASTA per genome, for example `protein_fastas/genome_A.faa` and `protein_fastas/genome_B.faa`
- `genomes.tsv` mapping each stable genome identifier to its FASTA path and query/reference role
- For MMseqs2 clustering of a concatenated FASTA, `protein_to_genome.tsv` mapping every unique protein ID back to exactly one genome; a merged `proteins.faa` without this mapping cannot produce a valid genome-by-family matrix

## Output

- results/bio-protein-clustering-pangenome/orthogroups.tsv
- results/bio-protein-clustering-pangenome/presence_absence.parquet
- results/bio-protein-clustering-pangenome/copy_number_matrix.parquet
- results/bio-protein-clustering-pangenome/relative_genome_metrics.tsv
- results/bio-protein-clustering-pangenome/family_copy_number_comparison.tsv
- results/bio-protein-clustering-pangenome/conserved_neighborhoods.tsv
- results/bio-protein-clustering-pangenome/closest_relative_comparison.tsv
- results/bio-protein-clustering-pangenome/query_specific_candidates.tsv
- results/bio-protein-clustering-pangenome/pangenome_report.md
- results/bio-protein-clustering-pangenome/logs/
- stdout: the last line is one JSON envelope `{ok, skill, out, warnings}` (driver stdout contract in AGENTS.md)

## Quality Gates

- [ ] Cluster size distributions meet project thresholds.
- [ ] Matrix completeness meets project thresholds.
- [ ] The tested artifact bundle contains marker-gene and ncRNA censuses alongside copy-number and synteny matrices for the same genome set.
- [ ] On failure: retry with alternative parameters; if still failing, record in report and exit non-zero.
- [ ] Verify every per-genome FASTA is non-empty, amino-acid encoded, and has protein IDs unique across the full dataset.
- [ ] Verify the genome manifest covers every FASTA exactly once; if proteins were concatenated for MMseqs2, verify every clustered protein maps to exactly one genome.
- [ ] Comparison baseline is justified from literature, phylogeny, taxonomy, or data availability.
- [ ] Query-specific, missing, expanded, and conserved orthogroups are reported separately.
- [ ] Candidate discovery orthogroups have annotation evidence or a recommended follow-up analysis.
- [ ] `relative_genome_metrics.tsv` places each query in the distribution of relatives and notes the literature-defined extreme of the inferred group.
- [ ] `family_copy_number_comparison.tsv` reports per-family fold change vs the relative median for the full annotated family set, not only top candidates.
- [ ] `conserved_neighborhoods.tsv` is produced and includes intergenic spacing for both query and relative sides; broken synteny, unusual spacing, and expansions are flagged.
