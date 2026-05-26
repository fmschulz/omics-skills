# Agents

Agents are Markdown system prompts. They define the role, the skill lookup policy, and the workflow decision tree for a broad class of tasks. They do not execute anything by themselves; Claude Code or Codex loads the prompt, then uses the router and the referenced skills.

## Agent Overview

| Agent | Use it for | Typical first skills |
|---|---|---|
| `omics-scientist` | Reads, assemblies, MAGs, annotations, taxonomy, phylogenomics, viral discovery, JGI data, and final biological interpretation. | `bio-reads-qc-mapping`, `bio-assembly-qc`, `tracking-taxonomy-updates`, `bio-annotation`, `bio-fasta-database-curator` |
| `literature-expert` | Literature discovery, preprint scans, DOI lookup, citation metadata cleanup, impact checks, structured claim/evidence extraction, and current API docs. | `polars-dovmed`, `arxiv-search`, `biorxiv-search`, `crossref-lookup`, `csag-extraction`, `get-api-docs` |
| `science-writer` | Manuscript drafting, section rewrites, rebuttals, proposal critique, methods documentation, multi-reviewer evaluation, and argument-graph extraction. | `scientific-writing`, `manuscript-review-council`, `proposal-review`, `bio-workflow-methods-docwriter`, `csag-extraction` |
| `dataviz-artist` | Scientific data inspection, reproducible notebooks, exploratory plots, publication figures, and dashboards. | `exploratory-data-analysis`, `notebooks`, `beautiful-data-viz`, `plotly-dashboard-skill` |

## Choosing an Agent

Use the router first when the task is not obvious:

```bash
python3 scripts/skill_index.py route "<task>"
```

Constrain the router to one agent when you already know the domain:

```bash
python3 scripts/skill_index.py route --agent omics-scientist "annotate viral contigs and compare relatives"
```

The output gives the selected agent, primary skills, supporting skills, suggested order, and file paths. Open the returned files before doing substantial work.

## Source Files

| Agent | Source |
|---|---|
| `omics-scientist` | [`agents/omics-scientist.md`](https://github.com/fmschulz/omics-skills/blob/main/agents/omics-scientist.md) |
| `literature-expert` | [`agents/literature-expert.md`](https://github.com/fmschulz/omics-skills/blob/main/agents/literature-expert.md) |
| `science-writer` | [`agents/science-writer.md`](https://github.com/fmschulz/omics-skills/blob/main/agents/science-writer.md) |
| `dataviz-artist` | [`agents/dataviz-artist.md`](https://github.com/fmschulz/omics-skills/blob/main/agents/dataviz-artist.md) |
