# Tool cheat sheets (QuickClade, GTDB-Tk, EukCC, vConTACT3, TaxonKit)

This file focuses on **operational usage** and **provenance capture**.

If the user asks “what’s the best tool?”, prefer **domain-appropriate** tools and then cross-check with NCBI taxids for interoperability.

---

## QuickClade (BBTools / BBMap suite) — fast k-mer taxonomy screen

Authoritative docs:
- https://bbmap.org/tools/quickclade
- BBMap/BBTools home (find QuickClade under Tools):
  https://bbmap.org/

### What it does
- Compares k-mer frequency “spectra” between query sequences and a reference.
- Very fast; good for **first-pass** taxonomy screening for bins/contigs.
- Not a marker-gene phylogeny method; validate when stakes are high.

### Preferred execution (container)
Run QuickClade via the official BBTools container image:

- Container image: `bryce911/bbtools:39.65` (tagged per BBTools release)
- Docker Hub page:
  https://hub.docker.com/r/bryce911/bbtools/

#### Docker examples
Run on a FASTA in the current directory:
```bash
docker run --rm -u "$(id -u):$(id -g)"   -v "$PWD":/work -w /work   bryce911/bbtools:39.65   quickclade.sh contigs.fa percontig out=results.tsv usetree
```

Run on a directory of bins:
```bash
docker run --rm -u "$(id -u):$(id -g)"   -v "$PWD":/work -w /work   bryce911/bbtools:39.65   quickclade.sh bins/ out=quickclade_bins.tsv usetree
```

#### Apptainer / Singularity examples
Pull + run directly from Docker Hub:
```bash
apptainer exec --bind "$PWD":/work --pwd /work   docker://bryce911/bbtools:39.65   quickclade.sh contigs.fa percontig out=results.tsv usetree
```

### Reference spectra (important)
The QuickClade docs show a default reference path that may not exist on your system/container.
Best practice:
- always pass `ref=<spectra.gz>` explicitly, and record which reference you used
- build your own spectra from a reference FASTA using `cladeloader.sh` (BBTools)

---

## GTDB-Tk — prokaryote genome taxonomy (Bacteria/Archaea)

Docs:
- https://ecogenomics.github.io/GTDBTk/

### When to use
- Genome-based taxonomy for MAGs/SAGs/isolate genomes.
- Outputs GTDB taxonomy strings like: `d__Bacteria;p__...;...;s__...`

### Install/run (recommended)
Use **Pixi** for reproducible dependency management (see env/README.md in this Skill).
Always record:
- GTDB-Tk version
- GTDB reference package release ID/date

Note: GTDB-Tk has heavy reference data requirements; plan disk and RAM accordingly.

---

## EukCC — eukaryotic MAG/genome QC + taxonomy context

Docs:
- https://eukcc.readthedocs.io/

### When to use
- Eukaryotic MAGs/genomes where bacterial QC tools are inappropriate.
- Provides completeness/contamination estimates and a taxonomy lineage.

### Install/run (recommended)
Use **Pixi** (see env/README.md) and capture:
- EukCC version
- database location/version (`EUKCC2_DB` or `--db`)

---

## vConTACT3 — viral clustering to support taxonomy inference

Docs:
- https://vcontact3.readthedocs.io/

### When to use
- Viral contigs/genomes: protein-sharing network clustering supports taxonomy inference.
- Not a replacement for ICTV; interpret results in ICTV context and with hallmark genes/phylogeny.

### Install/run (recommended)
Use **Pixi** (see env/README.md) and capture:
- vConTACT3 version
- database/reference used (if any)
- parameterization (e.g., thresholds, export options)

---

## TaxonKit — NCBI taxonomy toolkit for taxids and lineages

Docs:
- https://bioinf.shenwei.me/taxonkit/usage/
- https://github.com/shenwei356/taxonkit

### When to use
- Enrich results with NCBI taxids, ranks, and complete lineages.
- Detect merged/deleted taxids and avoid brittle name-joins.

### Key commands
Taxid → lineage:
```bash
taxonkit lineage taxids.txt
```

Name → taxid:
```bash
taxonkit name2taxid names.txt
```

Lineage reformat:
```bash
taxonkit lineage taxids.txt | taxonkit reformat -f "{d};{k};{p};{c};{o};{f};{g};{s}"
```

### Data requirement
TaxonKit needs the NCBI taxdump on disk; record which dump/snapshot date you used.
