---
name: bio-phylogenomics
description: Build marker-gene alignments and ML trees and find closest relatives. Use when inferring phylogenies, placing genomes, choosing substitution models, or checking tree support.
---

# Bio Phylogenomics

Build marker-gene alignments and maximum-likelihood trees, identify closest relatives, and fetch the relative genomes that downstream comparisons need.

## Instructions

Tool guides, versions, and verified flags: [docs/README.md](docs/README.md).

1. Use the literature-derived analysis playbook to choose markers, reference sampling, rooting, and placement strategy for the inferred group.
2. Extract marker genes or SSU rRNA sequences for the queries and references.
3. Validate the marker and reference manifests and write a checksum-gated, fixed-seed plan; inspect `run_manifest.json`, then rerun with `--execute`:

   ```bash
   uv run --script skills/bio-phylogenomics/scripts/run_phylogenomics.py \
     markers.tsv --references references.tsv --seed 1729 \
     --tree-tool veryfasttree --threads 4 --out results/bio-phylogenomics/trees
   ```

   - `markers.tsv` columns: `marker_id fasta sequence_type` (`protein` or `nucleotide`); each FASTA holds the unaligned marker sequences.
   - `references.tsv` columns: `accession path sha256`; every reference file must match its checksum before anything runs.
   - Per marker the plan runs `mafft --auto`, `trimal -automated1`, then the tree tool, and writes `support.tsv`. `--tree-tool iqtree3` (default) runs `-m MFP -B 1000 --alrt 1000`; `veryfasttree` runs `-boot 1000` and adds `-nt` for nucleotide markers. `--threads` sets the thread count for MAFFT and the tree tool.
   - A stage is reused only when its outputs are non-empty and its `.done` marker exists.
   - `support.tsv` holds every internal support value on a 0–1 scale. IQ-TREE `SH-aLRT/UFBoot` labels become separate `sh_alrt` and `ufboot` rows; mixed 0–1 and 0–100 values within one support type fail validation. `--normalize-only TREE --out support.tsv` normalizes an existing tree.
4. Align with MAFFT v7.5 or later and trim with trimAl v1.5 (or ClipKIT when phylogenetically informed trimming is preferred).
5. Choose the tree builder by objective first, then by leaf count:
   - Exploratory placement, reference-set screening, benchmark iterations, or any time-bounded run: VeryFastTree v4.0.5, at any size. `VeryFastTree -boot 1000 -threads <n> alignment.faa > tree.nwk`; add `-nt` for nucleotides.
   - Final or publication trees up to about 2,000 taxa: IQ-TREE v3.1.4 with ModelFinder (`-m MFP`), UFBoot and SH-aLRT, and a fixed `--seed`.
   - Above about 2,000 taxa, or when memory or runtime is uncertain: VeryFastTree, with `-disk-computing` for very large trees.
   - Use `iqtree3 --fast` only when VeryFastTree is unavailable or the project requires IQ-TREE output; record the fallback in the report.
6. Post-process trees with ETE v4 (`ete4`): root, prune, collapse weak nodes, compute distances, and attach taxonomy or trait annotations. ETE's default Newick parser rejects IQ-TREE `SH-aLRT/UFBoot` labels; load those trees with `parser=1` as shown in [docs/ete-toolkit.md](docs/ete-toolkit.md).
7. Draw tree figures in greyscale by default. Use color only when it encodes information the reader must tell apart (for example the query versus references, or a small set of clades), choose a colorblind-safe palette, and pair color with a second encoding such as label text, shape, or line style.
8. Identify nearest neighbors and the closest named relatives for each query when the marker and reference set support that interpretation. Separate well-supported nearest relatives from weak placements.
9. Export `closest_relatives.tsv` with support values, distances, taxonomy, reference accessions, and uncertainty notes.
10. Fetch and persist the close-relative genomes and proteomes for downstream comparisons: `results/bio-phylogenomics/relatives/{accession}/genome.fna` and `proteins.faa`, plus `relatives_manifest.tsv` with accession, source database, taxonomy, genome size, gene count, and the reason for inclusion. Record each failed download with its reason. The comparative axes downstream cannot run without this table.
11. Pass the well-supported relatives, or a documented broader comparison set, to `/bio-protein-clustering-pangenome` and `/bio-annotation`.

Run tree inference for real datasets on a workstation or compute node with an explicit thread count; on HPC, submit it through `sbatch` with CPUs matched to `--threads`.

## Input Requirements

Prerequisites:
- MAFFT, trimAl, IQ-TREE 3, VeryFastTree, and ETE 4 pinned in the project's Pixi environment; see [docs/README.md](docs/README.md).

Inputs:
- `markers.tsv` with one unaligned FASTA per marker (`markers.faa`), or existing alignments
- `references.tsv` with reference file paths and SHA-256 checksums

## Output

Driver outputs under the `--out` directory (`results/bio-phylogenomics/trees/` above):
- one directory per marker (`{marker_id}/`) with `alignment.fasta`, `trimmed.fasta`, `support.tsv`, and stage `.done` markers
- the tree in the same directory: `tree.nwk` from VeryFastTree, or IQ-TREE's `.treefile` and companion files next to `trimmed.fasta`
- `run_manifest.json`: seed, tree tool, threads, inputs, and every stage command
- stdout: the last line is one JSON envelope `{ok, skill, out, manifest, warnings}` (driver stdout contract in AGENTS.md)

Workflow outputs under `results/bio-phylogenomics/`, written by the agent:
- (agent-authored) `closest_relatives.tsv`
- (agent-authored) `relatives/{accession}/genome.fna` and `relatives/{accession}/proteins.faa`
- (agent-authored) `relatives_manifest.tsv`
- (agent-authored) `phylo_report.md`, `logs/`

## Quality Gates

- [ ] `markers.faa` is non-empty and aligned sequences are consistent.
- [ ] Every reference checksum matches before alignment, and the run manifest records a positive fixed seed and the thread count.
- [ ] Alignment length and missingness meet the project thresholds.
- [ ] A stage is reused only when its outputs are non-empty and its `.done` marker exists.
- [ ] Internal supports are exported on a documented 0–1 scale without mixing IQ-TREE and VeryFastTree conventions.
- [ ] Support summaries meet the project thresholds, or the shortfall is reported.
- [ ] Marker and reference choices are justified against the literature-derived playbook.
- [ ] Closest relatives are reported with support and distance, or the uncertainty is stated.
- [ ] `relatives_manifest.tsv` is populated and the matching genome and proteome files exist, or each failure is recorded with a reason.
- [ ] Tree figures are greyscale unless color encodes information, and no information is carried by color alone.
- [ ] On execution failure, logs are kept and the failed command is reported; a retry follows a diagnosis and records the changed parameters. Parameters are never tuned only to pass a gate.
