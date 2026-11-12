# Tooling

The default tool for each analysis step, with the version the skills' commands were last checked against. Each tool guide records its own check date; the latest re-check was on 2026-11-11, and rows whose tools no guide re-ran (Dorado, Pychopper, Parabricks, VirSorter2, ESMFold, pyhmmer) keep their earlier versions. These versions are not install pins. A project installs the newest release at setup, confirms the options the skill uses, and locks the release in `pixi.lock`. Databases are downloaded separately: the project uses the release the tool needs and records it. `tasks/METHODS.md` holds the tool version and source and the database release, source, date and checksum (the `bioinformatics-project` skill describes the steps). Agents still choose methods from the biological question, the input data, the hardware, and the literature for the organism or virus group.

| Step | CPU default (checked version) | GPU or accelerated option |
|---|---|---|
| Read QC (short) | fastp v1.4.0; BBDuk via `bryce911/bbtools:39.85` (contaminant and host removal) | None |
| Read QC (long) | Dorado (summaries, trimming), Chopper 0.15.0, Filtlong v0.3.1, Pychopper (full-length cDNA), Porechop_ABI 0.5.1 (fallback only) | Dorado on GPU |
| Read mapping (short) | bwa-mem2 2.3, BBMap via `bryce911/bbtools:39.85` | NVIDIA Parabricks `fq2bam` |
| Read mapping (long) | minimap2 v2.31 | Parabricks `minimap2`; `mm2-fast` and `mm2-gb` (minimap2 v2.24 base) |
| Assembly | SPAdes v4.3.0 (short-read isolates), metaSPAdes (short-read metagenomes), Flye v2.9.6 (long-read isolate draft), Autocycler v0.8.0 (bacterial isolate consensus), metaFlye (long-read metagenomes), metaMDBG v1.4 (HiFi metagenomes; its `--in-ont` mode is nanoMDBG, an alternative for ONT metagenomes that is not independently benchmarked), myloasm v0.7.0 (optional) | None |
| Assembly QC | QUAST v5.3+ or MetaQUAST | None |
| Domain triage | QuickClade via `bryce911/bbtools:39.85` (`percontig` for assemblies), then GTDB-Tk 2.8.0 with GTDB R232, EukCC, vConTACT3 or GVClass by domain | None |
| Binning | QuickBin via `bryce911/bbtools:39.85` (default for speed and a fixed time budget); CoverM v0.8.0 (contig depth); MetaBAT2 v2.18 (fastest) | SemiBin2 v2.6.0 (CUDA PyTorch) or COMEBin when accuracy matters most |
| Bin QC | CheckM2 v1.1.0, EukCC v2.2.0, GUNC v1.1.1 | None |
| Gene calling | Pyrodigal v3.7.1, pyrodigal-gv v0.3.2, BRAKER4 v0.6.0-beta (eukaryotes), BRAKER3 v3.0.8 (legacy reproduction) | Tiberius for eukaryotes (preprint, not independently benchmarked) |
| ncRNA | tRNAscan-SE v2.0.13 (with a domain flag), Infernal v1.1.5 (`cmsearch` with Rfam rRNA models), ARAGORN v1.2.41+ (tmRNA) | None |
| Annotation | DIAMOND v2.2.8 (clustered nr preferred), eggNOG-mapper v2.1.15 on eggNOG 5 (v3 for eggNOG 7 is still a beta), Bakta as the alternative for prokaryote genomes, InterProScan 5.78-109.0 or 6.0.3.0, pyhmmer v0.10+, TaxonKit v0.20.0 | MMseqs2-GPU |
| Phylogenetics | VeryFastTree v4.0.5 (exploratory, or more than 2,000 taxa), IQ-TREE v3.1.4 (final trees up to 2,000 taxa), MAFFT v7.526, trimAl v1.5.1, ete4 v4.4.0 | None |
| Viromics | geNomad v1.13.0 (database v1.9), CheckV v1.1.1 (database v1.5), VirSorter2 v2.2.4, vConTACT3 3.2.4 (prokaryotic viruses), GVClass v2.1.0 with resources v2.1.0 (giant viruses) | None |
| Structure | TM-Vec fork 1.1.0 at commit `6bdf11a` (triage), Foldseek 10-941cd33 | Boltz v2.2.1 (default predictor), ColabFold v1.6.3 with MMseqs2-GPU MSAs, ESMFold (pre-screen), Foldseek `--gpu 1` (static GPU build) |

A GPU tool is an alternative, not an upgrade: it needs matching hardware and the same validation as the CPU path. When a skill changes a default tool or a checked version, update this table in the same commit; `python3 scripts/check_tool_versions.py` lists the tool guides whose checked version is behind the newest GitHub release.
