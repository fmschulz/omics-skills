# Structure annotation

**Last verified:** 2026-11-11
**Tool version/release checked:** Boltz v2.2.1 (docs and source of the tag, not run); ColabFold v1.6.3 (source of the tag, not run); Foldseek 10-941cd33 (bioconda build, and the static GPU build at commit 39b02b9; both run); TM-Vec 1.0.2 (original) and valentynbez/tmvec fork 1.1.0 at commit 6bdf11a (2026-07-24, still the head of the fork's default branch on 2026-11-11; source of that commit, not run)
**Official docs/manual:** https://github.com/jwohlwend/boltz ; https://github.com/sokrypton/ColabFold ; https://github.com/steineggerlab/foldseek ; https://github.com/tymor22/tm-vec ; https://github.com/valentynbez/tmvec
**Release/source:** https://github.com/jwohlwend/boltz/releases/tag/v2.2.1 ; https://github.com/sokrypton/ColabFold/releases/tag/v1.6.3 ; https://github.com/steineggerlab/foldseek/releases/tag/10-941cd33 ; https://github.com/tymor22/tm-vec/releases/tag/1.0.2

Shared rules (hypotheses, thresholds as results, environment, scheduler, threads): see the shared rules in [../SKILL.md](../SKILL.md). Tool notes kept in full: [boltz.md](boltz.md) and [tm-vec.md](tm-vec.md).

## Use when

Sequence search gives weak or no hits, or you need a fold, a complex model or a prediction confidence. Inputs: `proteins.faa` (amino acids), a Boltz YAML for prediction, one Foldseek query structure (PDB or mmCIF) with a target database prefix, and a TM-Vec database (`.npz`). `BIO_DB_ROOT` points to the project or site database directory.

## Tool choice

| Case | Default | Use the alternative when |
| --- | --- | --- |
| Triage of many candidates by remote homology | TM-Vec (pinned fork) | - |
| Monomer, complex, protein-ligand affinity | Boltz-2 (MIT, CUDA) | - |
| A deeper MSA than Boltz-2 builds | ColabFold with MMseqs2-GPU MSAs | - |
| Fast monomer pre-screen | ESMFold | final models always go to Boltz-2 |
| Structure search, clustering | Foldseek | `easy-multimersearch` for complex against complex |

## Rules a model would not guess

- AlphaFold3 is not part of this stack: non-commercial license and a large VRAM footprint. Use Boltz-2.
- Run prediction on a GPU node. Keep Boltz in its own pixi environment (`boltz[cuda]` adds the cuEquivariance kernels).
- Boltz YAML: `version: 1` and a non-empty `sequences` list. Each item holds one entity (`protein`, `dna`, `rna`, `ligand`) with an `id`. A ligand has exactly one of `smiles` or `ccd`.
- Without `--use_msa_server`, every protein needs an `msa:` value: a path to an `.a3m` file, or `empty` for single-sequence mode (lower accuracy, not recommended).
- `--use_msa_server` sends sequences to a public server. Pass it only with the user's explicit approval, recorded first. `colabfold_batch` without local MSAs also queries a public server; the same approval applies.
- Foldseek `--gpu 1` needs CUDA Turing or newer and a target database built with `makepaddedseqdb`. Search the padded database, not the original. Use the static GPU build (`https://mmseqs.com/foldseek/foldseek-linux-gpu.tar.gz`): on an RTX A6000, the bioconda `foldseek` 10-941cd33 accepted `--gpu 1`, then ran at 100% CPU without a result until it was killed after 60 s, while the GPU build returned the same hits in 2 s.
- Pass an explicit `--threads` to Foldseek; its default is all cores.
- On a RAM-bound Foldseek search, `--sort-by-structure-bits 0` cuts memory by about 75%.
- The pinned TM-Vec fork (commit 6bdf11a) differs from the original 1.0.2 CLI. Both subcommands need `--input-fasta`; `--query` from the fork's README is rejected. `--output` is a folder, and `tmvec search` writes `results.tsv` into it. It returns 5 neighbors per query (`--k-nearest`) and skips sequences over 1024 residues. Compute nodes without internet need the model files and `--local` at `build-db`; keep the stored model paths valid.
- Keep the TM-Vec database checksum and the filter thresholds with the results.

## Commands

```bash
# TM-Vec triage (build-db writes $TMDB.npz; search writes $OUT/tmvec/results.tsv)
tmvec build-db --input-fasta $REF_FASTA --output $TMDB
tmvec search --input-fasta $QUERY_FAA --database $TMDB.npz --output $OUT/tmvec

# Boltz-2 (drop --use_msa_server unless the user approved the public upload)
boltz predict $YAML --out_dir $OUT/boltz [--use_msa_server]

# Foldseek search (CPU); $QUERY is a PDB or mmCIF file
foldseek easy-search $QUERY $FOLDSEEK_DB $OUT/foldseek_hits.tsv $OUT/foldseek_tmp --threads $THREADS
# Foldseek GPU: pad the database once, then search it
foldseek makepaddedseqdb $FOLDSEEK_DB ${FOLDSEEK_DB}_pad
foldseek easy-search $QUERY ${FOLDSEEK_DB}_pad $OUT/foldseek_hits.tsv $OUT/foldseek_tmp --threads $THREADS --gpu 1
# Complex against complex
foldseek easy-multimersearch $QUERY_COMPLEX $TARGET_COMPLEX $OUT/multimer_hits.tsv $OUT/foldseek_tmp --threads $THREADS
```

The Foldseek lines ran on 2026-11-11 on six PDB structures (`easy-search`, `makepaddedseqdb`, the GPU search) and on three hemoglobin entries (`easy-multimersearch` with a directory as target). The TM-Vec, Boltz and ColabFold lines were checked against the source of their pinned versions (options, defaults, output names) and were not run: the ProtT5 weights and the MSA databases are larger than a smoke test allows.

```bash
# ColabFold with MMseqs2-GPU MSAs; $MMSEQS is the mmseqs binary, $CF_DB the local ColabFold database
colabfold_search --gpu 1 --threads $THREADS --mmseqs $MMSEQS $QUERY_FAA $CF_DB $OUT/msas
colabfold_batch $OUT/msas $OUT/colabfold
```

## QC gates to record

- Prediction success rate: the cutoff chosen for this project, the observed rate (models finished over models requested) and pass or fail. A failure is reported, not tuned away.
- Search hit thresholds: the cutoff for each search (TM-Vec score, Foldseek E-value or TM-score), the number of hits kept at it, and pass or fail. Write the thresholds into `structure_hits.tsv`. A failure is reported, not tuned away.
- `proteins.faa` is non-empty and amino-acid encoded; the Foldseek databases exist under the reference root.
- GPU Foldseek searches use a `makepaddedseqdb` database.
- Explicit user approval for any public MSA upload is recorded before the flag is used.

## Outputs

The agent writes these. A restartable project driver follows the `bioinformatics-project` skill. Under `<run>/structure/`, where `<run>` is the dated run directory `results/<date>_<name>/` that `bioinformatics-project` defines:
- `boltz/`: predictions and confidence files
- `foldseek_hits.tsv`
- `tmvec/results.tsv`
- `structure_hits.tsv`: merged, filtered hits with the thresholds used
- `structure_report.md` and `logs/`

Send high-value unknowns back to the annotation stage for sequence-side context.
