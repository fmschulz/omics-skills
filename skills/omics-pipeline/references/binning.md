# Binning and bin QC

**Last verified:** 2026-11-11
**Tool version/release checked:** CheckM2 v1.1.0 (`predict --help`); CoverM v0.8.0 (run); EukCC 2.2.0 (git tag v.2.2.0; `folder --help`; the change from 2.1.3 is a docs update and a test); GUNC v1.1.1 (`run --help`); MetaBAT2 v2.18 (run); QuickBin/BBTools v39.85 container tag (run; also run on tag 40.05, newest GitHub release v40.01); SemiBin2 v2.6.0 (`single_easy_bin --help`)
**Official docs/manual:** https://bbmap.org/tools/quickbin ; https://github.com/chklovski/CheckM2 ; https://eukcc.readthedocs.io/en/latest/ ; https://grp-bork.embl-community.io/gunc/ ; https://github.com/wwood/CoverM ; https://github.com/BigDataBiology/SemiBin ; https://bitbucket.org/berkeleylab/metabat
**Release/source:** https://hub.docker.com/r/bryce911/bbtools/tags ; https://github.com/bbushnell/BBTools ; https://github.com/chklovski/CheckM2/releases/tag/1.1.0 ; https://github.com/EBI-Metagenomics/EukCC ; https://github.com/grp-bork/gunc/releases/tag/v1.1.1 ; https://github.com/wwood/CoverM/releases/tag/v0.8.0 ; https://github.com/BigDataBiology/SemiBin/releases/tag/v2.6.0

Read the shared rules in [../SKILL.md](../SKILL.md) first. They cover domain routing, hypotheses, failures, environment, threads and the scheduler.

## Use when

Bin metagenomic contigs and score bin completeness, contamination and chimerism. Inputs: `contigs.fasta`, sorted BAMs of each sample's reads on that assembly (mapping is in the reads QC and mapping stage), and `results/taxonomy/domain_routing.tsv`. `BIO_DB_ROOT` holds the QC reference databases. QuickBin needs Docker or Apptainer. Run it from the container ([quickbin.md](quickbin.md)).

## Tool choice

| Case | Default | Alternative |
| --- | --- | --- |
| Bin short-read or long-read assemblies | QuickBin, `bryce911/bbtools:39.85`: the default for speed and a fixed time budget | SemiBin2 (CUDA GPU node) or COMEBin when accuracy matters most; MetaBAT2 is the fastest binner; use it to reproduce a prior pipeline |
| Per-contig depth | CoverM `contig` | `jgi_summarize_bam_contig_depths` for MetaBAT2 |
| Bacterial and archaeal bin QC | CheckM2, plus GUNC for chimerism | none |
| Eukaryotic bin QC | EukCC | none |
| Bin taxonomy | GTDB-Tk for prokaryotes (release recorded); EukCC `ncbi_lng` for eukaryotes | none |
| Viral or virus-like bins | Leave MAG QC; send to the viromics stage | none |

## Rules a model would not guess

- QuickBin is the default as a trade-off between speed and accuracy. Its only published evaluation is its authors' own (Bushnell and Villada (2026) *Communications Biology* https://doi.org/10.1038/s42003-026-10782-z). Independent benchmarks rank SemiBin2 and COMEBin best and MetaBAT2 and GenomeFace fastest (Yazhini et al. (2025) *Briefings in Bioinformatics* https://doi.org/10.1093/bib/bbaf617), and find the neural-network binners COMEBin, SemiBin2 and multi-sample VAMB ahead of MetaBAT2 at a higher compute cost (Kim et al. (2026) *Nature Communications* https://doi.org/10.1038/s41467-026-71521-w). Neither benchmark includes QuickBin. Use SemiBin2 or COMEBin when accuracy matters most.
- Run the QuickClade `percontig` screen on the bin directory and on the source assembly before any CheckM2, EukCC or GTDB-Tk decision.
- Routes are `prokaryote`, `eukaryote`, `prokaryotic_virus`, `giant_virus`, `manual_review`. The routing table has one row per contig (`query_id` is the contig name). To route a bin, join its contigs to the bin (the headers of the bin FASTA) and group by `(sample_id, bin)`. If all contigs share a route, the bin takes it. If they differ, the bin is `manual_review` with `review_flag` true. Inspect the per-contig assignments before scoring such a bin.
- Bin names must be unique within a sample, and a contig belongs to one bin.
- `checkm2 predict -x` defaults to `.fna`: pass `-x .fa` for bins named `.fa`. CheckM2 v1.1.0 breaks older installs. Update the pinned environment and fetch the DIAMOND v3 database (Zenodo DOI 10.5281/zenodo.14897628). Do not compare with v1.0.x runs.
- EukCC database `eukcc2_db_ver_1.2` is the one these commands use. The FTP directory also holds `eukcc2_db_ver_2026_11.tar.gz` (6.2 GB, dated 2026-11-09), which the EukCC docs and release notes do not mention yet and which was not tested.
- EukCC folder mode writes `eukcc.tsv` for good bins. Its first column is `bin` (`fasta` in single mode). Bins with a marker set supported by under half of the alignments go to `bad_quality.csv`, which is tab-separated despite the name. Those bins still need a row in `bin_metrics.tsv`.
- `eukcc folder` reads only files that end in `--suffix` (default `.fa`). Bins named `.fna` or `.fasta` are skipped without an error, so pass the suffix of your bin files.
- EukCC keeps the FASTA suffix in bin names. The other tools drop it. Strip `.fasta`, `.fna` and `.fa` before you join tables.
- EukCC taxonomy is `ncbi_lng`: NCBI taxon IDs joined by `-`, or `NA`.
- GUNC runs on prokaryotic bins only, never on eukaryotic ones. It needs v1.1.0 or later for the `progenomes_3` and `gtdb_214` databases. Record which database gave the scores. `gunc run` reads `.fa` files from `--input_dir`. Set `--file_suffix` for other suffixes.
- GTDB-Tk writes separate `bac120` and `ar53` summaries. Concatenate them under one header line.
- CoverM: use `-m metabat` when the depth table feeds MetaBAT2 (MetaBAT2 2.18 read the table CoverM 0.8.0 wrote). Use `-m mean variance` otherwise. CoverM 0.8.0 adds `--min-mapq`, a `makedb` mode, more mappers and fasta.gz input; both `contig` modes ran unchanged.
- QuickBin: pin the container tag and record the image digest when you pull it. Use a local BBTools install only when no container runtime exists, and record its version and path. Use `xstrict` with several samples (3 to 10 are best) and `strict` with one. Contigs under 2500 bp do not seed bins.
- SemiBin2: `--sequencing-type long_read` for long-read assemblies. Use `--environment global` when no pre-trained model fits. `-p` defaults to 0, which means all CPUs: set it. Bins land in `semibin/output_bins/`. SemiBin2 2.6.0 needs Python 3.11, Pandas 3 and PyTorch 2.4 or newer.

## Commands

The CoverM, QuickBin and MetaBAT2 lines ran on 2026-11-11 on a mock community of four genomes (two BAM files from bwa-mem2). The CheckM2, GUNC, EukCC and SemiBin2 lines were checked against `--help` of the versions above in their bioconda containers; they were not run because their databases or GPU are not part of a smoke test.

```bash
# Depth per contig (sorted BAMs, same reference as the contigs)
coverm contig --bam-files $BAMS -m mean variance -t $THREADS -o $OUT/coverage.tsv
# For MetaBAT2 input use: -m metabat

# Bin with QuickBin (default); $OUT is relative to $PWD
mkdir -p $OUT/bins
docker run --rm -u "$(id -u):$(id -g)" -v "$PWD":/work -w /work \
  bryce911/bbtools:39.85 \
  quickbin.sh in=$CONTIGS out=$OUT/bins/bin%.fa \
    reads=s1.bam,s2.bam,s3.bam threads=$THREADS xstrict covout=$OUT/bins/coverage.txt

# GPU alternative
SemiBin2 single_easy_bin -i $CONTIGS -b $BAM --environment global -o $OUT/semibin -p $THREADS

# Prokaryotic bins (directory built from the routing table; do not move the originals)
checkm2 predict --input $PROK_BINS -x .fa --output-directory $OUT/checkm2 -t $THREADS
gunc download_db gunc_db/ -db progenomes_3
GUNC_DB=$(find gunc_db -name '*.dmnd' | head -n 1)
gunc run --input_dir $PROK_BINS --file_suffix .fa --db_file "$GUNC_DB" \
  --out_dir $OUT/gunc --threads $THREADS --detailed_output

# Eukaryotic bins
wget http://ftp.ebi.ac.uk/pub/databases/metagenomics/eukcc/eukcc2_db_ver_1.2.tar.gz
tar -xzvf eukcc2_db_ver_1.2.tar.gz && export EUKCC2_DB=$(realpath eukcc2_db_ver_1.2)
eukcc folder $EUK_BINS --out $OUT/eukcc --db $EUKCC2_DB --threads $THREADS --suffix .fa
```

GTDB-Tk setup and the reference package follow the taxonomy tracking skill named in the stage table of [../SKILL.md](../SKILL.md).

## QC gates to record

- Completeness, contamination and GUNC chimerism, against thresholds you set for the project (MIMAG is one example). An unmet threshold is a result.
- `contigs.fasta` and the depth table are non-empty. The QC databases exist under `BIO_DB_ROOT`.
- The `percontig` screen exists for the assembly and the bin set before any QC decision.
- Each prokaryotic bin has GTDB-Tk taxonomy, with the database release recorded.
- Viral and virus-like bins go to the viromics stage. Mixed-domain bins are flagged with per-contig evidence.
- `bin_metrics.tsv` covers every routed bin, including viral and `manual_review` rows. `gtdbtk_taxonomy.tsv` covers every prokaryotic bin.

## Outputs

The agent writes these tables from the native tool outputs. A restartable project driver follows the `bioinformatics-project` skill. All files sit under `<run>/binning/`, where `<run>` is the dated run directory `results/<date>_<name>/` that `bioinformatics-project` defines.

- `bins/`: QuickBin or SemiBin2 output.
- `bin_metrics.tsv`: one row per routed bin. Columns: `bin_id`, `domain_route`, `completeness`, `contamination`, `qc_tool`, `gunc_pass`, `gunc_css`, `taxonomy`, `taxonomy_tool`, `review_flag`. Sources: CheckM2 `Name`, `Completeness`, `Contamination`; GUNC `genome`, `clade_separation_score`, `pass.GUNC`; EukCC `bin`, `completeness`, `contamination`, `ncbi_lng`; GTDB-Tk `user_genome`, `classification`.
- `gtdbtk_taxonomy.tsv`: one row per prokaryotic bin. Columns: `bin_id`, `classification`, `tool`.
- `bin_qc_report.json`: routed bins, prokaryotic bins, eukaryotic bins, and viral or review bins.
- `logs/`.
