# Environment setup

Last verified: 2026-05-30
Tool version/release checked: Pixi v0.69.0; BBTools/QuickClade v39.85 via `bryce911/bbtools:39.85`; GTDB-Tk 2.7.2 / GTDB-Tk reference Release 232; EukCC v.2.1.3; vConTACT3 release notes v3.2.0; GVClass v1.6.0; TaxonKit v0.20.0
Official docs/manual: https://pixi.sh/latest/ ; https://bbmap.org/tools/quickclade ; https://ecogenomics.github.io/GTDBTk/ ; https://eukcc.readthedocs.io/ ; https://vcontact3.readthedocs.io/ ; https://github.com/NeLLi-team/gvclass ; https://bioinf.shenwei.me/taxonkit/
Release/source: https://github.com/prefix-dev/pixi/releases/tag/v0.69.0 ; https://hub.docker.com/r/bryce911/bbtools/tags ; https://github.com/Ecogenomics/GTDBTk/releases/tag/2.7.2 ; https://github.com/EBI-Metagenomics/EukCC/releases/tag/v.2.1.3 ; https://bitbucket.org/MAVERICLab/vcontact3 ; https://github.com/NeLLi-team/gvclass/releases/tag/v1.6.0 ; https://github.com/shenwei356/taxonkit/releases/tag/v0.20.0

This Skill assumes you may run tools locally (HPC, workstation, CI) and want **reproducible installs**.

## Recommended approach
- **QuickClade (BBTools)**: run via the BBTools container tag used in this skill, `bryce911/bbtools:39.85` (Docker or Apptainer/Singularity). As of 2026-05-30, the checked digest is `sha256:e697da46d8955a30256cc1c2a9ed8da362ad5a86ed16b6a41ab64ed03801a2a1`; record the resolved image digest at run time.
- **GTDB-Tk, EukCC, vConTACT3, TaxonKit**: manage dependencies via **Pixi** using `pixi.toml`.
- **GVClass**: use the `/bio-viromics` GVClass setup notes for giant-virus routes.

---

## A) QuickClade via container (preferred)

### Docker
```bash
docker pull bryce911/bbtools:39.85
docker run --rm bryce911/bbtools:39.85 quickclade.sh --help
```

For data in the current directory:
```bash
docker run --rm -u "$(id -u):$(id -g)"   -v "$PWD":/work -w /work   bryce911/bbtools:39.85   quickclade.sh contigs.fa percontig out=results.tsv usetree
```

For production runs, pass the spectra explicitly and write the standard per-contig artifact:

```bash
mkdir -p results/taxonomy
docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD":/work -w /work \
  bryce911/bbtools:39.85 \
  quickclade.sh contigs.fa percontig ref=references/quickclade.spectra.gz out=results/taxonomy/quickclade_percontig.tsv usetree
```

### Apptainer / Singularity
```bash
apptainer exec docker://bryce911/bbtools:39.85 quickclade.sh --help
```

For data in the current directory:
```bash
apptainer exec --bind "$PWD":/work --pwd /work   docker://bryce911/bbtools:39.85   quickclade.sh contigs.fa percontig out=results.tsv usetree
```

Provenance: record container tag (and digest if available) in outputs.

---

## B) Pixi for GTDB-Tk / EukCC / vConTACT3 / TaxonKit

Pixi docs:
- https://pixi.sh/latest/
Pixi manifest reference:
- https://pixi.sh/latest/reference/pixi_manifest/

### Install Pixi
Follow the official Pixi install instructions for your OS.

### Create the environment
From this Skill directory:
```bash
cd ~/.agents/skills/tracking-taxonomy-updates/env
pixi install
```

### Run commands
```bash
pixi run gtdbtk-help
pixi run eukcc-help
pixi run vcontact3-help
pixi run taxonkit-help
```

### Reproducibility tip
If you use this environment in a pipeline, commit:
- `pixi.toml`
- the generated lockfile (e.g., `pixi.lock`), if you create one

---

## C) Data packages you still need to manage explicitly
Even with reproducible tool installs, taxonomy work depends on large external datasets:

- **NCBI Taxdump** (TaxonKit needs this): download and record the dump date.
- **GTDB-Tk reference package**: GTDB-Tk 2.7.2 expects the Release 232 package (`gtdbtk_r232_data.tar.gz`); record the release ID/date and checksum.
- **EukCC database**: set `EUKCC2_DB` (or pass `--db`) and record DB version/path. The public EukCC docs still show `eukcc2_db_ver_1.1`; do not silently substitute another database without documenting it.
- **vConTACT3 reference sets**: use `vcontact3 prepare_databases --list-versions` and record the selected version/location.
