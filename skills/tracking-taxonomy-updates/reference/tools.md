# Tool cheat sheets (QuickClade, GTDB-Tk, EukCC, vConTACT3, GVClass, TaxonKit)

Last verified: 2026-05-30
Tool version/release checked: QuickClade / BBTools v39.85 via `bryce911/bbtools:39.85`; GTDB-Tk 2.7.2 / GTDB Release 232; EukCC v.2.1.3; vConTACT3 release notes v3.2.0; GVClass v1.6.0; TaxonKit v0.20.0
Official docs/manual: See table below.
Release/source: See table below.

| Tool/source | Tool version/release checked | Official docs/manual | Release/source |
|---|---|---|---|
| QuickClade / BBTools | BBTools QuickClade docs checked; examples use container tag `39.85` and checked digest `sha256:e697da46d8955a30256cc1c2a9ed8da362ad5a86ed16b6a41ab64ed03801a2a1` | https://bbmap.org/tools/quickclade | https://hub.docker.com/r/bryce911/bbtools/tags |
| GTDB-Tk | GTDB-Tk 2.7.2; GTDB-Tk reference package Release 232 (`gtdbtk_r232_data.tar.gz`) | https://ecogenomics.github.io/GTDBTk/ | https://github.com/Ecogenomics/GTDBTk/releases/tag/2.7.2 |
| EukCC | EukCC v.2.1.3; EukCC2 database docs still show `eukcc2_db_ver_1.1` | https://eukcc.readthedocs.io/ | https://github.com/EBI-Metagenomics/EukCC/releases/tag/v.2.1.3 |
| vConTACT3 | Release notes latest entry v3.2.0 (2026-03-26); ReadTheDocs title still says 3.0.1 | https://vcontact3.readthedocs.io/ | https://bitbucket.org/MAVERICLab/vcontact3 |
| GVClass | GVClass v1.6.0; resource bundle v1.5.0 compatible | https://github.com/NeLLi-team/gvclass | https://github.com/NeLLi-team/gvclass/releases/tag/v1.6.0 |
| TaxonKit | TaxonKit v0.20.0; NCBI taxdump FTP listing checked 2026-05-30 | https://bioinf.shenwei.me/taxonkit/ | https://github.com/shenwei356/taxonkit/releases/tag/v0.20.0 |

This file focuses on **operational usage** and **provenance capture**.

If the user asks “what’s the best tool?”, prefer **domain-appropriate** tools and then cross-check with NCBI taxids for interoperability.

## First-pass routing contract

Run QuickClade first for any assembly, MAG, SAG, isolate genome, bin directory, or unbinned contig FASTA. Use `percontig` for assemblies so mixed-domain contigs are not hidden by a whole-file majority label.

| QuickClade domain signal | Route | Downstream tool |
|---|---|---|
| Bacteria | Prokaryote genome taxonomy | GTDB-Tk |
| Archaea | Prokaryote genome taxonomy | GTDB-Tk |
| Eukaryota | Eukaryotic MAG/genome QC + lineage context | EukCC |
| Viral, virus-like, or phage/prokaryotic virus | Viral analysis | `/bio-viromics` -> vConTACT3 when phage/prokaryotic-virus evidence is supported |
| Nucleocytoviricota, giant virus, NCLDV | Giant-virus analysis | `/bio-viromics` -> GVClass plus marker-gene phylogeny |
| Mixed or low confidence | Review/split | Split contigs or keep as manual-review rows before domain-specific tools |

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
Run QuickClade via the BBTools container image used in the examples below:

- Container image in examples: `bryce911/bbtools:39.85`
- Checked digest on 2026-05-30: `sha256:e697da46d8955a30256cc1c2a9ed8da362ad5a86ed16b6a41ab64ed03801a2a1`
- Record the resolved image digest at run time with `docker image inspect` or the equivalent Apptainer/Singularity metadata.
- Docker Hub page:
  https://hub.docker.com/r/bryce911/bbtools/

#### Docker examples
Run on a FASTA in the current directory:
```bash
mkdir -p results/taxonomy
docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD":/work -w /work \
  bryce911/bbtools:39.85 \
  quickclade.sh contigs.fa percontig ref=references/quickclade.spectra.gz out=results/taxonomy/quickclade_percontig.tsv usetree
```

Run on a directory of bins:
```bash
mkdir -p results/taxonomy
docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD":/work -w /work \
  bryce911/bbtools:39.85 \
  quickclade.sh bins/ percontig ref=references/quickclade.spectra.gz out=results/taxonomy/quickclade_bins_percontig.tsv usetree
```

#### Apptainer / Singularity examples
Pull + run directly from Docker Hub:
```bash
mkdir -p results/taxonomy
apptainer exec --bind "$PWD":/work --pwd /work \
  docker://bryce911/bbtools:39.85 \
  quickclade.sh contigs.fa percontig ref=references/quickclade.spectra.gz out=results/taxonomy/quickclade_percontig.tsv usetree
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
Release checked:
- GTDB-Tk 2.7.2, announced 2026-05-08.
- GTDB-Tk reference package Release 232: `gtdbtk_r232_data.tar.gz`.

### When to use
- Genome-based taxonomy for MAGs/SAGs/isolate genomes.
- Outputs GTDB taxonomy strings like: `d__Bacteria;p__...;...;s__...`

### Install/run (recommended)
Use **Pixi** for reproducible dependency management (see env/README.md in this Skill).
Always record:
- GTDB-Tk version
- GTDB reference package release ID/date

Note: GTDB-Tk has heavy reference data requirements; plan disk and RAM accordingly.

### Database check
Before classification, verify the reference package exists:

```bash
test -n "${GTDBTK_DATA_PATH:-}" && test -d "$GTDBTK_DATA_PATH"
gtdbtk check_install
```

If it is missing, create a project or shared DB location under `$BIO_DB_ROOT`, install the GTDB-Tk reference package using the current GTDB-Tk documentation or site mirror, export `GTDBTK_DATA_PATH`, then rerun `gtdbtk check_install`. Do not classify with a partial or unknown database.

### Classification example
```bash
gtdbtk classify_wf --genome_dir bins --out_dir results/taxonomy/gtdbtk \
  --cpus 16 -x fa
```

GTDB-Tk 2.7.x runs the ANI screen by default using the pre-sketched skani database. If a project requires species that pass the ANI screen to still be placed in pplacer trees, add `--place_species`; this replaces the older `--skip_ani_screen` workflow.

---

## EukCC — eukaryotic MAG/genome QC + taxonomy context

Docs:
- https://eukcc.readthedocs.io/
Release checked:
- EukCC v.2.1.3 (GitHub release).
- EukCC docs still show EukCC2 database `eukcc2_db_ver_1.1`; record the exact database directory or `--db` path used in each run.

### When to use
- Eukaryotic MAGs/genomes where bacterial QC tools are inappropriate.
- Provides completeness/contamination estimates and a taxonomy lineage.

### Install/run (recommended)
Use **Pixi** (see env/README.md) and capture:
- EukCC version
- database location/version (`EUKCC2_DB` or `--db`)

### Run examples
```bash
eukcc single --out results/taxonomy/eukcc_one --threads 8 bin.fa
eukcc folder --out results/taxonomy/eukcc_bins --threads 8 bins
```

---

## vConTACT3 — viral clustering to support taxonomy inference

Docs:
- https://vcontact3.readthedocs.io/
Release checked:
- vConTACT3 release notes latest entry: v3.2.0 (2026-03-26).
- The ReadTheDocs page title still reports "vConTACT3 3.0.1"; prefer the release notes and installed `vcontact3 --version` for provenance.

### When to use
- Phage/prokaryotic-virus contigs/genomes: protein-sharing network clustering supports taxonomy inference.
- Not a replacement for ICTV; interpret results in ICTV context and with hallmark genes/phylogeny.

### Install/run (recommended)
Use **Pixi** (see env/README.md) and capture:
- vConTACT3 version
- database/reference used (if any)
- parameterization (e.g., thresholds, export options)

### Run examples
```bash
vcontact3 prepare_databases --list-versions
vcontact3 prepare_databases --get-version latest --set-location ./db
vcontact3 run --nucleotide genomes.fna --output results/taxonomy/vcontact3
```

---

## GVClass — giant-virus / Nucleocytoviricota taxonomy

Docs:
- https://github.com/NeLLi-team/gvclass
Release checked:
- GVClass v1.6.0 (2026-05-29).
- Release notes state software v1.6.0 is compatible with resource bundle v1.5.0.

### When to use
- Giant-virus, NCLDV, or Nucleocytoviricota candidates from QuickClade, geNomad, hallmark genes, or genome-size/marker evidence.
- Use with marker-gene phylogenies and literature-supported reference sets; do not force vConTACT3 on giant-virus candidates unless the literature justifies it.

### Provenance to capture
- GVClass version or commit
- reference/model bundle version
- run mode and thresholds
- marker-gene phylogeny inputs used for validation

### Run examples
```bash
gvclass my_genomes -o results/taxonomy/gvclass -t 32
gvclass --contigs candidate_contigs.fna -o results/taxonomy/gvclass_contigs -t 32
```

---

## TaxonKit — NCBI taxonomy toolkit for taxids and lineages

Docs:
- https://bioinf.shenwei.me/taxonkit/usage/
- https://github.com/shenwei356/taxonkit
Release checked:
- TaxonKit v0.20.0.
- NCBI `taxdump.tar.gz` FTP listing was current on 2026-05-30.

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

```bash
wget -c https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz
tar -zxvf taxdump.tar.gz
mkdir -p "$HOME/.taxonkit"
cp names.dmp nodes.dmp delnodes.dmp merged.dmp "$HOME/.taxonkit"
```
