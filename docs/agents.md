# Agents

An agent is a Markdown system prompt. It sets a role, the skills to use, and a workflow decision tree. Claude Code or Codex loads the prompt; the agent runs nothing by itself.

| Agent | Use it for | Common first skills |
|---|---|---|
| [`omics-scientist`](https://github.com/fmschulz/omics-skills/blob/main/agents/omics-scientist.md) | Reads, assemblies, MAGs, annotation, taxonomy, phylogenomics, viral discovery, public database records, project setup and biological interpretation. | `bioinformatics-project`, `bio-reads-qc-mapping`, `bio-assembly-qc`, `tracking-taxonomy-updates`, `bio-annotation` |
| [`literature-expert`](https://github.com/fmschulz/omics-skills/blob/main/agents/literature-expert.md) | Literature and preprint search, DOI and citation metadata, citation impact, and claim and evidence extraction. | `polars-dovmed`, `arxiv-search`, `biorxiv-search`, `crossref-lookup`, `csag-extraction` |
| [`science-writer`](https://github.com/fmschulz/omics-skills/blob/main/agents/science-writer.md) | Manuscripts, revisions and response letters, proposal review, methods sections, multi-reviewer evaluation and argument graphs. | `scientific-writing`, `manuscript-review-council`, `proposal-review`, `bio-workflow-methods-docwriter`, `csag-extraction` |
| [`dataviz-artist`](https://github.com/fmschulz/omics-skills/blob/main/agents/dataviz-artist.md) | Data inspection, notebooks, exploratory plots, figures and dashboards, greyscale first. | `exploratory-data-analysis`, `notebooks`, `beautiful-data-viz`, `plotly-dashboard-skill` |

When the right agent is not obvious, ask the [router](routing.md). `--agent` limits the answer to one agent:

```bash
python3 scripts/skill_index.py route --agent omics-scientist "annotate viral contigs and compare relatives"
```
