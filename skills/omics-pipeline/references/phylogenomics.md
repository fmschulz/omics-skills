# Phylogenomics

**Last verified:** 2026-10-01
**Tool version/release checked:** IQ-TREE v3.1.4; VeryFastTree v4.0.5; ETE Toolkit 4.4.0; MAFFT v7.526; trimAl v1.5.1; ClipKIT 2.14.0
**Official docs/manual:** https://iqtree.github.io/doc/ ; https://github.com/citiususc/veryfasttree ; https://etetoolkit.github.io/ete/
**Release/source:** https://github.com/iqtree/iqtree3/releases/tag/v3.1.4 ; https://github.com/citiususc/veryfasttree/releases/tag/v4.0.5 ; https://github.com/etetoolkit/ete/releases/tag/4.4.0

Shared rules (hypotheses, thresholds as results, environment, scheduler, threads): see the shared rules in [../SKILL.md](../SKILL.md). This page holds only the phylogenomics decisions.

## Use when

You need marker alignments, ML trees, support values, or the closest relatives of a query genome. Inputs: unaligned marker FASTA files (protein or nucleotide, one per marker), reference files with SHA-256 checksums, and the literature-derived playbook for the inferred group (markers, reference sampling, rooting, placement).

## Tool choice

| Case | Default | Use the alternative when |
| --- | --- | --- |
| Exploratory placement, reference screening, benchmark iterations, time-bounded runs | VeryFastTree, any size | - |
| Final tree, up to about 2,000 taxa | IQ-TREE 3 (`iqtree3`) | - |
| More than about 2,000 taxa, or memory or runtime unclear | VeryFastTree | add `-disk-computing` when RAM runs short; add `-fastest` only when runtime forces it |
| Exploratory tree without VeryFastTree | `iqtree3 --fast` | the project requires IQ-TREE output; record the fallback |
| Alignment | MAFFT `--auto` | - |
| Trimming | trimAl `-automated1` | ClipKIT when phylogenetically informed trimming is preferred |
| Tree handling (root, prune, collapse, distances, annotation) | ETE 4 (`ete4`, replaces `ete3`) | - |

## Rules a model would not guess

- Normalize all support to a 0-1 scale and record the scale. VeryFastTree reports 0-1. IQ-TREE reports SH-aLRT and UFBoot on 0-100, as one label `98.7/100` (SH-aLRT/UFBoot). Keep them as separate `sh_alrt` and `ufboot` rows. Mixed 0-1 and 0-100 values within one support type are an error.
- Record a fixed positive seed and the thread count with every tree.
- Check every reference file against its SHA-256 before any alignment runs.
- ETE's default Newick parser rejects IQ-TREE `SH-aLRT/UFBoot` labels. Load with `parser=1` and split the label into properties.
- Read support labels before rerooting. A label stored as a node name stays on its node and can end up on the wrong side of a rerooted branch.
- After midpoint rooting with ete4, a node's support can be `None`. Guard before comparing.
- On shared nodes, pass the allocated CPU count to `-T`, not `AUTO`. Keep VeryFastTree's default deterministic mode (`-threads-mode 1`) for reproducible trees.
- Interrupted IQ-TREE run: repeat the exact original command and it resumes from the checkpoint. `--redo` discards that progress.
- Support thresholds are project choices; state the one you use. IQ-TREE documentation suggests SH-aLRT 80 or more and UFBoot 95 or more. VeryFastTree: many studies treat 0.7 as moderate and 0.9 as strong.
- Separate well-supported nearest relatives from weak placements in `closest_relatives.tsv`.

## Commands

```bash
# per marker; $FASTA is the unaligned marker file, $M the marker id, $OUT/$M the marker directory
mafft --auto --thread $THREADS $FASTA > $OUT/$M/alignment.fasta
trimal -in $OUT/$M/alignment.fasta -out $OUT/$M/trimmed.fasta -automated1

# final tree (writes $OUT/$M/trimmed.fasta.treefile)
iqtree3 -s $OUT/$M/trimmed.fasta -m MFP -B 1000 --alrt 1000 --seed $SEED -T $THREADS

# exploratory or large tree; add -nt for nucleotide markers
VeryFastTree -boot 1000 -seed $SEED -threads $THREADS $OUT/$M/trimmed.fasta > $OUT/$M/tree.nwk
```

Parse an IQ-TREE tree and guard a rooted VeryFastTree tree with ete4:

```python
from ete4 import Tree

t = Tree(open("trimmed.fasta.treefile"), parser=1)  # labels arrive as node names
for node in t.traverse():
    if not node.is_leaf and "/" in (node.name or ""):
        sh_alrt, ufboot = (float(v) for v in node.name.split("/"))
        node.add_props(sh_alrt=sh_alrt, ufboot=ufboot)

v = Tree(open("tree.nwk"))
v.set_outgroup(v.get_midpoint_outgroup())
for node in list(v.traverse()):
    if not node.is_leaf and not node.is_root and node.support is not None and node.support < 0.70:
        node.delete()  # weak node collapsed; the 0.70 cutoff is a project choice
```

## QC gates to record

- Reference checksums matched; the seed is positive and recorded; the thread count is recorded.
- Internal support is exported on a documented 0-1 scale without mixing IQ-TREE and VeryFastTree conventions.
- Marker and reference choices are justified against the literature-derived playbook.
- Every input sequence appears in the tree. A very long branch points to an alignment error or a contaminant; inspect the alignment first.
- IQ-TREE: record the BIC-selected model and how close the next candidates are, the log-likelihood, tree length, proportion of invariable sites and Gamma shape. Extreme values can mean saturation.
- Closest relatives are reported with support and distance, or the uncertainty is stated. An unmet support threshold is a result, not a reason to retune.
- `relatives_manifest.tsv` is populated and the genome and proteome files exist, or each failed download has a reason.

## Outputs

The agent writes these. A restartable project driver follows the `bioinformatics-project` skill: write to `.tmp`, check, move, and reuse a stage only when its output is non-empty and its `.done` marker exists. Record seed, tree tool, threads, inputs and every command in a run manifest.

Under `results/phylogenomics/`:
- `trees/{marker_id}/alignment.fasta`, `trimmed.fasta`, the tree (`tree.nwk` or `trimmed.fasta.treefile` with its IQ-TREE companion files) and `support.tsv`
- `support.tsv` columns: `node_index support_type raw_support normalized_support` (`support_type` is `support`, `sh_alrt` or `ufboot`; `node_index` counts internal labels in file order)
- `closest_relatives.tsv`: support, distance, taxonomy, reference accession, uncertainty note
- `relatives/{accession}/genome.fna` and `proteins.faa`, plus `relatives_manifest.tsv` (accession, source database, taxonomy, genome size, gene count, reason for inclusion). The downstream comparative axes need this table.
- `phylo_report.md` and `logs/`

Pass well-supported relatives, or a documented broader set, to the annotation stage and the comparative axes (shared rule 3).
