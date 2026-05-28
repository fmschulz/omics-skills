# omics-skills

`omics-skills` is a set of agent prompts and reusable skills for scientific work with Claude Code and the Codex CLI. It covers omics workflows, literature discovery, scientific writing, peer review, notebooks, dashboards, and publication figures.

The repository is deliberately simple. Agents are Markdown system prompts. Skills are Markdown directories with a `SKILL.md` contract and optional references, examples, scripts, or templates. A small router reads those files and recommends the right agent and skill order for a task.

## What Is Included

| Area | What the repository provides |
|---|---|
| Omics analysis | Read QC, mapping, assembly, binning, annotation, taxonomy triage, phylogenomics, viromics, pangenomes, structure annotation, and reporting. |
| Literature and metadata | PMC and bioRxiv search, arXiv search, DOI lookup, citation metadata, impact checks, and API documentation retrieval. |
| Writing and review | Manuscript drafting, response letters, proposal review, methods documentation, and rigorous review of AI scientist outputs. |
| Visualization | Reproducible notebooks, matplotlib/seaborn figures, and Plotly Dash dashboards. |

The current package contains four agents and 35 skills. The source files remain the source of truth; this documentation explains how to find and use them.

## Start Here

| Goal | Go to |
|---|---|
| Install the pack for Claude Code or Codex | [Getting Started](getting-started.md) |
| Pick the right agent | [Agents](agents.md) |
| Browse every skill | [Skills](skills.md) |
| Understand the router | [Routing](routing.md) |
| Add or maintain skills | [Development](development.md) |
| Contribute a change | [Contributing](CONTRIBUTING.md) |
| Review distribution notes | [Distribution](DISTRIBUTION.md) |
| Publish the documentation site | [GitHub Pages](github-pages.md) |

## Quick Example

Install the pack:

```bash
git clone https://github.com/fmschulz/omics-skills.git
cd omics-skills
make install
```

Ask the router which workflow fits a task:

```bash
python3 scripts/skill_index.py route "assemble a metagenome and recover MAGs"
```

Use the suggested agent and skills as the starting point. For installed checkouts, the same router is available through `~/.agents/omics-skills/skill_index.py`.

## Design Principles

The skills are meant to keep scientific agents grounded. Bioinformatics work starts with explicit hypotheses, records QC reflections, searches the literature for the relevant clade or data type, compares like with like, and reports both candidate discoveries and credible negative findings. Writing and review skills favor evidence strength, reproducibility, and clear limits over polished but unsupported claims.
