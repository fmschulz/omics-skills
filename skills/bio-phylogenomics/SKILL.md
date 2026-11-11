---
name: bio-phylogenomics
description: Build marker-gene alignments and ML trees and find closest relatives. Use when inferring phylogenies, placing genomes, choosing substitution models, or checking tree support.
disable-model-invocation: true
---

# Bio Phylogenomics

Build marker-gene alignments and maximum-likelihood trees, identify closest relatives, and fetch the relative genomes that downstream comparisons need. Shared pipeline rules: read `~/.agents/skills/omics-pipeline/SKILL.md` first (in a plugin install, `../omics-pipeline/SKILL.md` from this file).

## Instructions

Tool guides, versions, and verified flags: [docs/README.md](docs/README.md).

1. Use the literature-derived analysis playbook to choose markers, reference sampling, rooting, and placement strategy for the inferred group.
2. Extract marker genes or SSU rRNA sequences for the queries and references.
3. Validate the marker and reference manifests and write a checksum-gated, fixed-seed plan; inspect `run_manifest.json`, then rerun with `--execute`:

   ```bash
   uv run --script ~/.agents/skills/bio-phylogenomics/scripts/run_phylogenomics.py \
     markers.tsv --references references.tsv --seed 1729 \
     --tree-tool veryfasttree --threads 4 --out results/bio-phylogenomics/trees
   ```

   - `markers.tsv` columns: `marker_id fasta sequence_type` (`protein` or `nucleotide`); each FASTA holds the unaligned marker sequences.
   - `references.tsv` columns: `accession path sha256`; every reference file must match its checksum before anything runs.
   - Per marker the plan runs `mafft --auto`, `trimal -automated1`, then the tree tool, and writes `support.tsv`. `--tree-tool iqtree3` (default) runs `-m MFP -B 1000 --alrt 1000`; `veryfasttree` runs `-boot 1000` and adds `-nt` for nucleotide markers. `--threads` sets the thread count for MAFFT and the tree tool.
   - A stage is reused only when its outputs are non-empty and its `.done` marker exists.
   - `support.tsv` holds every internal support value on a 0–1 scale. IQ-TREE `SH-aLRT/UFBoot` labels become separate `sh_alrt` and `ufboot` rows; mixed 0–1 and 0–100 values within one support type fail validation. `--normalize-only TREE --out support.tsv` normalizes an existing tree.
4. The driver aligns with MAFFT and trims with trimAl; use ClipKIT instead when phylogenetically informed trimming is preferred.
5. Choose the tree builder by objective first, then by leaf count:
   - Exploratory placement, reference-set screening, benchmark iterations, or any time-bounded run: VeryFastTree, at any size. `VeryFastTree -boot 1000 -threads <n> alignment.faa > tree.nwk`; add `-nt` for nucleotides.
   - Final or publication trees up to about 2,000 taxa: IQ-TREE 3 with ModelFinder (`-m MFP`), UFBoot and SH-aLRT, and a fixed `--seed`.
   - Above about 2,000 taxa, or when memory or runtime is uncertain: VeryFastTree, with `-disk-computing` for very large trees.
   - Use `iqtree3 --fast` only when VeryFastTree is unavailable or the project requires IQ-TREE output; record the fallback in the report.
6. Post-process trees with ETE 4 (`ete4`): root, prune, collapse weak nodes, compute distances, and attach taxonomy or trait annotations. ETE's default Newick parser rejects IQ-TREE `SH-aLRT/UFBoot` labels such as `98.7/100`: load those trees with `parser=1` and split the labels into properties (example in [docs/README.md](docs/README.md)). Read the labels before rerooting, because a label stored as a node name stays on its node and can end up on the wrong side of a rerooted branch.
7. Draw tree figures following `beautiful-data-viz`.
8. Identify nearest neighbors and the closest named relatives for each query when the marker and reference set support that interpretation. Separate well-supported nearest relatives from weak placements.
9. Export `closest_relatives.tsv` with support values, distances, taxonomy, reference accessions, and uncertainty notes.
10. Fetch and persist the close-relative genomes and proteomes for downstream comparisons: `results/bio-phylogenomics/relatives/{accession}/genome.fna` and `proteins.faa`, plus `relatives_manifest.tsv` with accession, source database, taxonomy, genome size, gene count, and the reason for inclusion. Record each failed download with its reason. The comparative axes downstream cannot run without this table.
11. Pass the well-supported relatives, or a documented broader comparison set, to `/bio-protein-clustering-pangenome` and `/bio-annotation`.

## Input Requirements

- MAFFT, trimAl, IQ-TREE 3, VeryFastTree, and ETE 4; versions in [docs/README.md](docs/README.md).
- `markers.tsv` with one unaligned FASTA per marker (`markers.faa`), or existing alignments
- `references.tsv` with reference file paths and SHA-256 checksums

## Output

Driver outputs under the `--out` directory (`results/bio-phylogenomics/trees/` above):
- one directory per marker (`{marker_id}/`) with `alignment.fasta`, `trimmed.fasta`, `support.tsv`, and stage `.done` markers
- the tree in the same directory: `tree.nwk` from VeryFastTree, or IQ-TREE's `.treefile` and companion files next to `trimmed.fasta`
- `run_manifest.json`: seed, tree tool, threads, inputs, and every stage command. A failed `--execute` run also writes it, with the status of each step reached (`failed` on the failing step), and the error envelope names the marker and the failed command

Workflow outputs under `results/bio-phylogenomics/`, written by the agent:
- (agent-authored) `closest_relatives.tsv`
- (agent-authored) `relatives/{accession}/genome.fna` and `relatives/{accession}/proteins.faa`
- (agent-authored) `relatives_manifest.tsv`
- (agent-authored) `phylo_report.md`, `logs/`

## Quality Gates

- [ ] Every reference checksum matches before alignment, and the run manifest records a positive fixed seed and the thread count.
- [ ] Internal supports are exported on a documented 0–1 scale without mixing IQ-TREE and VeryFastTree conventions.
- [ ] Marker and reference choices are justified against the literature-derived playbook.
- [ ] Closest relatives are reported with support and distance, or the uncertainty is stated.
- [ ] `relatives_manifest.tsv` is populated and the matching genome and proteome files exist, or each failure is recorded with a reason.
