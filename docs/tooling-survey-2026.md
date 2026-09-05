# Tooling Survey 2026

This page records the default tool choices referenced by the agents and bioinformatics skills. It is a practical baseline, not a claim that every workflow should use the same tool. Agents should still choose methods from the biological question, input data, available hardware, and the literature for the inferred organism or virus group.

| Step | CPU baseline | GPU or accelerated option |
|---|---|---|
| Read QC (long) | Dorado summaries/trimming, Chopper, Filtlong, Pychopper for full-length cDNA; Porechop_ABI only as a documented fallback | — |
| Read mapping (short) | bwa-mem2, BBMap | NVIDIA Parabricks `fq2bam` |
| Read mapping (long) | `minimap2` v2.31 | `mm2-fast` (AVX-512), `mm2-gb`, `mm2-ax` |
| Assembly | SPAdes v4.2.0 (Illumina), Flye v2.9.6 (long-read isolate draft), Autocycler v0.6.2 (bacterial isolate consensus), Flye `--meta` / metaFlye (long-read metagenome), metaMDBG 1.1 (HiFi metagenome), myloasm (optional) | — |
| Domain taxonomy triage | BBTools QuickClade via `bryce911/bbtools:39.85` container (`percontig` for assemblies), then GTDB-Tk / EukCC / vConTACT3 / GVClass by domain | — |
| Binning | QuickBin via `bryce911/bbtools:39.85` container | SemiBin2 v2.3.0 (CUDA-backed PyTorch) |
| Bin QC | CheckM2 v1.1.0, EukCC2 v2.1.3, GUNC v1.1.1 | — |
| Gene calling | Pyrodigal v3.7.1, pyrodigal-gv v0.3.2, BRAKER4 for current eukaryotic workflows; BRAKER3 v3.0.8 for legacy reproduction | — |
| ncRNA | tRNAscan-SE v2.0.12, Infernal v1.1.5 (`cmsearch` against Rfam SSU/LSU CMs) | — |
| Annotation | DIAMOND v2.2.1 (clusterednr preferred), eggNOG-mapper v2.1.15, InterProScan 5.77-108.0, pyhmmer, TaxonKit v0.20 | MMseqs2-GPU |
| Phylogenetics | VeryFastTree v4 (exploratory/time-bounded trees and >2,000 taxa), IQ-TREE v3.1.2 (final ≤2,000 taxa), MAFFT, trimAl, ete4 | — |
| Orthology / pangenome | OrthoFinder v3, ProteinOrtho v6 (large pangenomes), MMseqs2 | MMseqs2-GPU |
| Synteny | MCScanX, ntSynt, SibeliaZ | — |
| Viromics | geNomad v1.12.0, CheckV v1.1.1, VirSorter2, vConTACT3 v3.2.x (prokaryotic-virus taxonomy), GVClass v1.6.0 (Nucleocytoviricota) | — |
| Structure | TM-Vec v1.0.2 (triage), Boltz v2.2.1 (default predictor), ColabFold v1.6.1 + MMseqs2-GPU MSA, ESMFold (pre-screen), Foldseek 10-941cd33 | Boltz, Foldseek `--gpu 1`, ColabFold, ESMFold |
| Statistics / ML | LinkML v1.11.1 schemas, Pydantic v2.13.4 validation/parsing, DuckDB v1.5.3, scikit-learn 1.8.0, XGBoost v3.2.0 | XGBoost `device=cuda`, RAPIDS cuML |

## Maintenance Notes

- Pin container tags or database versions in run records when they affect interpretation.
- Record database names and dates for taxonomy, annotation, and literature searches.
- Treat GPU paths as alternatives, not automatic upgrades. They need matching hardware and the same scientific validation as CPU paths.
- If a newer tool becomes the default in a skill, update the skill, this page, and any routing benchmark that depends on the workflow.
