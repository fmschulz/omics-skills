# Tooling

The default tool for each analysis step, with the version the skills' commands were last checked against (2026-10-01). These versions are not install pins. A project installs the newest release at setup, confirms the options the skill uses, and locks the release in `pixi.lock`. Databases are downloaded separately: the project uses the release the tool needs and records it. `tasks/METHODS.md` holds the tool version and source and the database release, source, date and checksum (the `bioinformatics-project` skill describes the steps). Agents still choose methods from the biological question, the input data, the hardware, and the literature for the organism or virus group.

| Step | CPU default (checked version) | GPU or accelerated option |
|---|---|---|
| Read QC (short) | fastp v1.3.7; BBDuk via `bryce911/bbtools:39.85` (contaminant and host removal) | None |
| Read QC (long) | Dorado (summaries, trimming), Chopper, Filtlong v0.3.1, Pychopper (full-length cDNA), Porechop_ABI 0.5.1 (fallback only) | Dorado on GPU |
| Read mapping (short) | bwa-mem2, BBMap via `bryce911/bbtools:39.85` | NVIDIA Parabricks `fq2bam` |
| Read mapping (long) | minimap2 v2.31 | Parabricks `minimap2`; `mm2-fast` and `mm2-gb` (minimap2 v2.24 base) |
| Assembly | SPAdes v4.2.0 (short-read isolates), metaSPAdes (short-read metagenomes), Flye v2.9.6 (long-read isolate draft), Autocycler v0.6.2 (bacterial isolate consensus), metaFlye (long-read metagenomes), metaMDBG v1.4 (HiFi metagenomes), myloasm v0.7.0 (optional) | None |
| Assembly QC | QUAST v5.3+ or MetaQUAST | None |
| Domain triage | QuickClade via `bryce911/bbtools:39.85` (`percontig` for assemblies), then GTDB-Tk 2.7.2 with GTDB R232, EukCC, vConTACT3 or GVClass by domain | None |
| Binning | QuickBin via `bryce911/bbtools:39.85`; CoverM v0.7.0 (contig depth) | SemiBin2 v2.3.0 (CUDA PyTorch) |
| Bin QC | CheckM2 v1.1.0, EukCC2 v2.1.3, GUNC v1.1.1 | None |
| Gene calling | Pyrodigal v3.7.1, pyrodigal-gv v0.3.2, BRAKER4 (eukaryotes), BRAKER3 v3.0.8 (legacy reproduction) | None |
| ncRNA | tRNAscan-SE v2.0.12 (with a domain flag), Infernal v1.1.5 (`cmsearch` with Rfam rRNA models), ARAGORN v1.2.41+ (tmRNA) | None |
| Annotation | DIAMOND v2.2.1 (clustered nr preferred), eggNOG-mapper v2.1.15, InterProScan 5.78-109.0 or 6.0.2.2, pyhmmer v0.10+, TaxonKit v0.20.0 | MMseqs2-GPU |
| Phylogenetics | VeryFastTree v4.0.5 (exploratory, or more than 2,000 taxa), IQ-TREE v3.1.4 (final trees up to 2,000 taxa), MAFFT v7.526, trimAl v1.5.1, ete4 v4.4.0 | None |
| Orthology and pangenomes | OrthoFinder v3.1.5, ProteinOrtho v6.3.6 (large pangenomes), MMseqs2 v18-8cc5c | MMseqs2-GPU (v16 or newer) |
| Synteny | MCScanX, ntSynt, SibeliaZ | None |
| Viromics | geNomad v1.12.0 (database v1.9), CheckV v1.1.1 (database v1.5), VirSorter2 v2.2.4, vConTACT3 3.2.4 (prokaryotic viruses), GVClass v2.0.3 with resources v2.0.0 (giant viruses) | None |
| Structure | TM-Vec fork 1.1.0 at commit `6bdf11a` (triage), Foldseek 10-941cd33 | Boltz v2.2.1 (default predictor), ColabFold v1.6.1 with MMseqs2-GPU MSAs, ESMFold (pre-screen), Foldseek `--gpu 1` |
| Statistics and ML | LinkML v1.11.1, Pydantic v2.13.4, DuckDB v1.5.3, scikit-learn 1.8.0, XGBoost v3.2.0 | XGBoost `device=cuda`, RAPIDS cuML |

A GPU tool is an alternative, not an upgrade: it needs matching hardware and the same validation as the CPU path. When a skill changes a default tool or a checked version, update this table in the same commit; `python3 scripts/check_tool_versions.py` lists the tool guides whose checked version is behind the newest GitHub release.
