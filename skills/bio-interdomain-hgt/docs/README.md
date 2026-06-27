# bio-interdomain-hgt — tools & environment

Last verified: 2026-06-27
Tool version/release checked: DIAMOND v2.2.x, MAFFT v7.5+, trimAl v1.4, IQ-TREE 2/3, geNomad v1.8+ (see table)
Official docs/manual: https://github.com/bbuchfink/diamond/wiki
Release/source: https://github.com/bbuchfink/diamond/releases

All tools are expected on the active environment (Pixi/conda/system). Validate the
exact CLI with `--help`/`--version` before large runs; pin versions in the project
env, not here.

| Tool | Role | Notes |
|------|------|-------|
| DIAMOND (>=2.1) | forward search (`blastp`/`blastx`), reciprocal search, homolog gathering | `blastx -F 15 --range-culling --top 10` for genome-length queries; `--outfmt 6 ... full_sseq` to pull homolog seqs for trees; DEFAULT sensitivity for classification at scale |
| MMseqs2 (+GPU) | alternative to DIAMOND; building/clustering the arbiter | `easy-taxonomy --gpu` on CUDA nodes; clustered DB for speed |
| MAFFT | per-gene alignment | `--auto` |
| trimAl | alignment trimming | `-automated1` |
| IQ-TREE (2/3) | per-gene trees | `-m LG+G4 -B 1000 --seed <fixed> -keep-ident`; binary may be `iqtree` or `iqtree2/3` |
| geNomad | "is this contig viral" context cross-check | needs `genomad_db` under `$BIO_DB_ROOT` |
| TaxonKit (>=0.20) | resolve lineages from the labels table / taxdump | 2025 NCBI rank update: `domain` replaces `superkingdom`, adds `realm` for viruses |
| seqkit | FASTA stats / extraction | |
| ete3 / dendropy | tree parsing + nesting/monophyly test | parse-only; no Qt needed |

## Environment
- `BIO_DB_ROOT` — site/project reference-DB root. The skill NEVER hardcodes absolute
  paths; everything is resolved relative to this.
- Heavy steps run on SLURM as size-balanced task arrays; the login node is for
  smoke-tests only.

## Reciprocal-arbiter database
See `database-availability.md`. Minimum: one protein search DB spanning eukaryotes +
bacteria + archaea + viruses (incl. NCLDV + phage) + organelles, headers prefixed by
domain, with a `genome_id<TAB>lineage` labels file. Build/curate with
`/bio-fasta-database-curator` if absent.
