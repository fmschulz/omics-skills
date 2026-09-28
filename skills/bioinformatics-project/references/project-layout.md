# Project layout (Noble 2009, adapted)

Derived from Noble WS, "A Quick Guide to Organizing Computational Biology Projects" (PLOS Comput Biol 2009, doi:10.1371/journal.pcbi.1000424), adapted to modern bioinformatics. Read this when laying out a new project or auditing an existing one.

## Contents

- Two governing principles
- Top-level structure
- Organization philosophy (logical / chronological / logical)
- Dated experiment directories
- The lab notebook
- Script categories
- Data provenance

## Two governing principles

1. **A stranger can understand what you did and why.** Anyone unfamiliar with the project should be able to open the directories and reconstruct, in detail, what was done and why — with no verbal explanation. A reviewer opening `results/2024-03-12_blastp_screen/` sees `runall`, a `README`, an input symlink to `data/refseq_v220.faa`, and the `lab_notebook.md` entry explaining the e-value cutoff, and can reconstruct the whole analysis unaided.
2. **You will redo everything.** Assume every analysis will be rerun with new data, new parameters, or a fixed bug. Build each experiment to re-execute end-to-end from a script. When assembly `GCA_000001405.29` replaces `.28`, you rerun the entire annotation pipeline by editing one `ASSEMBLY=...` line at the top of `runall` and typing `./runall`, instead of retyping 40 prodigal/hmmsearch commands.

## Top-level structure

Place the whole project under one root with fixed subdirectories:

```
metagenome_mags_project/
├── tasks/     # METHODS.md (committed); todo, lessons, hypotheses (local)
├── data/      # fixed datasets + metadata; treat as read-only inputs
├── results/   # computational experiments (regenerable outputs)
├── doc/       # manuscripts, notes, changelog — one subdir per manuscript
├── src/       # your own source code (analysis modules, helpers)
└── bin/       # compiled binaries and third-party / wrapper scripts
```

- `data/` holds raw FASTQs and sample metadata. Treat it as read-only; cleaned and generated files go in `results/`, never back into `data/`.
- `results/` holds dated experiment dirs (e.g. MAG-binning runs) plus `lab_notebook.md` at its root.
- `doc/` gives each paper its own subdirectory — `doc/2025_giant_virus_paper/` and `doc/2025_methods_note/` each with their own `manuscript.tex`, `figures/`, `references.bib` — rather than mixing drafts.
- `src/` holds the project's own importable, tested analysis code (e.g. a Python dereplication module).
- `bin/` holds project-wide executables: third-party / compiled tools (e.g. `checkm`) plus your own standalone wrapper or utility scripts that are run directly and reused across several experiments (e.g. `filter_contigs.py`).

## Annotated full tree

```
metagenome_mags_project/
├── README.md                       # study description, setup, how to reproduce
├── LICENSE                         # explicit reuse terms
├── CITATION.cff                    # how to cite the project
├── pixi.toml                       # pinned tool stack (conda-forge + bioconda)
├── pixi.lock                       # exact resolved versions (committed)
├── .gitignore                      # excludes data blobs + all results/ outputs
│
├── tasks/
│   ├── todo.md                     # active outcomes and their proof
│   ├── METHODS.md                  # exact commands, versions, parameters, seeds
│   ├── lessons.md                  # corrections and prevention rules
│   └── hypotheses.md               # active and retired exploratory hypotheses
│
├── data/
│   ├── README.md                   # provenance for every dataset
│   ├── raw/                        # immutable; chmod 444; never edited
│   │   ├── sampleA_R1.fastq.gz
│   │   └── sampleA_R2.fastq.gz
│   ├── refseq_v220/                # downloaded reference DB + its own README
│   │   └── README.txt              # source URL, version, download date, md5
│   └── samples.tsv                 # tidy sample sheet (key: sample_id)
│
├── results/
│   ├── lab_notebook.md             # dated decision log at the root of results/
│   ├── 2024-03-12_blastp_screen/
│   │   ├── runall                  # driver: reproduces this experiment alone
│   │   ├── README.md               # what / why for this experiment
│   │   ├── reformat_one_off.awk    # single-use script, kept beside its driver
│   │   ├── provenance.txt          # tool versions + seed, written by runall
│   │   ├── logs/
│   │   ├── hits.tsv                # generated output (gitignored)
│   │   └── figures/
│   │       ├── hits_histogram.png
│   │       └── hits_histogram_data.tsv   # raw data behind the plot
│   └── 2024-06-01_phylo/
│       ├── runall
│       ├── summarize.py            # reads partial experiment, emits summary.html
│       ├── alignments/             # logical structure below the date
│       ├── trees/
│       └── logs/
│
├── doc/
│   ├── 2025_giant_virus_paper/
│   │   ├── manuscript.qmd          # literate doc: numbers pulled from results/
│   │   ├── figures/
│   │   └── references.bib
│   └── changelog.md
│
├── src/
│   ├── parse_hits.py               # project source code; prints a usage statement
│   └── dereplicate.py
│
└── bin/
    ├── filter_contigs.py           # project-specific, reused across experiments
    └── checkm                      # compiled third-party tool
```

## Organization philosophy

Use **logical** (named-by-purpose) organization at the project root, **chronological** (date-named) organization at the experiment level, and **logical** organization again inside each experiment:

```
results/                                    # logical
└── 2024-06-01_phylo/                        # chronological
    ├── alignments/                          # logical (below the date)
    ├── trees/
    └── logs/
```

Let the driver script create this below-the-date structure automatically rather than building it by hand: `runall` starts with `for d in alignments trees logs; do [ -d "$d" ] || mkdir -p "$d"; done` before running `mafft` and `iqtree`.

## Dated experiment directories

Name each experiment dir under `data/` and `results/` with an ISO date `YYYY-MM-DD`, optionally plus a topic word, so they sort in time order and you never rename as the project's logical structure shifts. Use `results/2024-03-12_blastp_screen/`, not `results/final/` or `results/blast_v2_really_final/`.

## The lab notebook

Maintain a single chronologically organized, dated lab-notebook document at the root of `results/` (`results/lab_notebook.md`). Record observations, conclusions, ideas for future work, and the reasoning behind each experiment.

- **Explain decisions.** `## 2024-03-12 BLASTp screen — used e-value 1e-5 because 1e-3 gave too many short spurious hits; see results/2024-03-12_blastp_screen/figures/hits_histogram.png`.
- **Record how you knew an experiment failed.** `2024-04-02 SPAdes assembly FAILED — N50 dropped to 412 bp and BUSCO completeness 6%; cause was adapter contamination not removed; rerun after fastp.` Documenting the evidence prevents repeating dead ends.
- **Link evidence without copying private correspondence.** Link images and tables, record the approved scientific decision and rationale, and reference a durable project decision record. Do not paste private email, credentials, or personal data into the repository.

A dated entry template: `examples/lab-notebook-entry.md`.

## Script categories

Place each script according to its scope of reuse:

| Category | Where it lives | Example |
|---|---|---|
| Driver script (one or two per dir) | the experiment dir | `results/2024-03-12_blastp_screen/runall` — the only file you execute to reproduce that experiment |
| Single-use script | beside its driver | `results/2024-03-12_blastp_screen/reformat_one_off.awk` — no value outside this experiment |
| Project-specific script | one level below the root (`bin/`) | `bin/filter_contigs.py` — reused by several dated assembly experiments, called as `../../bin/filter_contigs.py` |
| Multi-project script | a separate, separately-versioned repo | `~/tools/genomics/make_roc_curve.py` — generic, reused across every project |

## Data provenance

For data pulled from central repositories, record the source URL, version number, and download date so the dataset can be re-obtained and cited exactly. `data/refseq_v220/README.txt`: "Downloaded RefSeq non-redundant protein DB v220 from https://ftp.ncbi.nlm.nih.gov/blast/db/ on 2024-03-10; md5 a1b2c3...".
