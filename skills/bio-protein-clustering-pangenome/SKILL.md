---
name: bio-protein-clustering-pangenome
description: Cluster proteins into orthogroups and build pangenome matrices. Use when comparing gene-family presence, copy number, or core and accessory content across genomes.
disable-model-invocation: true
---

# Bio Protein Clustering Pangenome

Cluster proteins into orthogroups and derive pangenome matrices. Shared pipeline rules: read `~/.agents/skills/omics-pipeline/SKILL.md` first (in a plugin install, `../omics-pipeline/SKILL.md` from this file).

## Instructions

Tool guides and versions: [docs/README.md](docs/README.md). Literature starting points: [references.md](references.md).

1. Cluster proteins. Choose the tool by dataset size and goal:
   - Default for orthology inference up to a few hundred genomes: **OrthoFinder** (supports MSA-based gene trees; supersedes OrthoFinder v2 and OrthoMCL workflows).
   - Very large pangenomes where OrthoFinder is too RAM-heavy: **ProteinOrtho**.
   - Sequence clustering (not strict orthology) and similarity-search backbones: **MMseqs2**. GPU search requires MMseqs2 v16 or newer plus a GPU-enabled build on CUDA Turing-or-newer hardware; full-speed kernels require Ampere or newer. Enable `--gpu` only for commands that expose it and record the CPU/GPU build used.
2. Build and validate the complete small-to-large comparison bundle. It covers the query AND the close relatives produced by `/bio-phylogenomics`, with a presence/absence matrix and an integer copy-number matrix (orthogroup x genome):

   ```bash
   uv run --script ~/.agents/skills/bio-protein-clustering-pangenome/scripts/build_pangenome_artifacts.py \
     orthogroups.tsv --genomes genomes.tsv --marker-catalog marker_catalog.tsv \
     --marker-hits marker_hits.tsv --ncrna ncRNA_census.tsv \
     --out results/bio-protein-clustering-pangenome
   ```

   `orthogroups.tsv` is a long table with one row per protein: `orthogroup, protein_id, genome, contig, order, start, end`. Build it from the clustering output (OrthoFinder `Orthogroups.tsv` is wide and must be melted) joined with gene coordinates from the gene-calling GFF; `order` is the gene's rank along its contig. `genomes.tsv` has `genome, role (query|reference), genome_size, contig_count, n50, gene_count, coding_density, gc`. The marker catalog has `category, family_id, family_name`; marker hits have `genome, family_id, protein_id, e_value`; the ncRNA census uses the `/bio-gene-calling` columns. The driver requires globally unique protein IDs, at least two reference genomes for a defensible median, and a fresh output directory. It persists marker and ncRNA censuses alongside copy-number, presence/absence, family-comparison, genome-frontier, and conserved-neighborhood artifacts. `fixtures/` is a runnable three-genome contract test.
3. Compute core, accessory, cloud, and singleton partitions, and pangenome statistics (completeness, orthogroup occupancy). Identify single-copy orthologs for phylogenetic analysis, and separate paralogs from orthologs in multi-copy families.
4. Choose the comparison baseline from the literature-derived analysis playbook: closest relatives, a broader clade, environmental references, or a negative or control set.
5. Complete `relative_genome_metrics.tsv`: add tRNA and rRNA counts, any group-relevant property, a column that places the query in the relative distribution (percentile, min/median/max, record-class tag), and a column citing the literature that defines the group's known range.
6. Synteny and conserved neighborhoods: for each (query, relative) pair compute conserved gene neighborhoods (for example at least two collinear orthologs). Tool selection:
   - Pairwise, classical: MCScanX (*Nature Protocols* 2024 updated protocol).
   - Multi-genome at scale (more than two assemblies, up to more than 3 Gbp, more than 15% divergence): **ntSynt** (*BMC Biology* 2025, DOI: 10.1186/s12915-025-02455-w). It is alignment-free (minimizer graph) and does not detect duplications.
   - Strain-level work where duplication detection matters: SibeliaZ.

   Save `conserved_neighborhoods.tsv` with columns `query_block_id, relative, relative_block_id, members (ortholog IDs), intergenic_spacing_query, intergenic_spacing_relative, spacing_ratio, notes`. Flag conserved gene pairs and unusual spacing or expansions.
7. Identify the differences the playbook defines: query-specific families, missing expected families, expansions and contractions, unusual sharing patterns, and high-value unknowns. They go into `family_copy_number_comparison.tsv` (query versus relative-median fold change per family), coordinated with `/bio-annotation`'s family matrix.
8. Annotate candidate orthogroups with `/bio-annotation`; route representatives of high-value unknowns to `/bio-structure-annotation` when structure-based inference is appropriate.
9. Write a comparison summary that separates conserved lineage features from unusual or query-specific ones, states the baseline, and reports the comparative axes side by side with the relatives.

## Input Requirements

- `protein_fastas/` with one non-empty amino-acid FASTA per genome, for example `protein_fastas/genome_A.faa`. OrthoFinder uses each filename as a taxon identifier, so filenames must be unique and stable.
- `genomes.tsv` with one row per genome, its query/reference role, and the genome-property columns listed in step 2.
- For MMseqs2 clustering of a concatenated FASTA, `protein_to_genome.tsv` mapping every unique protein ID back to exactly one genome. A merged `proteins.faa` without this mapping cannot produce a valid genome-by-family matrix.

## Output

The driver writes the matrices, `family_copy_number_comparison.tsv`, both censuses, `conserved_neighborhoods.tsv` (adjacent ortholog pairs only), and `relative_genome_metrics.tsv` (genome properties and roles; you add the percentile placement, tRNA and rRNA counts, and the literature range). Files marked agent-authored come from you.

- results/bio-protein-clustering-pangenome/orthogroups.tsv (agent-authored)
- results/bio-protein-clustering-pangenome/presence_absence.parquet
- results/bio-protein-clustering-pangenome/copy_number_matrix.parquet
- results/bio-protein-clustering-pangenome/relative_genome_metrics.tsv
- results/bio-protein-clustering-pangenome/family_copy_number_comparison.tsv (`status` is one of `query_specific`, `missing_expected`, `expanded`, `contracted`, `conserved`, or `present_in_reference_minority`; the last means the reference median is 0 while at least one reference carries the family, so no fold change is reported and it is not a query-specific discovery)
- results/bio-protein-clustering-pangenome/marker_census.tsv
- results/bio-protein-clustering-pangenome/ncRNA_census.tsv
- results/bio-protein-clustering-pangenome/conserved_neighborhoods.tsv
- results/bio-protein-clustering-pangenome/closest_relative_comparison.tsv (agent-authored)
- results/bio-protein-clustering-pangenome/query_specific_candidates.tsv (agent-authored)
- results/bio-protein-clustering-pangenome/pangenome_report.md (agent-authored)
- results/bio-protein-clustering-pangenome/logs/

## Quality Gates

- [ ] Every per-genome FASTA is non-empty, amino-acid encoded, and has protein IDs unique across the full dataset.
- [ ] The genome manifest covers every FASTA exactly once; if proteins were concatenated for MMseqs2, every clustered protein maps to exactly one genome.
- [ ] The bundle holds marker-gene and ncRNA censuses alongside the copy-number and synteny tables for the same genome set.
- [ ] Query-specific, missing, expanded, and conserved orthogroups are reported separately; candidate orthogroups have annotation evidence or a stated follow-up.
- [ ] `relative_genome_metrics.tsv` places each query in the distribution of relatives and notes the literature-defined extreme of the inferred group.
- [ ] `family_copy_number_comparison.tsv` covers the full annotated family set, not only top candidates.
- [ ] `conserved_neighborhoods.tsv` includes intergenic spacing on both sides; broken synteny, unusual spacing, and expansions are flagged.
