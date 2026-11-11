# Bio-Annotation Tool Choice

**Last verified**: 2026-05-30
**Tool version/release checked:** DIAMOND v2.2.1; eggNOG-mapper v2.1.15; InterProScan 5.77-108.0 / InterProScan6 6.0.0; TaxonKit v0.20.0; MMseqs2 official static build checked 2026-05-30
**Official docs/manual:** https://github.com/bbuchfink/diamond/wiki; https://github.com/eggnogdb/eggnog-mapper; https://interproscan-docs.readthedocs.io/; https://bioinf.shenwei.me/taxonkit/usage/; https://github.com/soedinglab/MMseqs2/wiki
**Release/source:** https://github.com/bbuchfink/diamond/releases/tag/v2.2.1; https://github.com/eggnogdb/eggnog-mapper/releases/tag/v2.1.15; https://github.com/ebi-pf-team/interproscan/releases/tag/5.77-108.0; https://github.com/shenwei356/taxonkit/releases/tag/v0.20.0

This page records which tool to use for which task and the points a model is likely to get wrong. For flags, run `--help`.

## Tool choice

| Task | Tool | Reason |
|------|------|--------|
| Homology search, CPU | DIAMOND | Fast BLAST-compatible search for proteins and translated DNA. |
| Homology search, GPU node (CUDA Turing or newer) | MMseqs2-GPU | Use `mmseqs easy-search` or `easy-taxonomy` with `--gpu`. Also replaces JackHMMER for iterative profile searches. |
| Orthology and function (GO, COG, KEGG) | eggNOG-mapper v2 | Transfers annotation through orthologous groups. |
| Domains and families | InterProScan | Integrates the member signature databases and maps them to InterPro entries and GO terms. |
| Taxonomy from homology hits | TaxonKit | Resolves the TaxIDs in search results to lineages. |
| HMM marker and domain-family scans | pyhmmer | Python bindings for HMMER 3.4. Fall back to `hmmsearch` or `hmmscan` only when an upstream tool requires the CLI. |

## Sequence search backends

Default CPU path: DIAMOND v2.1.20 or later, against a clustered nr database. Use MMseqs2-GPU when a CUDA node is available.

### DIAMOND

- Prefer a clustered nr database (for example `clusterednr`) over full nr. It searches much faster at comparable sensitivity for most annotation tasks. Check `$BIO_DB_ROOT` first. If it is missing, fall back to full nr and record the choice in the run log, or build one with `diamond makedb` from an MMseqs2 or CD-HIT reduced nr FASTA (identity 70 to 90% by use case).
- The default mode sits between `--fast` and `--mid-sensitive`. `--sensitive` is a separate mode above the default, with full sensitivity for hits above 40% identity. Use `--very-sensitive` for divergent sequences.
- `--memory-limit` applies only to `cluster` and `linclust`. For `blastp` and `blastx`, lower `--block-size` or raise `--index-chunks`.
- DIAMOND tabular output has no header. Do not drop the first line before TaxonKit.

```bash
diamond blastp --query proteins.faa --db clusterednr.dmnd --out results.tsv \
  --outfmt 6 qseqid sseqid staxids evalue bitscore --threads 32 --sensitive
```

### MMseqs2-GPU

Published benchmark: 20 times faster and about 71 times cheaper per query than 128-core CPU MMseqs2, and 177 to 199 times faster than JackHMMER iterative search (Kallenborn et al., *Nature Methods* 2025, https://doi.org/10.1038/s41592-025-02819-8). Benchmark the current build on the target node before production.

## eggNOG-mapper (orthology and function)

- Stay on v2 (`eggnog-mapper>=2.1.13,<3`) with the eggNOG v5.0.2 data these commands were checked against. v3.0.0 is a beta with changes. Use it only when a project pins it on purpose.
- `download_eggnog_data.py` skips files that are already present; `-f` forces a new download. It writes `eggnog.db` and `eggnog_proteins.dmnd` (`-D` skips the DIAMOND database).
- `--dbmem` loads `eggnog.db` (39 GB) and the DIAMOND database (8.7 GB) into memory. Benchmark runs ran out of memory at 32 GB and often at 64 GB. Request at least 128 GB or leave it out.
- `emapper.py` finds DIAMOND with `shutil.which('diamond')`. Inside a pixi environment on a batch node, put the environment `bin` on `PATH`.
- `-m cache -c <file>` reuses an earlier annotations file made with `--md5`.

```bash
emapper.py -i proteins.faa -o annotation --data_dir $EGGNOG_DATA_DIR \
  --sensmode very-sensitive --report_orthologs --cpu 32
```

## InterProScan (domains)

- InterProScan 5 (`interproscan.sh`) and InterProScan 6 (Nextflow) both have current releases. 5.78-109.0 and 6.0.2.2 were current on 2026-10-01. Pin one release and one InterPro data release per project.
- InterProScan 6 needs Nextflow 25.10 or later and a container runtime (Docker, Podman, SingularityCE or Apptainer). It has no `local` profile. Pin the workflow with `-r` and the data with `--interpro` (`latest` is not reproducible). A node without internet needs `--noMatchesApi`.
- InterProScan 5: the precalculated match lookup is on by default and needs network. `-dp` turns it off. `-pa` adds pathways and implies `-iprlookup`.
- `-b`, `-d` and `-o` are mutually exclusive. Input sequences need at least 15 amino acids and no `*`. After a packaged install, run `python3 setup.py -f interproscan.properties`.

```bash
interproscan.sh -i proteins.faa -b interpro_results -f TSV,GFF3 \
  -goterms -iprlookup -pathways -cpu 32
```

```bash
nextflow run ebi-pf-team/interproscan6 -r 6.0.2.2 -profile singularity \
  --input proteins.faa --datadir /path/to/interpro_data --interpro 110.0
```

## TaxonKit (taxonomy from homology)

- Use v0.20.0 or later. It handles the March 2025 NCBI rank update ("superkingdom" became "domain"; viruses gained "realm").
- Use `reformat2` with `{domain|acellular root|superkingdom}`; `{a|b}` takes the first rank present. `reformat2` takes TaxIDs only and has no `-F` or `-P`. Write rank prefixes in the format string.
- `lca` splits ids on spaces. Pass `-s ","` for comma-separated ids.
- The taxdump needs `names.dmp`, `nodes.dmp`, `delnodes.dmp` and `merged.dmp` in `~/.taxonkit` or `--data-dir`. The last two resolve renamed and deleted IDs. `reformat2 -R` marks unresolved IDs.

```bash
cut -f3 results.tsv | taxonkit lineage -n -r -j 8 | taxonkit reformat2 -j 8 \
  -f "{domain|acellular root|superkingdom};{phylum};{class};{order};{family};{genus};{species}" \
  | paste results.tsv - > results_with_taxonomy.tsv
```

## References

- DIAMOND: Buchfink et al. (2021) *Nature Methods* https://doi.org/10.1038/s41592-021-01101-x
- TaxonKit: Shen & Ren (2021) *Journal of Genetics and Genomics* https://doi.org/10.1016/j.jgg.2021.03.006
- InterProScan: Jones et al. (2014) *Bioinformatics* https://doi.org/10.1093/bioinformatics/btu031
- eggNOG-mapper: Cantalapiedra et al. (2021) *Molecular Biology and Evolution* https://doi.org/10.1093/molbev/msab293
- MMseqs2-GPU: Kallenborn et al. (2025) *Nature Methods* https://doi.org/10.1038/s41592-025-02819-8
