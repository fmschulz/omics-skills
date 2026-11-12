# Viromics Tool Choice

Last verified: 2026-11-11
Tool version/release checked: geNomad v1.13.0 / DB v1.9 (`--help` of the 1.13.0 container; database listing on portal.nersc.gov); CheckV v1.1.1 / DB v1.5 (`end_to_end --help`; `CURRENT_RELEASE.txt`); vConTACT3 3.2.4 (newest tag; bioconda 3.1.6, `--help` of the container); GVClass v2.1.0 / resources v2.1.0 (docs of the tag, not run)
Official docs/manual: https://portal.nersc.gov/genomad/; https://bitbucket.org/berkeleylab/checkv; https://vcontact3.readthedocs.io/; https://NeLLi-team.github.io/gvclass/
Release/source: https://github.com/apcamargo/genomad/releases/tag/v1.13.0; https://pypi.org/project/checkv/; https://bitbucket.org/MAVERICLab/vcontact3/commits/tag/3.2.4; https://github.com/NeLLi-team/gvclass/releases/tag/v2.1.0

This page records what each tool does in this pack, the order they run in, and the points a model is likely to get wrong. For flags, run `--help`. Models know geNomad and CheckV well, so they have no guide here. vConTACT3 and GVClass have guides because models know them poorly.

## Order

1. Domain triage (QuickClade via `/tracking-taxonomy-updates`). Viral and virus-like rows continue here.
2. geNomad detects virus and plasmid sequences, finds proviruses and gives a first ICTV taxonomy.
3. CheckV grades completeness and contamination and trims host regions from proviruses.
4. Then one of:
   - [vConTACT3](vcontact3-usage.md) for prokaryotic viruses. It clusters genomes by gene sharing and assigns taxonomy. Input: high- and medium-quality CheckV genomes.
   - [GVClass](gvclass-usage.md) for Nucleocytoviricota, Mirusviricota and Preplasmiviricota. It places each marker on a tree and reports completeness and contamination. Input: bins or contigs of 30 kb or more (50 kb preferred).

| Tool | Role | Key output |
|------|------|------------|
| geNomad | Viral detection | `<prefix>_summary/<prefix>_virus.fna` |
| CheckV | Quality assessment | `quality_summary.tsv` |
| vConTACT3 | Clustering and taxonomy | `final_assignments.csv` |
| GVClass | Giant-virus classification | `gvclass_summary.tsv` |

## Versions and databases

- Pair geNomad v1.13.0 with database v1.9 (still the newest database on 2026-11-11) and CheckV v1.1.1 with database v1.5. geNomad 1.13.0 adds one thing over 1.12.0: the `GENOMAD_DB` environment variable replaces the `DATABASE` argument of `annotate`, `find-proviruses`, `marker-classification` and `end-to-end` when you leave it out.
- `genomad download-database .` writes `genomad_db/`. Record the database version from that directory in the run manifest.
- `checkv download_database ./` fetches the release named in `https://portal.nersc.gov/CheckV/CURRENT_RELEASE.txt` (`checkv-db-v1.5` at verification time). Point to it with `-d` (no long form) or `export CHECKVDB=/path/to/checkv-db-v1.5`. `checkv update_database <db> <new_db> genomes.fna` adds your own complete viral genomes to a copy.
- A PyPI install of CheckV needs DIAMOND v2.2.0 (upstream flags v2.1.9 as a core-dump risk) and HMMER v3.3 installed separately.
- vConTACT3 3.2.4 is the upstream source tag; bioconda ships 3.1.6. It needs Python 3.10 or 3.11. GVClass runs from its own pixi checkout or, with `--apptainer`, from the single `gvclass` launcher (v2.1.0 retired `gvclass-a`); it needs resource bundle v2.1.0.

```bash
pixi add genomad checkv
pixi add "python>=3.10,<3.12" vcontact3
wget https://raw.githubusercontent.com/NeLLi-team/gvclass/main/gvclass && chmod +x gvclass
```

## geNomad

```bash
genomad end-to-end -t 16 --cleanup contigs.fna.gz genomad_out genomad_db
```

- `-t` defaults to every CPU the process may use, which is the whole node when the scheduler does not bind CPUs. Set it to the allocation.
- `<prefix>` is the input name without extensions. `genomad_out/<prefix>_summary/` holds `<prefix>_virus_summary.tsv`, `<prefix>_virus.fna` (proviruses excised), `<prefix>_virus_proteins.faa` and `<prefix>_virus_genes.tsv`, plus the same four files for plasmids and `<prefix>_summary.json`. The CheckV input is `<prefix>_virus.fna`.
- A rerun resumes. `--restart` overwrites intermediate files. `--splits 8` lowers memory use.
- `--conservative` cuts false positives and `--relaxed` suits exploratory screens followed by CheckV. Neither combines with explicit thresholds (`--min-score`, `--max-fdr`, `--min-number-genes`, `--max-uscg`).
- `--max-fdr` has no effect unless `--enable-score-calibration` is set. Taxonomy below family needs `--lenient-taxonomy`.

## CheckV

```bash
checkv end_to_end viral.fna checkv_out -d checkv-db-v1.5 -t 16
```

- `-t` defaults to every CPU the process may use. Set it to the allocation. A rerun continues where it stopped; `--restart` starts over.
- Outputs: `quality_summary.tsv` (primary), `completeness.tsv`, `contamination.tsv`, `complete_genomes.tsv`, `proviruses.fna` (host regions removed) and `viruses.fna`.
- `quality_summary.tsv` has `checkv_quality` and `miuvig_quality` columns:

| `checkv_quality` | Rule | `miuvig_quality` |
|------------------|------|------------------|
| Complete | Closed-genome prediction (direct or inverted terminal repeats) at medium or high confidence | High-quality |
| High-quality | Completeness 90% or more | High-quality |
| Medium-quality | Completeness 50% to under 90% | Genome-fragment |
| Low-quality | Completeness under 50% | Genome-fragment |
| Not-determined | No completeness estimate; the sequence is too divergent from the database | Genome-fragment |

- Short fragments rarely get a completeness estimate. Report sequences that fail the project thresholds.

## References

- geNomad: Camargo et al. (2023) *Nature Biotechnology* https://doi.org/10.1038/s41587-023-01953-y
- CheckV: Nayfach et al. (2020) *Nature Biotechnology* https://doi.org/10.1038/s41587-020-00774-7
- GVClass: Pitot et al. (2024) *npj Viruses* https://doi.org/10.1038/s44298-024-00069-7
