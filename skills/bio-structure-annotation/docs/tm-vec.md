# TM-Vec

Fast protein structure embedding and similarity search using transformer-based vector representations.

Last verified: 2026-05-30
Tool version/release checked: TM-Vec 1.0.2 (original); valentynbez/tmvec fork 1.1.0 at commit 6bdf11a (2026-07-24; the fork has no tagged releases)
Official docs/manual: https://github.com/tymor22/tm-vec; https://github.com/valentynbez/tmvec
Release/source: https://github.com/tymor22/tm-vec/releases/tag/1.0.2

## Installation

Pin the maintained fork in the project's Pixi environment. The original
`tymor22/tm-vec` repository points users to `valentynbez/tmvec` for continued
maintenance. The fork provides the `tmvec build-db` and `tmvec search`
commands used below; the original 1.0.2 package ships `tmvec-build-database`
and `tmvec-search` with different arguments. The fork's README shows
`tmvec search --query`, but the pinned CLI (`src/tmvec/cli.py`) requires
`--input-fasta` for both subcommands and rejects `--query`.

```bash
pixi add --pypi "tmvec @ git+https://github.com/valentynbez/tmvec.git@6bdf11adff9884cff54e4f69927d40edebc80038"
```

With internet access the fork downloads its models on first use into a cache
directory. Compute nodes without internet need the models copied in. Pass
them to `build-db` with `--tm-vec-model` and `--protrans-model`, plus
`--local` to stop download attempts. The database stores these model paths,
and `search` reuses them: it ignores `--protrans-model` and uses
`--tm-vec-model` only to override the stored path. Keep the stored paths
valid on the compute node.

### Download Model Weights
Required for embedding generation:
```bash
mkdir Rostlab && cd Rostlab
wget https://zenodo.org/record/4644188/files/prot_t5_xl_uniref50.zip
unzip prot_t5_xl_uniref50.zip
cd ..
```

## Available Models

| Model | Max Length | Training Set | Use Case |
|-------|-----------|--------------|----------|
| `tmvec_swiss_model` | 300 residues | SWISS-PROT | Base model for short sequences |
| `tmvec_swiss_model_large` | 1000 residues | SWISS-PROT | Long sequences, Swiss-Prot searches |
| `tm_vec_cath_model` | 300 residues | CATH S40 | Base model for domain searches |
| `tm_vec_cath_model_large` | 1000 residues | CATH S100 | Long domains, CATH searches |

Models available at: https://figshare.com/s/e414d6a52fd471d86d69

## Pre-built Databases

Download from Zenodo: https://zenodo.org/records/11199459

- **CATH domains database** - Use with `tm_vec_cath_model_large`
- **SWISS-PROT sequences** - Use with `tmvec_swiss_model_large`

Embeddings stored as numpy arrays (.npy format):
```python
import numpy as np
embeddings = np.load('database.npy', allow_pickle=True)
```

## Common Usage

### Build a database

```bash
tmvec build-db --input-fasta references.faa --output tmvec_db/references
```

### Search a database

```bash
tmvec search \
  --input-fasta queries.faa \
  --database tmvec_db/references.npz \
  --output tmvec_out
```

`--output` is a folder. The search writes the hit table to
`tmvec_out/results.tsv` and, with the default `--output-fmt npz`, the query
embeddings to `tmvec_out/embeddings.npy`.
It returns 5 neighbors per query by default (`--k-nearest`) and skips
sequences longer than 1024 residues. `build-db --output tmvec_db/references`
writes `tmvec_db/references.npz`.

`scripts/run_structure_annotation.py --tmvec-query queries.faa --tmvec-db
tmvec_db/references.npz --out-dir OUT` plans this search with
`--output OUT/tmvec` and checks `OUT/tmvec/results.tsv` after `--execute`.

## Input/Output Formats

- **Input**: Protein sequences in FASTA format
- **Output**:
  - Vector embeddings (numpy arrays)
  - Similarity scores for homology detection
  - Position-indexed metadata linking embeddings to sequences

## Performance Tips

- Use GPU for embedding generation on large datasets
- GPU users may need to reinstall PyTorch separately for optimal compatibility
- Choose model size based on maximum sequence length in dataset
- Pre-embed large databases for repeated searches

## Typical Workflow

1. Pin the maintained TM-Vec fork and model/cache paths.
2. Build or obtain a versioned database.
3. Search queries with `tmvec search`.
4. Preserve the database checksum and filter thresholds with the results.
