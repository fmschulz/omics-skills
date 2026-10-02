# Reproducibility checklist (Sandve 2013)

Derived from Sandve GK, Nekrutenko A, Taylor J, Hovig E, "Ten Simple Rules for Reproducible Computational Research" (PLOS Comput Biol 2013, doi:10.1371/journal.pcbi.1003285). Each rule below is operationalized as an actionable check plus a concrete bioinformatics how-to. Read this when making an analysis reproducible.

## Contents

1. Track how every result was produced
2. Avoid manual data manipulation
3. Archive exact versions of external programs
4. Version-control all custom scripts
5. Record intermediate results in standard formats
6. Note random seeds for stochastic steps
7. Store the raw data behind every plot
8. Generate hierarchical, drill-down output
9. Connect textual statements to underlying results
10. Provide public access to scripts, runs, and results

---

## Rule 1 — For every result, keep track of how it was produced

Record the exact program, version, parameters, and input files for every result, preferably as an executable spec rather than prose.

- [ ] Drive each result through a script or workflow rule (`runall`, Snakemake, Nextflow), not typed by hand.
- [ ] Log the full command, tool version, and inputs to a per-result log file.

How-to: run alignment from a rule so the result is reproducible — `bwa mem -t 8 ref.fa R1.fq.gz R2.fq.gz | samtools sort -o sample.sorted.bam` — with the command, BWA version, and inputs captured in the rule and written to `results/logs/bwa_sample.log` instead of typed at a prompt.

## Rule 2 — Avoid manual data manipulation steps

Script every transformation; if a manual step is truly unavoidable, document it explicitly.

- [ ] No editing of VCFs, count matrices, or tables in a spreadsheet.
- [ ] Sample/column dropping happens in a tracked script, not by copy-pasting cells.

How-to: instead of opening a VCF in Excel to delete failing samples, filter programmatically — `bcftools view -e 'QUAL<30 || INFO/DP<10' in.vcf.gz -Oz -o filtered.vcf.gz` — or drop samples in a tracked `scripts/filter_counts.py`.

## Rule 3 — Archive the exact versions of all external programs used

Pin and archive the exact versions of all third-party tools so a rerun uses the identical software stack; capture full environment images when needed.

- [ ] Toolchain added at its newest release at setup, checked against the skill's commands, and locked: `pixi.lock` committed (it holds the exact builds).
- [ ] Container image built for long-lived analyses.
- [ ] Tool versions recorded into `tasks/METHODS.md` and the experiment's provenance file.

How-to: `pixi add bwa samtools metabat2`, then commit `pixi.lock`; build a Docker/Apptainer image `FROM` that locked env so the MetaBAT2 version that produced the bins is preserved; record `samtools --version` and `metabat2 2>&1 | head`. See `references/environments.md`.

## Rule 4 — Version-control all custom scripts

Keep every custom script and analysis file under Git so the exact code behind any past result can be recovered.

- [ ] `src/`, `runall`, Snakefile, and configs committed to Git.
- [ ] The commit behind each figure is tagged.

How-to: `git tag fig3-coverage`, so `git checkout fig3-coverage` recovers the precise read-counting script that produced that panel.

## Rule 5 — Record all intermediate results, when possible in standardized formats

Persist intermediate outputs in standard formats so you can detect bugs, inspect each stage, and rerun only the affected portion.

- [ ] Each pipeline stage writes a named file in a standard format under the experiment dir.
- [ ] Pipelines are checkpointed, not collapsed into one opaque pipe.

How-to: keep the assembly FASTA, the sorted BAM, its BAI index, and the per-contig depth TSV under `results/.../intermediate/` (FASTA/BAM/BAI/TSV standard formats) rather than streaming everything through a single pipe, so a downstream error can be traced to its stage and re-run from there.

## Rule 6 — For analyses that include randomness, note underlying random seeds

Set and record an explicit seed for any stochastic step so the analysis reproduces bit-for-bit.

- [ ] Every subsample, bootstrap, and clustering step takes an explicit seed.
- [ ] The seed is written into the provenance file / METHODS.md.

How-to: bin contigs with a fixed, logged seed — `metabat2 -i contigs.fasta -a depth.tsv -o bins/bin --seed 42` — and subsample reads with a fixed seed where needed — `samtools view -s 42.1 in.bam -b -o sub10pct.bam` (42 = seed, .1 = 10%) or `seqtk sample -s100 reads.fq.gz 1000000 > sub.fq`. Set seeds for bootstrapping too: `numpy.random.default_rng(42)`, `set.seed(42)` in R.

## Rule 7 — Always store raw data behind plots

Save the underlying values used to draw every plot so figures can be re-rendered and exact numbers inspected without rerunning the analysis.

- [ ] Each figure has a sibling `<plot>_data.tsv`.
- [ ] The plotting script reads that table, not in-memory analysis state.

How-to: before plotting bin sizes, write the source table to `results/figures/bin_sizes_data.tsv` (bin, contigs, total_bp — e.g. from `seqkit stats -T`), then have `plot_bin_sizes.py` read that TSV; the plot can be restyled or audited from the stored values alone.

## Rule 8 — Generate hierarchical analysis output, allowing layers of increasing detail to be inspected

Produce layered output where high-level summaries link down to progressively more detailed results.

- [ ] A top-level summary report exists.
- [ ] It links down to per-sample detail and raw logs.

How-to: emit a MultiQC HTML report summarizing every sample's FastQC/trimming/mapping metrics on the top page, with each metric linking to per-sample detail underneath, so a flagged sample can be traced from the summary down to its individual FastQC output.

## Rule 9 — Connect textual statements to underlying results

Tie every claim or number in the write-up directly to the result file that produced it, ideally via a literate document.

- [ ] Stated numbers are computed inline from result files, not typed.
- [ ] Manuscript / methods are in a code-embedded document.

How-to: write the manuscript or methods as an R Markdown / Quarto / Jupyter document where the stated number of recovered MAGs is computed inline from `results/bin_sizes_data.tsv` (e.g. an inline `nrow(bins)` chunk) so the text value and the data file cannot drift apart.

## Rule 10 — Provide public access to scripts, runs, and results

Make inputs, scripts, exact versions, parameters, and outputs publicly available so others can rerun and verify.

- [ ] Raw reads deposited (SRA / ENA).
- [ ] Analysis repo (Snakefile, `pixi.lock`, `scripts/`, config) public and archived with a DOI.
- [ ] Final results (MAGs, count matrices) uploaded.

How-to: deposit raw reads in SRA/ENA, the MAGs at GenBank, push the analysis repo to a public GitHub release archived with a Zenodo DOI, and upload derived tables so a reader can reconstruct every figure from public inputs.
