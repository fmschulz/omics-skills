# Pinned flags: CoverM, SemiBin2, MetaBAT2, GUNC

Pinned flags for the tools that need no full guide. Add all four with `pixi add coverm semibin metabat2 gunc`; the lock file records the build.

Last verified: 2026-05-30
Tool version/release checked: CoverM v0.7.0; SemiBin2 2.3.0; MetaBAT2 v2.18; GUNC v1.1.1
Official docs/manual: https://github.com/wwood/CoverM ; https://github.com/BigDataBiology/SemiBin ; https://bitbucket.org/berkeleylab/metabat ; https://grp-bork.embl-community.io/gunc/
Release/source: https://github.com/wwood/CoverM/releases/tag/v0.7.0 ; https://github.com/BigDataBiology/SemiBin/blob/main/SemiBin/semibin_version.py ; https://bitbucket.org/berkeleylab/metabat/src/v2.18/ ; https://github.com/grp-bork/gunc/releases/tag/v1.1.1

## CoverM

Per-contig depth for binning, from sorted BAMs (BAMs must be sorted and aligned to the same reference as the contigs):

```bash
coverm contig --bam-files sample1.sorted.bam sample2.sorted.bam -m mean variance -t 8 -o contig_coverage.tsv
coverm make --coupled reads_1.fq.gz reads_2.fq.gz --reference contigs.fasta -o alignments/ -t 16
```

Genome-level abundance uses `coverm genome` with `--genome-fasta-files`. Methods: `mean`, `variance`, `trimmed_mean`, `covered_fraction`, `covered_bases`, `relative_abundance`, `rpkm`, `tpm`. Run `coverm filter` to drop low-identity alignments first.

## SemiBin2 (GPU alternative to QuickBin)

```bash
pixi add semibin pytorch-gpu cuda
SemiBin2 single_easy_bin -i contigs.fasta -b reads.sorted.bam --environment global -o semibin/ -p 16
```

- `--sequencing-type long_read` for long-read assemblies; default is `short_read`.
- `--environment` picks a pre-trained model: `human_gut`, `dog_gut`, `cat_gut`, `mouse_gut`, `pig_gut`, `chicken_caecum`, `human_oral`, `ocean`, `soil`, `built_environment`, `wastewater`, or `global` (diverse fallback). Without a matching model, use `global`, or `--self-supervised` in multi-sample mode.
- Multi-sample mode: `SemiBin2 multi_easy_bin` with a combined FASTA whose contig names read `sample:contig` (`-s` changes the separator) and one sorted BAM per sample. Three or more samples bin better.
- `--minfasta-kbs` sets the minimum bin size in kb (default 1). Final bins are in `semibin/output_bins/`.

## MetaBAT2 (reproduce prior pipelines only)

```bash
jgi_summarize_bam_contig_depths --outputDepth depth.txt *.bam
metabat2 -i contigs.fasta -a depth.txt -o bins/bin --seed 12345 --unbinned --saveCls -t 16
```

- Defaults: `-m` 2500 bp minimum contig, `-s` 200000 bp minimum bin, `--maxP` 95, `--minS` 60. `-t 0` uses every core, so always pass `-t`.
- Less contamination: `--noAdd`, higher `--minS`. Higher completeness: higher `--maxEdges` (up to 500), lower `-m`.
- Bins are written as `bin.<n>.fa`. The depth table is the `jgi_summarize_bam_contig_depths` format; `coverm contig -m metabat` reproduces that output (CoverM README).

## GUNC (prokaryotic bins only)

```bash
gunc download_db gunc_db/ -db progenomes_3      # ~7 GB; gtdb_214 is ~30 GB and covers more references
GUNC_DB=$(find gunc_db -name '*.dmnd' | head -n 1)
gunc run --input_dir bins/ --file_suffix .fa --db_file "$GUNC_DB" --out_dir gunc_output/ --threads 16 --detailed_output
```

- Record which database produced the scores. `--sensitive` is slower and more accurate; `--detailed_output` adds per-contig assignments for refinement.
- The result table is `GUNC.<db>.maxCSS_level.tsv`. A bin is flagged chimeric when `clade_separation_score` (CSS) is above 0.45 and `contamination_portion` is above 0.05; `pass.GUNC` carries the verdict. CSS above 0.85 is highly chimeric; 0.30 to 0.45 is borderline, so review it by hand.
- Bins under about 100 kb give unreliable results. A high CSS with low CheckM2 contamination points to a chimeric bin from related taxa, which CheckM2 misses.
- Memory is 8 to 16 GB for typical runs; use the ProGenomes database when memory is tight.
