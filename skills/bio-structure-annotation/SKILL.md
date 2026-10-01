---
name: bio-structure-annotation
description: Predict protein or complex structures and find structural homologs. Use when sequence search gives weak or no hits, or when a fold, complex model, or prediction confidence is needed.
---

# Bio Structure Annotation

Structure prediction and structure-based annotation.

## Instructions

Tool guides and versions: [docs/README.md](docs/README.md).

1. Run a fast embedding screen with TM-Vec to triage candidate proteins by remote homology before incurring structure-prediction cost.
2. Predict structures on a GPU node through `sbatch`. AlphaFold3 is not part of this stack (non-commercial license, large VRAM footprint). Use:
   - **Boltz-2** (MIT license, CUDA) as the default predictor for monomers, complexes, and protein-ligand binding affinity.
   - **ColabFold** v1.5.5+ with an **MMseqs2-GPU** MSA backend when a deeper MSA than Boltz-2 builds is required. Kallenborn et al. (2025) *Nature Methods* https://doi.org/10.1038/s41592-025-02819-8 report that MMseqs2-GPU makes ColabFold prediction 31.8× faster than the standard AlphaFold2 pipeline.
   - **ESMFold** for fast monomer pre-screening only; route candidates to Boltz-2 for final models.
3. Search predicted or experimental structures with **Foldseek v9+**. On CUDA Turing or newer, `--gpu 1` enables the GPU ungapped prefilter and needs a target database built with `makepaddedseqdb`; the same paper reports a 4-27× Foldseek speedup. Use `easy-multimersearch` for complex-vs-complex search.
4. Annotate hits and route high-value unknowns back to `/bio-annotation` for sequence-side context, or to comparative analyses via `/bio-protein-clustering-pangenome`.
5. Build and validate commands with `scripts/run_structure_annotation.py`. It prints the command plan as JSON and, with `--execute`, runs it.
   Public MSA services receive biological sequences; `--use-msa-server` (passed to Boltz as `--use_msa_server`) is
   rejected unless the user explicitly approved upload with
   `--approve-public-msa-upload`.

## Quick Reference

| Task | Action |
|------|--------|
| Validate and plan | `uv run --script skills/bio-structure-annotation/scripts/run_structure_annotation.py --boltz-yaml complex.yaml --out-dir results/bio-structure-annotation` |
| Structure search | add `--foldseek-query query.pdb --foldseek-db targetDB` (with `--gpu`, pass `--foldseek-padded-db`) |
| Embedding screen | add `--tmvec-query proteins.faa --tmvec-db db.npz` |

## Input Requirements

Prerequisites:
- Tools declared in the project's pinned Pixi environment. See `docs/README.md` for expected tools.
- Reference DB root: set `BIO_DB_ROOT` to the project or site-local database directory.
- Protein FASTA inputs are available.
Inputs:
- proteins.faa (FASTA protein sequences)
- Boltz input YAML (`version: 1` with a `sequences` list; see `fixtures/boltz-complex.yaml`)
- One Foldseek query structure file (PDB/mmCIF) and a target database prefix; a padded database for GPU search
- TM-Vec database (`.npz` from `tmvec build-db`)

## Output

Written by the driver's `--execute` run:
- results/bio-structure-annotation/boltz/ (Boltz predictions and confidence files)
- results/bio-structure-annotation/foldseek_hits.tsv
- results/bio-structure-annotation/tmvec/results.tsv (TM-Vec hits; `tmvec search` writes into the `tmvec/` folder)
- The command plan on stdout, or in `--plan-out` when given

Written by the agent:
- results/bio-structure-annotation/structure_hits.tsv (merged, filtered hits with thresholds)
- results/bio-structure-annotation/structure_report.md
- results/bio-structure-annotation/logs/

## Quality Gates

- [ ] Prediction success rate meets project thresholds.
- [ ] Search hit thresholds meet project thresholds.
- [ ] On execution failure, preserve logs and report the failed command; retry only after diagnosing the cause and recording the changed parameters. Report unmet biological thresholds as results; never tune parameters solely to pass a gate.
- [ ] Verify proteins.faa is non-empty and amino acid encoded.
- [ ] Verify Foldseek databases exist under the reference root.
- [ ] GPU Foldseek searches use a database produced by `makepaddedseqdb`.
- [ ] Public MSA upload has explicit user approval recorded before `--use-msa-server` is passed.
- [ ] GPU prediction and search run through `sbatch` on a GPU node, never on a login node.
