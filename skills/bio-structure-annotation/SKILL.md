---
name: bio-structure-annotation
description: Predict protein structures and perform structure-based annotation. Use when sequence evidence is insufficient or structural similarity, confidence, domains, or complexes matter.
---

# Bio Structure Annotation

Structure prediction and structure-based annotation.

## Instructions

Tool guides and versions: [docs/README.md](docs/README.md).

1. Run a fast embedding screen with TM-Vec to triage candidate proteins by remote homology before incurring structure-prediction cost.
2. Predict structures on a GPU node. AlphaFold3 is intentionally not part of this stack (non-commercial license, large VRAM footprint, no clear quality gap for the workflows in this repo). Use:
   - **Boltz-2** (MIT license; CUDA; NVIDIA cuEquivariance kernels) as the default predictor — joint structure-and-affinity, ~1000× faster than FEP for binding-affinity estimation, comparable accuracy to AF3 on benchmarked complexes.
   - **ColabFold** v1.5.5+ with an **MMseqs2-GPU** MSA backend when a wider MSA than Boltz-2 builds is required (≈31.8× faster MSA generation versus the standard AF2 pipeline; *Nature Protocols* 2025, DOI: 10.1038/s41596-024-01060-5).
   - **ESMFold** for fast monomer pre-screening only (15–20 GB VRAM; lower accuracy than Boltz-2).
3. Search predicted or experimental structures with **Foldseek v9+**. Use `--gpu 1` on CUDA Turing or newer for the ProstT5-backed search (4–27× speedup). Consider Foldseek-Multimer when complex-vs-complex search is needed.
4. Annotate hits and route high-value unknowns back to `/bio-annotation` for sequence-side context, or to comparative analyses via `/bio-protein-clustering-pangenome`.
5. Build and validate commands with `scripts/run_structure_annotation.py`.
   Public MSA services receive biological sequences; `--use-msa-server` is
   rejected unless the user explicitly approved upload with
   `--approve-public-msa-upload`.

## Quick Reference

| Task | Action |
|------|--------|
| Validate and plan | `uv run --script scripts/run_structure_annotation.py ...` |

## Input Requirements

Prerequisites:
- Tools declared in the project's pinned Pixi environment. See `docs/README.md` for expected tools.
- Reference DB root: set `BIO_DB_ROOT` to the project or site-local database directory.
- Protein FASTA inputs are available.
Inputs:
- proteins.faa (FASTA protein sequences)

## Output

- results/bio-structure-annotation/structures/
- results/bio-structure-annotation/structure_hits.tsv
- results/bio-structure-annotation/structure_report.md
- results/bio-structure-annotation/logs/

## Quality Gates

- [ ] Prediction success rate meets project thresholds.
- [ ] Search hit thresholds meet project thresholds.
- [ ] On failure: retry with alternative parameters; if still failing, record in report and exit non-zero.
- [ ] Verify proteins.faa is non-empty and amino acid encoded.
- [ ] Verify Foldseek databases exist under the reference root.
- [ ] GPU Foldseek searches use a database produced by `makepaddedseqdb`.
- [ ] Public MSA upload has explicit user approval recorded before `--use_msa_server` is used.
