---
name: bio-phylogenomics
description: Build and validate marker-gene alignments and phylogenetic trees. Use when inferring evolutionary relationships, choosing models, or checking tree support and contamination.
---

# Bio Phylogenomics

Build marker gene alignments and phylogenetic trees.

## Instructions

1. Validate marker/reference manifests and create a checksum-gated, fixed-seed execution plan:

   ```bash
   uv run --script skills/bio-phylogenomics/scripts/run_phylogenomics.py \
     markers.tsv --references references.tsv --seed 1729 \
     --out results/bio-phylogenomics
   # Inspect run_manifest.json, then add --execute.
   ```

   The driver restarts only from non-empty stage outputs paired with a stage `.done` marker. It normalizes internal support values from either 0–1 or 0–100 notation to `support.tsv` on a 0–1 scale. IQ-TREE `SH-aLRT/UFBoot` labels are emitted as separate `sh_alrt` and `ufboot` rows; mixed scales within one support type fail validation.
2. Extract marker genes or SSU rRNA sequences.
3. Align with MAFFT v7.5+ and trim with trimAl v1.4 (or ClipKIT when phylogenetically-informed trimming is preferred).
4. Build ML trees with support values. Choose by objective first, then leaf count:
   - Exploratory placement, benchmark iterations, reference-set screening, or any time-bounded analysis: use VeryFastTree v4.0 first, even below ~2,000 taxa. Prefer `VeryFastTree -boot 1000 -threads <n> < alignment.faa > tree.nw` for proteins and add `-nt` for nucleotide alignments.
   - Final or publication-quality trees up to ~2,000 taxa: IQ-TREE v3 (v3.1.2+) for comprehensive model selection, MAST/GTRpmix, UFBoot/SH-aLRT, and defensible final inference.
   - Above ~2,000 taxa, or when memory/runtime is uncertain: VeryFastTree v4.0 (multi-threaded, SIMD, `-disk-computing` for very large trees).
   - Use `iqtree3 -fast` only when VeryFastTree is unavailable or a project explicitly requires IQ-TREE-compatible exploratory output; record that fallback in the report.
5. Post-process trees with ETE v4 (`ete4`):
   - Compute tree statistics (branch lengths, distances, topology metrics).
   - Root, prune, or collapse nodes as needed.
   - Filter by bootstrap support.
   - Add taxonomic or trait annotations.
   - Generate publication-quality visualizations.
6. Use the literature-derived analysis playbook to choose markers, reference sampling, rooting, and placement strategy appropriate for the inferred group.
7. Identify nearest neighbors and closest named relatives for each query sequence/genome when the chosen marker/reference set supports that interpretation.
8. Export a closest-relatives table with support values, distances, taxonomy, reference accessions, and uncertainty notes.
9. **Fetch and persist the close-relative genomes and proteomes** that downstream comparative analyses will use. Save under `results/bio-phylogenomics/relatives/{accession}/genome.fna` and `proteins.faa`, plus `relatives_manifest.tsv` recording accession, source DB, taxonomy, genome size, gene count, and the reason for inclusion. If a relative cannot be downloaded, record the failure explicitly. Without this artifact, the comparative axes downstream cannot run.
10. Use well-supported relatives or a documented broader comparison set to guide downstream comparative analysis with `/bio-protein-clustering-pangenome` and `/bio-annotation`.

## Quick Reference

| Task | Action |
|------|--------|
| Run workflow | Follow the steps in this skill and capture outputs. |
| Validate inputs | Confirm required inputs and reference data exist. |
| Review outputs | Inspect reports and QC gates before proceeding. |
| Tool docs | See `docs/README.md`. |

## Input Requirements

Prerequisites:
- Tools declared in the project's pinned Pixi environment. See `docs/README.md` for expected tools.
- Marker gene set or alignments available.
Inputs:
- markers.faa (marker genes) or alignments.fasta

## Output

- results/bio-phylogenomics/alignments/
- results/bio-phylogenomics/trees/
- results/bio-phylogenomics/closest_relatives.tsv
- results/bio-phylogenomics/relatives/{accession}/genome.fna
- results/bio-phylogenomics/relatives/{accession}/proteins.faa
- results/bio-phylogenomics/relatives_manifest.tsv
- results/bio-phylogenomics/phylo_report.md
- results/bio-phylogenomics/logs/

## Quality Gates

- [ ] Alignment length and missingness meet project thresholds.
- [ ] Every reference checksum matches before alignment, and the run manifest records a positive fixed seed.
- [ ] A stage is reused only when its declared outputs are non-empty and its `.done` marker exists.
- [ ] Internal supports are exported on a documented 0–1 scale without mixing raw IQ-TREE and VeryFastTree conventions.
- [ ] Bootstrap support summary meets project thresholds.
- [ ] On failure: retry with alternative parameters; if still failing, record in report and exit non-zero.
- [ ] Verify markers.faa is non-empty and aligned sequences are consistent.
- [ ] Marker and reference choices are justified against the literature-derived analysis playbook.
- [ ] Closest relatives are reported with support/distance metrics or uncertainty is stated.
- [ ] Tree interpretation distinguishes well-supported nearest relatives from weakly supported placements.
- [ ] `relatives_manifest.tsv` is populated and the matching genome/proteome files are present on disk (or each failure is recorded with a reason).

## Examples

### Example 1: Expected input layout

```text
markers.faa (marker genes) or alignments.fasta
```

## Troubleshooting

**Issue**: Missing inputs or reference databases
**Solution**: Verify paths and permissions before running the workflow.

**Issue**: Low-quality results or failed QC gates
**Solution**: Review reports, adjust parameters, and re-run the affected step.
