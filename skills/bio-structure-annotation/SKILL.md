---
name: bio-structure-annotation
description: Predict protein or complex structures and find structural homologs. Use when sequence search gives weak or no hits, or when a fold, complex model, or prediction confidence is needed.
disable-model-invocation: true
---

# Bio Structure Annotation

Structure prediction and structure-based annotation. Shared pipeline rules: read `~/.agents/skills/omics-pipeline/SKILL.md` first (in a plugin install, `../omics-pipeline/SKILL.md` from this file).

## Instructions

Tool guides and versions: [docs/README.md](docs/README.md).

1. Run a fast embedding screen with TM-Vec to triage candidate proteins by remote homology before incurring structure-prediction cost.
2. Predict structures on a GPU node. AlphaFold3 is not part of this stack (non-commercial license, large VRAM footprint). Use:
   - **Boltz-2** (MIT license, CUDA) as the default predictor for monomers, complexes, and protein-ligand binding affinity.
   - **ColabFold** with an **MMseqs2-GPU** MSA backend when a deeper MSA than Boltz-2 builds is required.
   - **ESMFold** for fast monomer pre-screening only; route candidates to Boltz-2 for final models.
3. Search predicted or experimental structures with **Foldseek**. On CUDA Turing or newer, `--gpu 1` enables the GPU ungapped prefilter and needs a target database built with `makepaddedseqdb`. Use `easy-multimersearch` for complex-vs-complex search.
4. Annotate hits and route high-value unknowns back to `/bio-annotation` for sequence-side context, or to comparative analyses via `/bio-protein-clustering-pangenome`.
5. Build and validate commands with the driver. It prints the command plan as JSON, then the one-line JSON envelope as the last line of stdout, and with `--execute` runs the plan first. A driver-detected failure prints the error envelope as the last line, the message on stderr, and exits 2:

   ```bash
   uv run --script ~/.agents/skills/bio-structure-annotation/scripts/run_structure_annotation.py \
     --boltz-yaml complex.yaml --out-dir results/bio-structure-annotation
   ```

   Add `--foldseek-query query.pdb --foldseek-db targetDB` for structure search (with `--gpu`, also `--foldseek-padded-db`; `--threads N` sets the Foldseek thread count, default 1) and `--tmvec-query proteins.faa --tmvec-db db.npz` for the embedding screen.

   Without `--use-msa-server`, every protein in the Boltz YAML needs an `msa:` value: a path to an `.a3m` file, or `empty` for single-sequence mode (lower accuracy). The driver rejects a protein without one.

   Public MSA services receive biological sequences. `--use-msa-server` (passed to Boltz as `--use_msa_server`) is rejected unless the user explicitly approved the upload with `--approve-public-msa-upload`.

## Input Requirements

- `BIO_DB_ROOT` set to the project or site-local database directory.
- `proteins.faa` (amino-acid FASTA).
- Boltz input YAML (`version: 1` with a `sequences` list; see `fixtures/boltz-complex.yaml`).
- One Foldseek query structure file (PDB/mmCIF) and a target database prefix; a padded database for GPU search.
- TM-Vec database (`.npz` from `tmvec build-db`).

## Output

Written by the driver's `--execute` run:
- results/bio-structure-annotation/boltz/ (Boltz predictions and confidence files)
- results/bio-structure-annotation/foldseek_hits.tsv
- results/bio-structure-annotation/tmvec/results.tsv (TM-Vec hits; `tmvec search` writes into the `tmvec/` folder)
- The command plan on stdout (before the envelope), or in `--plan-out` when given
- The envelope on the last stdout line: `{"ok": true, "skill", "out", "warnings"}`, plus `"manifest"` (the `--plan-out` path) when given

Written by the agent:
- results/bio-structure-annotation/structure_hits.tsv (merged, filtered hits with thresholds)
- results/bio-structure-annotation/structure_report.md
- results/bio-structure-annotation/logs/

## Quality Gates

- [ ] Prediction success rate: record the cutoff chosen for this project, the observed rate (models finished over models requested) and the outcome (pass or fail). A failure is reported, not tuned away.
- [ ] Search hit thresholds: record the cutoff chosen for each search (TM-Vec score, Foldseek E-value or TM-score), the number of hits kept at it and the outcome; write the thresholds into `structure_hits.tsv`. A failure is reported, not tuned away.
- [ ] `proteins.faa` is non-empty and amino-acid encoded; the Foldseek databases exist under the reference root.
- [ ] GPU Foldseek searches use a database produced by `makepaddedseqdb`.
- [ ] Public MSA upload has explicit user approval recorded before `--use-msa-server` is passed.
