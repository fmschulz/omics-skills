# IQ-TREE Usage Guide

Last verified: 2026-10-01
Tool version/release checked: IQ-TREE v3.1.4 (`iqtree3 -h` from bioconda; flags below checked against it)
Official docs/manual: https://iqtree.github.io/doc/
Release/source: https://github.com/iqtree/iqtree3/releases/tag/v3.1.4

## Official Documentation
- Main: https://iqtree.github.io/doc/
- Command Reference: https://iqtree.github.io/doc/Command-Reference
- Quickstart: https://iqtree.github.io/doc/Quickstart
- Tutorial: https://iqtree.github.io/doc/Tutorial
- IQ-TREE 3 source and releases: https://github.com/iqtree/iqtree3

## Installation

```bash
pixi add iqtree
iqtree3 --version
```

The bioconda `iqtree` package installs the `iqtree3` binary.

## Input/Output Formats

### Input
- PHYLIP, FASTA, or NEXUS alignments
- NEXUS or RAxML-style partition files for partitioned analyses

### Key Output Files
- `.treefile`: maximum-likelihood tree in Newick
- `.iqtree`: report with model selection and tree statistics
- `.log`: run log
- `.ckp.gz`: checkpoint for resuming
- `.contree`: UFBoot consensus tree (with `-B`)
- `.state`: ancestral states (with `--ancestral`)

With `-B` and `--alrt` together, internal labels in `.treefile` read `SH-aLRT/UFBoot` (for example `98.7/100`).

IQ-TREE 3 still accepts the IQ-TREE 1 spellings (`-bb`, `-nt`, `-alrt`, `-pre`); new commands should use the forms below.

## Key Command-Line Flags

### Essential Options
```bash
-s <alignment>          # Input alignment (required)
--seqtype <AA|DNA|CODON|...>   # Sequence type (auto-detected by default)
--prefix <prefix>       # Output file prefix
-T <n>|AUTO             # Threads (default 1); AUTO uses every core unless --threads-max is set
--seed <n>              # Random seed; set it for reproducible runs
--mem <n>G              # Maximum RAM
```

On shared nodes, set `-T` to the allocated CPU count rather than `AUTO`.

### Model Selection
```bash
-m TEST                 # Standard model selection, then tree inference
-m MFP                  # ModelFinder with FreeRate models, then tree inference
-m <MODEL>              # Fixed model, e.g. GTR+I+G, LG+G4, Q.pfam+R4
--mset <models>         # Restrict candidate models, e.g. WAG,LG,JTT
--msub <source>         # Amino-acid model source (nuclear, mitochondrial, chloroplast, viral)
--mfreq <list>          # Candidate state frequencies
--mrate <list>          # Candidate rate heterogeneity models
```

### Model Syntax
General form: `-m MODEL+Freq+Rate`.

- DNA models: JC, F81, K2P, HKY, TN, TNe, GTR, and others
- Protein models: LG, WAG, JTT, Q.pfam, Q.yeast, mtREV, cpREV, FLU, rtREV, VT, PMB, Blosum62, Dayhoff, and others
- Rate heterogeneity: `+I`, `+G[n]` (Gamma, 4 categories by default), `+R[n]` (FreeRate), `+I+G`, `+I+R`
- Mixtures: `MIX{m1,...,mK}`

### Branch Support
```bash
-B <n>                  # Ultrafast bootstrap (n >= 1000)
--bnni                  # Optimize UFBoot trees by NNI (reduces overestimation under model violation)
--bcor <x>              # UFBoot convergence threshold (default 0.99)
-b <n>                  # Standard nonparametric bootstrap
--alrt <n>              # SH-aLRT with n replicates
--abayes                # Approximate Bayes test
--lbp <n>               # Fast local bootstrap probabilities
```

### Tree Search
```bash
--fast                  # Fast search resembling FastTree
--nstop <n>             # Unsuccessful iterations before stopping (default 100)
--perturb <x>           # Perturbation strength for randomized NNI (default 0.5)
-g <constraint_tree>    # Topological constraint tree
-o <taxon>              # Outgroup for writing the .treefile
--redo                  # Ignore the checkpoint and overwrite outputs
--safe                  # Safe likelihood kernel against numerical underflow
```

### Partitioned Analysis
```bash
-p <file>               # Edge-linked partition model with proportional branch lengths
-q <file>               # Edge-linked partition model with equal branch lengths
-Q <file>               # Edge-unlinked partition model
-m MFP+MERGE            # ModelFinder plus partition merging
```

### Other Analyses
```bash
--pathogen              # CMAPLE search when sequence divergence is low
--ancestral             # Ancestral state reconstruction
--trees <file> --test <n> --test-au   # Tree topology tests (KH, SH, AU)
```

## Common Usage Examples

### Model selection with both support measures
```bash
iqtree3 -s alignment.faa -m MFP -B 1000 --alrt 1000 -T 8 --seed 1729
```

### Fixed model with ultrafast bootstrap
```bash
iqtree3 -s alignment.fna -m GTR+I+G -B 1000 -T 8 --seed 1729
```

### Partitioned concatenated analysis
```bash
iqtree3 -s concat.faa -p partitions.nex -m MFP+MERGE -B 1000 -T 8 --seed 1729
```

### Fast exploratory tree (fallback when VeryFastTree is unavailable)
```bash
iqtree3 -s alignment.faa -m LG+G4 --fast -T 8 --seed 1729
```

### Resume an interrupted run

Repeat the exact original command. IQ-TREE finds the matching `.ckp.gz` and resumes; `--redo` discards that progress.

### Ancestral state reconstruction
```bash
iqtree3 -s alignment.fna -m GTR+G --ancestral -T 8
```

### Topology test of candidate trees
```bash
iqtree3 -s alignment.faa -m LG+G4 --trees candidates.nwk --test 10000 --test-au -T 8
```

## Performance Tips

- Below about 2,000 sequences, run full ModelFinder (`-m MFP`) for final trees.
- For exploratory work at any size, use VeryFastTree first; `--fast` is the IQ-TREE fallback.
- `-m TEST` is faster than `-m MFP`; `--mset` restricts the candidate set further.
- For very large alignments, choose a model on a subsample and fix it with `-m`.
- Use `--mem` to cap memory and `-T` to match the CPU allocation.

## Quality Control Checks

### Model Selection
In the `.iqtree` report, check the BIC-selected model and how close the next candidates are.

### Branch Support
IQ-TREE's documentation suggests trusting a clade when SH-aLRT is 80 or more and UFBoot is 95 or more. Report both, and report weakly supported placements as uncertain.

### Tree Statistics
In the `.iqtree` report, check the log-likelihood, total tree length, the proportion of invariable sites, and the Gamma shape. Very long trees or extreme rate parameters can point to saturation or alignment problems; inspect the alignment before trusting such a tree.

## Version Information

Checked against IQ-TREE v3.1.4 on 2026-10-01; run `iqtree3 --version` to confirm the binary on PATH.
