# vConTACT3 Usage Guide

Last verified: 2026-10-01
Tool version/release checked: vConTACT3 3.2.4 source tag (`vcontact3 run --help` and `prepare_databases --help` run from that tag); bioconda latest 3.1.6
Official docs/manual: https://vcontact3.readthedocs.io/en/latest/
Release/source: https://bitbucket.org/MAVERICLab/vcontact3/commits/tag/3.2.4 ; https://bitbucket.org/MAVERICLab/vcontact3

## Official Documentation
- ReadTheDocs: https://vcontact3.readthedocs.io/
- Bitbucket: https://bitbucket.org/MAVERICLab/vcontact3

## Overview
vConTACT3 clusters viral genomes with gene-sharing networks of protein clusters and assigns hierarchical taxonomy from genus to order against a reference database. It replaces vConTACT2.

## Installation

```bash
pixi add "python>=3.10,<3.12" vcontact3
```

Bioconda ships 3.1.6. The 3.2.x line is available from the Bitbucket tag; install it into the project environment as a PyPI dependency from Git when a project needs it, and record the version in the run manifest.

Optional ANI export needs vclust:
```bash
pixi add --pypi vclust
```

## Key Commands & Flags

| Command | Purpose |
|---------|---------|
| `vcontact3 version` | Show the version |
| `vcontact3 prepare_databases` | List (`-l`), download (`-g VERSION`), and place (`-s PATH`) reference databases |
| `vcontact3 run` | Cluster genomes and assign taxonomy |

### `vcontact3 run` options (3.2.4)

| Flag | Description |
|------|-------------|
| `-n, --nucleotide` | Nucleotide FASTA; enables gene calling |
| `--pyrodigal-gv` | Use pyrodigal-gv models (giant viruses, alternative genetic codes) |
| `-p, --proteins` | Protein FASTA; disables ANI export |
| `-g, --gene2genome` | Gene-to-genome mapping (required with `--proteins`) |
| `-l, --len-nucleotide` | Genome length file |
| `-o, --output` | Output directory (default `vConTACT3_results`) |
| `-d, --db-path` | Database file or directory. Required, also with `--no-db` |
| `--db-domain` | `archaea`, `bacteria`, `prokaryotes` (default), or `eukaryotes` |
| `--db-version` | Database version to use |
| `--no-db` | Cluster user genomes de novo; VOG-based taxonomy still runs |
| `-e, --exports` | Any of `cytoscape graphml cosmograph d3js ani newick profiles completeness centroids` |
| `-t, --threads` | CPUs. Default: every CPU on the host (`multiprocessing.cpu_count()`), not the Slurm allocation; set it to the allocated CPU count |
| `--reduce-memory` | Use float16 arrays |
| `-i, --max-iterations` | Iterations for resolving mixed-realm components (default 3) |
| `-f, --force-overwrite` | Overwrite existing files |

## Common Usage Examples

### Database preparation
```bash
vcontact3 prepare_databases --list-versions
vcontact3 prepare_databases --get-version latest --set-location ./vcontact3_db
```

### Nucleotide input
```bash
vcontact3 run \
  --nucleotide genomes.fna \
  --db-path ./vcontact3_db \
  --db-domain prokaryotes \
  --output results_dir \
  --threads 16
```

### Protein input
```bash
vcontact3 run \
  --proteins proteins.faa \
  --gene2genome gene2genome.tsv \
  --len-nucleotide genome_lengths.tsv \
  --db-path ./vcontact3_db \
  --output results_dir \
  --threads 16
```

### Network and profile exports
```bash
vcontact3 run \
  --nucleotide genomes.fna \
  --db-path ./vcontact3_db \
  --exports graphml cytoscape profiles \
  --output results_dir \
  --threads 16
```

## Input/Output

### Input
- Nucleotide mode: FASTA of viral genomes
- Protein mode: protein FASTA, gene-to-genome TSV, and genome-length TSV

### Output
- `final_assignments.csv`: taxonomy and cluster assignments
- Network files for the requested `--exports` formats
- Protein-cluster profiles with `--exports profiles`
- ANI matrices with `--exports ani` (requires vclust and nucleotide input)

## Performance Tips

1. Filter low-quality genomes with CheckV before clustering.
2. Request only the exports you need.
3. Use `--reduce-memory` on memory-limited nodes.
4. Set `--threads` to the allocated CPU count.

## Integration with Viromics Workflow

1. Input: high- and medium-quality prokaryotic-virus genomes from CheckV.
2. Analysis: gene-sharing network and hierarchical clustering.
3. Output: genome clusters and taxonomy.
4. Use only for prokaryotic viruses unless the literature playbook supports another group.

## Troubleshooting

- **Memory errors**: use `--reduce-memory`, split the dataset, or request a larger node.
- **MMseqs2 not found**: install `mmseqs2` in the environment or pass `--mmseqs-bin`.
- **Python version errors**: use Python 3.10 or 3.11.
- **Database errors**: run `vcontact3 prepare_databases --list-versions`, then download a listed version.
