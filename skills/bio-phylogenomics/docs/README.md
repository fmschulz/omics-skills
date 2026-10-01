# Bio-Phylogenomics Tool Documentation

Guides for tree inference and tree post-processing tools.

**Last verified:** 2026-10-01
**Tool version/release checked:** IQ-TREE v3.1.4; VeryFastTree v4.0.5; ETE Toolkit 4.4.0; MAFFT v7.526; trimAl v1.5.1; ClipKIT 2.14.0
**Official docs/manual:** See linked per-tool guides in this directory.
**Release/source:** See linked per-tool guides in this directory.

The skill driver was run end to end with these versions (MAFFT, trimAl, then VeryFastTree or IQ-TREE) on a six-sequence test marker.

## Documentation Files

### Tree inference

- **[iqtree.md](iqtree.md)**: IQ-TREE v3.1.4 (https://github.com/iqtree/iqtree3/releases/tag/v3.1.4)
  - Maximum likelihood with ModelFinder, mixture models, and partitions
  - UFBoot, SH-aLRT, and standard bootstrap
  - Default for final trees up to about 2,000 taxa
- **[veryfasttree.md](veryfasttree.md)**: VeryFastTree v4.0.5 (https://github.com/citiususc/veryfasttree/releases/tag/v4.0.5)
  - FastTree-2 algorithm with parallel and vectorized code and the same command line
  - Default for exploratory trees at any size and for more than about 2,000 taxa
  - Disk computing for alignments that do not fit in RAM

### Tree post-processing

- **[ete-toolkit.md](ete-toolkit.md)**: ETE v4.4.0 (`ete4`, https://github.com/etetoolkit/ete/releases/tag/4.4.0)
  - Python API for rooting, pruning, support filtering, distances, annotation, and topology comparison
  - `ete4` replaces `ete3`; use `from ete4 import Tree`
  - IQ-TREE `SH-aLRT/UFBoot` labels need `parser=1`

## Tool Selection

| Objective and size | Tool | Notes |
|--------------------|------|-------|
| Exploratory, any size | VeryFastTree | Placement, screening, benchmark iterations, time-bounded work. `-boot 1000` gives local support. |
| Final, up to ~2,000 taxa | IQ-TREE 3 | `-m MFP -B 1000 --alrt 1000 --seed <n>` |
| Exploratory fallback | `iqtree3 --fast` | Only when VeryFastTree is unavailable or IQ-TREE output is required. |
| More than ~2,000 taxa | VeryFastTree | Add `-disk-computing` when memory runs short. |

Use ETE for post-processing: statistics, rooting, pruning, collapsing weak nodes, annotation, Robinson-Foulds comparison, and subtree extraction.

## Typical Workflows

### Final tree
```bash
iqtree3 -s alignment.faa -m MFP -B 1000 --alrt 1000 -T 8 --seed 1729
```

```python
from ete4 import Tree

t = Tree(open('alignment.faa.treefile'), parser=1)  # SH-aLRT/UFBoot labels as names
for node in t.traverse():
    if not node.is_leaf and '/' in (node.name or ''):
        sh_alrt, ufboot = (float(value) for value in node.name.split('/'))
        node.add_props(sh_alrt=sh_alrt, ufboot=ufboot)
```

### Exploratory tree
```bash
VeryFastTree -boot 1000 -seed 1729 -threads 8 alignment.faa > tree.nwk
```

```python
from ete4 import Tree

t = Tree(open('tree.nwk'))
t.set_outgroup(t.get_midpoint_outgroup())
for node in list(t.traverse()):
    # VeryFastTree support is on a 0-1 scale; the root has no support value.
    if not node.is_leaf and not node.is_root and node.support < 0.70:
        node.delete()
t.write(outfile='tree.filtered.nwk')
```

## Figures

Draw trees in greyscale by default. Use color only when it encodes information the reader must tell apart, such as the query versus references or a few named clades, choose a colorblind-safe palette, and repeat the encoding in label text, shape, or line style.

## Installation

```bash
pixi add iqtree veryfasttree mafft trimal "ete4=4.4.0"
```

## Key Differences

| Feature | IQ-TREE 3 | VeryFastTree |
|---------|-----------|--------------|
| Models | ModelFinder over many DNA, protein, mixture, and partition models | JTT (default), LG, or WAG for proteins; Jukes-Cantor (default) or GTR for nucleotides; CAT rates, optional Gamma rescaling |
| Support | UFBoot, SH-aLRT, aBayes, standard bootstrap | Local support from resampling |
| Typical use | Final trees | Exploratory, large, or time-bounded trees |

## Official Documentation Sources

- IQ-TREE: https://iqtree.github.io/doc/ and https://iqtree.github.io/doc/Command-Reference
- VeryFastTree: https://github.com/citiususc/veryfasttree
- ETE Toolkit: https://etetoolkit.github.io/ete/

## Additional Resources

- Skill specification: [../SKILL.md](../SKILL.md)
