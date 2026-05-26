# Tooling Survey 2026

This page records the default tool choices referenced by the agents and bioinformatics skills. It is a practical baseline, not a claim that every workflow should use the same tool. Agents should still choose methods from the biological question, input data, available hardware, and the literature for the inferred organism or virus group.

| Step | CPU baseline | GPU or accelerated option |
|---|---|---|
| Long-read QC | Dorado summaries/trimming, Chopper, Filtlong, Pychopper for full-length cDNA; Porechop_ABI only as a documented fallback | None documented |
| Short-read mapping | `bwa-mem2`, BBMap | NVIDIA Parabricks `fq2bam` |
| Long-read mapping | `minimap2` v2.30 | `mm2-fast`, `mm2-gb`, `mm2-ax` when the hardware fits |
| Assembly | SPAdes 4, Flye 2.9 for long-read isolate drafts, Autocycler 0.6+ for bacterial isolate consensus, Flye `--meta` / metaFlye for long-read metagenomes, metaMDBG 1.1, myloasm where appropriate | None documented |
| Domain taxonomy triage | BBTools QuickClade via `bryce911/bbtools`, followed by GTDB-Tk, EukCC, vConTACT3, or GVClass by domain | None documented |
| Binning | QuickBin via `bryce911/bbtools` | SemiBin2 with CUDA-backed PyTorch |
| Bin QC | CheckM2, EukCC, GUNC | None documented |
| Gene calling | pyrodigal, pyrodigal-gv, BRAKER3 | None documented |
| ncRNA screening | tRNAscan-SE, Infernal `cmsearch` against Rfam covariance models | None documented |
| Annotation | DIAMOND, eggNOG-mapper, InterProScan, pyhmmer, TaxonKit | MMseqs2-GPU |
| Phylogenomics | VeryFastTree, IQ-TREE, MAFFT, trimAl, ete4 | None documented |
| Orthology and pangenomes | OrthoFinder, ProteinOrtho, MMseqs2 | MMseqs2-GPU |
| Synteny | MCScanX, ntSynt, SibeliaZ | None documented |
| Viromics | geNomad, CheckV, VirSorter2, vConTACT3, GVClass | None documented |
| Structure annotation | TM-Vec, Boltz-2, ColabFold, ESMFold, Foldseek | Boltz-2, Foldseek GPU, ColabFold, ESMFold |
| Statistics and ML | LinkML schemas, Pydantic validation/parsing, DuckDB, scikit-learn, XGBoost | XGBoost CUDA, RAPIDS cuML |

## Maintenance Notes

- Pin container tags or database versions in run records when they affect interpretation.
- Record database names and dates for taxonomy, annotation, and literature searches.
- Treat GPU paths as alternatives, not automatic upgrades. They need matching hardware and the same scientific validation as CPU paths.
- If a newer tool becomes the default in a skill, update the skill, this page, and any routing benchmark that depends on the workflow.
