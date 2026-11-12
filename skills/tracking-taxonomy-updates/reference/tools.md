# Tool cheat sheets (QuickClade, GTDB-Tk, EukCC, vConTACT3, GVClass, TaxonKit)

Last verified: 2026-11-11
Tool version/release checked: QuickClade / BBTools v39.85 via `bryce911/bbtools:39.85` (run; the newest tag, 40.05, was run too and differs, see below); GTDB-Tk 2.8.0 / GTDB Release 232 (`--help` of the 2.8.0 container and release notes; not run, the reference package is too large); EukCC v.2.2.0 (`folder --help`; not run); vConTACT3 3.2.4 (newest tag; bioconda 3.1.6 `--help`); GVClass v2.1.0 (docs of the tag; not run); TaxonKit v0.20.0
Official docs/manual: See table below.
Release/source: See table below.

| Tool/source | Tool version/release checked | Official docs/manual | Release/source |
|---|---|---|---|
| QuickClade / BBTools | BBTools QuickClade docs checked; examples use container tag `39.85` and checked digest `sha256:e697da46d8955a30256cc1c2a9ed8da362ad5a86ed16b6a41ab64ed03801a2a1` (unchanged on 2026-11-11); newest tag on 2026-11-11 is `40.05` (`latest`, digest `sha256:b39c1c2a9bbbafefc1662d20607eece9ed4d4db72506760735062df3cd23f6ec`) | https://bbmap.org/tools/quickclade | https://hub.docker.com/r/bryce911/bbtools/tags |
| GTDB-Tk | GTDB-Tk 2.8.0; GTDB-Tk reference package Release 232 (`gtdbtk_r232_data.tar.gz`) | https://ecogenomics.github.io/GTDBTk/ | https://github.com/Ecogenomics/GTDBTk/releases/tag/2.8.0 |
| EukCC | EukCC v.2.2.0 (git tag; changed from 2.1.3 by a docs update and a test); EukCC2 database docs still show `eukcc2_db_ver_1.1` | https://eukcc.readthedocs.io/ | https://github.com/EBI-Metagenomics/EukCC/tree/v.2.2.0 |
| vConTACT3 | git tag 3.2.4; `run` options checked in `vcontact3/cli.py` | https://vcontact3.readthedocs.io/ | https://bitbucket.org/MAVERICLab/vcontact3 |
| GVClass | GVClass v2.1.0; resource bundle v2.1.0 required | https://github.com/NeLLi-team/gvclass | https://github.com/NeLLi-team/gvclass/releases/tag/v2.1.0 |
| TaxonKit | TaxonKit v0.20.0 (newest release on 2026-11-11); NCBI taxdump FTP listing checked 2026-05-30 | https://bioinf.shenwei.me/taxonkit/ | https://github.com/shenwei356/taxonkit/releases/tag/v0.20.0 |

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
- Checked digest of tag 39.85 (unchanged on 2026-11-11): `sha256:e697da46d8955a30256cc1c2a9ed8da362ad5a86ed16b6a41ab64ed03801a2a1`
- Stay on tag 39.85 for QuickClade. On 2026-11-11 the newest tag `40.05` (also `latest`) differed in three ways: its image no longer holds the reference `refseqA48_with_ribo.spectra.gz` (245 MB, present at `/bbmap/resources/` in 39.85); `quickclade.sh` without a local reference then queried a remote server and sent the k-mer spectra of the input (run with `--network none` it failed with `ConnectException`, while 39.85 ran offline); and its `format=machine` output has 21 columns instead of 26 (no `ANI`, `WKID`, `KID`, `Completeness`, `KmerMatches`). Mounting a copy of the 39.85 file into `/bbmap/resources/` and passing it with `ref=` made 40.05 run.
- `quickbin.sh ... report=<file>` also sends bin k-mer spectra to the QuickClade server on both tags unless you pass `clade=f` ([quickbin.md](../../omics-pipeline/references/quickbin.md)).
- Record the resolved image digest at run time with `docker image inspect` or the equivalent Apptainer/Singularity metadata.
- Docker Hub page:
  https://hub.docker.com/r/bryce911/bbtools/

#### Docker examples
Run on a FASTA in the current directory:
```bash
QUICKCLADE_REF="${QUICKCLADE_REF:?set QUICKCLADE_REF to an existing spectra file}"
test -s "$QUICKCLADE_REF"
mkdir -p "$RUN_DIR/taxonomy"
docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD":/work -w /work \
  bryce911/bbtools:39.85 \
  quickclade.sh contigs.fa percontig ref="$QUICKCLADE_REF" \
  out=$RUN_DIR/taxonomy/quickclade_percontig.tsv format=machine usetree
```

Run on a directory of bins:
```bash
mkdir -p "$RUN_DIR/taxonomy"
docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD":/work -w /work \
  bryce911/bbtools:39.85 \
  quickclade.sh bins/ percontig ref="$QUICKCLADE_REF" \
  out=$RUN_DIR/taxonomy/quickclade_bins_percontig.tsv format=machine usetree
```

#### Apptainer / Singularity examples
Pull + run directly from Docker Hub:
```bash
mkdir -p "$RUN_DIR/taxonomy"
apptainer exec --bind "$PWD":/work --pwd /work \
  docker://bryce911/bbtools:39.85 \
  quickclade.sh contigs.fa percontig ref="$QUICKCLADE_REF" \
  out=$RUN_DIR/taxonomy/quickclade_percontig.tsv format=machine usetree
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
- GTDB-Tk 2.8.0 (2026-10-13). It uses the same Release 232 reference package as 2.7.x: `gtdbtk_r232_data.tar.gz`.
- 2.8.0 changes `classify_wf` results: `classify` and `classify_wf` now apply one species rule (the closest reference with alignment fraction at or above `--min_af`, default 0.5, is checked against its ANI radius; before, `classify_wf` could assign a more distant species when the genome fell outside that radius), report the same `other_related_references` (alignment fraction at or above `--min_af`, closest first, at most 50, assigned reference not repeated), and write a new `classify/ani_screen/<prefix>.ani_screen_unassigned_hits.tsv.gz`. Fuzzy species assignments can therefore differ from 2.7.x runs. Resuming a `classify_wf` directory made by an older version reruns the ANI screen; older versions cannot resume a 2.8.0 directory.

### When to use
- Genome-based taxonomy for MAGs/SAGs/isolate genomes.
- Outputs GTDB taxonomy strings like: `d__Bacteria;p__...;...;s__...`

### Install/run (recommended)
Use the project's pinned **Pixi** environment and retain its lockfile.
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
SLURM_ACCOUNT="${SLURM_ACCOUNT:?}" \
  "$SKILL_DIR/scripts/submit_taxonomy.sh" gtdbtk bins "$RUN_DIR/taxonomy/gtdbtk"
```

The template passes `-x "${GTDBTK_EXTENSION:-fa}"`; export `GTDBTK_EXTENSION=fna` (or another suffix) when the genome files do not end in `.fa`.

GTDB-Tk 2.7.x and 2.8.0 run the ANI screen by default using the pre-sketched skani database. If a project requires species that pass the ANI screen to still be placed in pplacer trees, add `--place_species` (listed under `gtdbtk classify_wf --help` of 2.8.0); this replaces the older `--skip_ani_screen` workflow. `-x/--extension` defaults to `fna`, and `--cpus` to 1.

---

## EukCC — eukaryotic MAG/genome QC + taxonomy context

Docs:
- https://eukcc.readthedocs.io/
Release checked:
- EukCC v.2.2.0 (git tag; `eukcc folder --db --out --threads` options unchanged).
- EukCC docs still show EukCC2 database `eukcc2_db_ver_1.1`; the binning page uses `eukcc2_db_ver_1.2`. The FTP directory also holds `eukcc2_db_ver_2026_11.tar.gz` (6.2 GB, 2026-11-09), which the docs do not mention and which was not tested. Record the exact database directory or `--db` path used in each run.

### When to use
- Eukaryotic MAGs/genomes where bacterial QC tools are inappropriate.
- Provides completeness/contamination estimates and a taxonomy lineage.

### Install/run (recommended)
Use the project's pinned **Pixi** environment and capture:
- EukCC version
- database location/version (`EUKCC2_DB` or `--db`)

### Run examples
```bash
SLURM_ACCOUNT="${SLURM_ACCOUNT:?}" \
  "$SKILL_DIR/scripts/submit_taxonomy.sh" eukcc bins "$RUN_DIR/taxonomy/eukcc_bins"
```

---

## vConTACT3 — viral clustering to support taxonomy inference

Docs:
- https://vcontact3.readthedocs.io/
Release checked:
- vConTACT3 3.2.4 (git tag). Record the installed `vcontact3 version` for provenance.
- `vcontact3 run` needs `--db-path` (from `vcontact3 prepare_databases --get-version latest --set-location DIR`), even with `--no-db`.
- `--threads` defaults to every CPU on the node, so always pass it on shared nodes. The bundled sbatch template passes `--db-path "$VCONTACT3_DB"` and `--threads "$SLURM_CPUS_PER_TASK"`.

### When to use
- Phage/prokaryotic-virus contigs/genomes: protein-sharing network clustering supports taxonomy inference.
- Not a replacement for ICTV; interpret results in ICTV context and with hallmark genes/phylogeny.

### Install/run (recommended)
Use the project's pinned **Pixi** environment and capture:
- vConTACT3 version
- database/reference used (if any)
- parameterization (e.g., thresholds, export options)

### Run examples
```bash
SLURM_ACCOUNT="${SLURM_ACCOUNT:?}" VCONTACT3_DB=/path/to/vcontact3_db \
  "$SKILL_DIR/scripts/submit_taxonomy.sh" vcontact3 genomes.fna "$RUN_DIR/taxonomy/vcontact3"
```

---

## GVClass — giant-virus / Nucleocytoviricota taxonomy

Docs:
- https://github.com/NeLLi-team/gvclass
Release checked:
- GVClass v2.1.0 (2026-10-19). The changelog names resource bundle v2.1.0 (Zenodo DOI 10.5281/zenodo.23381313) as the compatible bundle.
- v2.1.0 merges the `gvclass` and `gvclass-a` entrypoints into `gvclass` (`--apptainer` for the container), drops the labels `moderate` and `high`, and reports `NaN` for estimates without evidence. The full list is in `skills/bio-viromics/docs/gvclass-usage.md`.

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
SLURM_ACCOUNT="${SLURM_ACCOUNT:?}" \
  "$SKILL_DIR/scripts/submit_taxonomy.sh" gvclass my_genomes "$RUN_DIR/taxonomy/gvclass"
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
