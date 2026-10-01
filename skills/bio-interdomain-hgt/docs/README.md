# bio-interdomain-hgt: tools and environment

Last verified: 2026-10-01
Tool version/release checked: DIAMOND v2.2.8, MAFFT v7.526, trimAl v1.5.1, IQ-TREE v3.1.4, geNomad v1.12.0, ETE 4.4.0 (bioconda; DIAMOND and IQ-TREE flags below run against these)
Official docs/manual: https://github.com/bbuchfink/diamond/wiki
Release/source: https://github.com/bbuchfink/diamond/releases

Pin all tools in the project's Pixi environment. Check the exact CLI with
`--help`/`--version` before large runs.

| Tool | Role | Notes |
|------|------|-------|
| DIAMOND (>=2.1) | forward search (`blastp`/`blastx`), reciprocal search, homolog gathering | `blastx -F 15 --range-culling --top 10` for genome-length queries; `--outfmt 6 ... full_sseq` to pull homolog seqs for trees; default sensitivity for classification at scale; set `--threads` |
| MMseqs2 (+GPU) | alternative to DIAMOND; building/clustering the arbiter | `easy-taxonomy --gpu` on CUDA nodes; clustered DB for speed |
| MAFFT | per-gene alignment | `--auto` |
| trimAl | alignment trimming | `-automated1` |
| IQ-TREE 3 | per-gene trees | `-m LG+G4 -B 1000 --seed <fixed> -keep-ident -T <n>`; the binary is `iqtree3` (older installs: `iqtree2`) |
| geNomad | "is this contig viral" context cross-check | needs `genomad_db` under `$BIO_DB_ROOT` |
| TaxonKit (>=0.20) | resolve lineages from the labels table / taxdump | 2025 NCBI rank update: `domain` replaces `superkingdom`, adds `realm` for viruses |
| seqkit | FASTA stats / extraction | |
| ETE 4 (`ete4`) | tree parsing and nesting/monophyly tests (`check_monophyly`) | load IQ-TREE `SH-aLRT/UFBoot` labels with `parser=1`; see the bio-phylogenomics ETE guide; no Qt needed |

## Environment
- `BIO_DB_ROOT`: site or project reference-DB root. The skill NEVER hardcodes absolute
  paths; everything is resolved relative to this.
- Heavy steps run on Slurm as size-balanced task arrays with an array throttle
  (`%N`) and explicit thread counts; the login node is for smoke tests only.

## Reciprocal-arbiter database
See `database-availability.md`. Minimum: one protein search DB spanning eukaryotes +
bacteria + archaea + viruses (incl. NCLDV + phage) + organelles, headers prefixed by
domain, with a `genome_id<TAB>lineage` labels file. Build/curate with
`/bio-fasta-database-curator` if absent.
