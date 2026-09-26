# Good enough practices (Wilson 2017)

Derived from Wilson G, Bryan J, Cranston K, Kitzes J, Nederbragt L, Teal TK, "Good enough practices in scientific computing" (PLOS Comput Biol 2017, doi:10.1371/journal.pcbi.1005510). Condensed into its six areas with bioinformatics specifics. Read this for data management, software, collaboration, project organization, change tracking, and manuscript practices. (This is the "good enough" companion to the authors' 2014 "Best Practices for Scientific Computing" — not a "Ten Simple Rules" paper.)

## Contents

1. Data management
2. Software
3. Collaboration
4. Project organization
5. Keeping track of changes
6. Manuscripts

---

## 1. Data management

- **Save the raw data.** Keep an untouched, read-only copy; never edit it in place — all processing happens via scripts on copies. Store demultiplexed FASTQs under `data/raw/` and `chmod -R 444 data/raw/*.fastq.gz`; write trimmed reads to `results/`, never into `data/raw/`.
- **Back up raw data in more than one location.** At least two physically separate places. Raw BAM/FASTQ live on HPC scratch, are rsynced nightly to institutional object storage, and the run is archived at SRA/ENA: `rsync -av --checksum data/raw/ /backup/seqcenter_run42/`.
- **Create open, readable formats.** Convert proprietary/binary outputs to open, documented, future-proof formats with explicit metadata. Export vendor format to CSV/TSV and bgzipped VCF; store sample metadata as a UTF-8 `sample_metadata.csv`, not a multi-tab `.xlsx`.
- **Create tidy data.** One variable per column, one observation per row. A tidy `samples.tsv` with columns `sample_id, condition, replicate, fastq_r1, fastq_r2` (one row per sample), not a wide spreadsheet with merged cells.
- **Record all processing steps.** Capture every step as scripts/workflows, not GUI edits — a Snakemake/Nextflow pipeline running `fastp -> metaspades -> bwa-mem -> metabat2`.
- **Anticipate multiple tables; use a unique identifier for every record.** Give every record a stable key. Use a canonical `sample_id` (e.g. `BIOSAMPLE_0001`) shared by `samples.tsv`, `qc_metrics.tsv`, and `bin_stats.tsv`; pair gene tables on stable Ensembl gene IDs, not display names.
- **Submit data to a DOI-issuing repository.** Reads at SRA/ENA, MAGs at GenBank, processed count matrix/derived tables to Zenodo for a citable DOI.

## 2. Software

- **Place a brief explanatory comment at the start of every program** stating purpose, inputs, outputs. Top of `src/parse_checkm.py`: `"""Parse CheckM quality from a bin set. In: checkm_qa.tsv. Out: bin_quality.tsv."""`.
- **Decompose programs into functions** (rule of thumb: fit on one screen, few arguments). Split a pipeline into `parse_fasta()`, `filter_by_length()`, `compute_gc()`, `write_table()` rather than one 300-line loop.
- **Be ruthless about eliminating duplication.** Factor a repeated `gzip -dc | grep -c '^>'` into a `count_seqs()` helper imported by both the QC and report scripts.
- **Always search for well-maintained libraries** before re-implementing. Parse alignments with `pysam` and sequences with Biopython rather than writing a homemade SAM/FASTQ parser.
- **Test libraries before relying on them.** Run a new aligner on a small simulated read set with known truth positions and check the mapped coordinates before using it on real samples.
- **Give functions and variables meaningful names.** `min_mapping_quality = 30` and `filter_low_qual_reads(reads)`, not `q=30` and `f(r)`.
- **Make dependencies and requirements explicit** in a machine-readable manifest. Pin tools in `pixi.toml` and commit `pixi.lock` (`bwa=0.7.18`, `samtools=1.21`, `snakemake=8.*`), committed with the code.
- **Do not comment/uncomment sections to control behavior.** Drive behavior with config/CLI args (`--ref contigs.fasta --min-qual 30`), not by toggling commented `#ref = 'old.fa'` lines.
- **Provide a simple example or test data set.** Ship `tests/data/tiny.fastq` (a few hundred reads) and `tests/expected/tiny_bins/` so `make test` runs the pipeline end-to-end and diffs output.
- **Submit code to a DOI-issuing repository.** Connect the GitHub repo to Zenodo and tag a release (`v1.0.0`) to mint a DOI for the exact pipeline version used.

## 3. Collaboration

- **Create a README** in every project: one-paragraph study description, setup (`pixi install`), how to reproduce (`snakemake --cores 8`), and a map of `data/`, `src/`, `results/`.
- **Create a shared to-do list.** GitHub Issues (or a tracked `doc/todo.txt`) for items like "rerun QC after adapter trim", "add CheckM filtering before dRep".
- **Decide on communication strategies.** Document in `CONTRIBUTING.md` where analysis decisions go (`doc/notebook.md`) and where discussion happens.
- **Make the license explicit.** Commit a `LICENSE` (e.g. MIT for the pipeline) and note data terms (e.g. CC-BY) in the README.
- **Make the project citable.** Add `CITATION.cff` listing authors, title, version, and the Zenodo DOI.

## 4. Project organization

One self-contained directory per project, named meaningfully. The directories below mirror the Noble 2009 layout (see `references/project-layout.md`).

- **Put each project in its own directory, named after the project** — `arctic_metagenome_2026/`, not files scattered across `~/Desktop`.
- **Put text documents in `doc/`** — `doc/notebook.md`, `doc/manuscript.md`, `doc/changelog.txt`.
- **Put raw data + metadata in `data/`, generated files in `results/`.** `data/raw/*.fastq.gz` and `data/samples.tsv` stay fixed; `results/qc/`, `results/aligned/*.bam`, `results/bins/` are regenerable. Cleaned/generated files belong in `results/`, never in `data/`.
- **Put your own source code in `src/`** — `src/parse_checkm.py`, `src/plot_bin_sizes.py`.
- **Put external scripts or compiled programs in `bin/`** — a downloaded helper like `fastqc` or a compiled C tool, separate from your own source.
- **Name files to reflect content or function**, sortable and machine-friendly (ordering prefixes help) — `results/2026-03-30_stationA.sorted.bam`, `src/01_trim.smk`, `src/02_assemble.smk`, not `final2.bam` or `script.py`.

## 5. Keeping track of changes

Two acceptable tiers: a manual/low-tech workflow and a version-control workflow.

Common to both:

- **Back up (almost) everything created by a human as soon as it is created.** Commit/track code, notes, configs, sample sheets immediately; large regenerable outputs (multi-GB BAMs/FASTQs) can be excluded.
- **Keep changes small** and logically coherent — "add adapter-trimming rule" separate from "raise MetaBAT2 min-contig length".
- **Share changes frequently** so collaborators stay in sync and divergence stays small.
- **Maintain and use a checklist for saving/sharing changes** — e.g. rerun `snakemake -n` dry run, update `doc/changelog.txt`, commit code, tag if results changed, push.

Manual tier (no version control): mirror the project folder off the working machine (synced cloud folder), log edits in `doc/changelog.txt`, and copy the whole project at milestones — `arctic_metagenome_2026_2026-04-01_assembly_v2/`.

Version-control tier (preferred): `git init`, commit code + configs, tag periodic snapshots/releases (`git tag v1.0.0` for the version that generated the paper's figures).

## 6. Manuscripts

Two acceptable approaches; both keep prose tied to the numbers the analysis produced.

- **Rich online tools** for broad collaboration — co-author in Google Docs / Overleaf with a Zotero library, tracked edits and comments for wet-lab and dry-lab co-authors.
- **Plain text under version control** — keep `doc/manuscript.md` in Git with figures/numbers pulled from `results/` (an R Markdown / Quarto doc that knits the recovered-MAG count straight from `results/bin_sizes_data.tsv`).
