# omics-skills

omics-skills is a set of agent prompts and skills for scientific work in Claude Code and the Codex CLI. It covers omics workflows, literature search, scientific writing and review, notebooks, dashboards and figures.

Agents are Markdown system prompts. A skill is a directory with a `SKILL.md` file and optional references, examples, scripts and templates. A router reads both and recommends an agent and an order of skills for a task. The pack has four agents and 34 skills; the generated `catalog/catalog.json` is the authoritative list.

| Area | Skills cover |
|---|---|
| Omics analysis | Read QC and mapping, assembly, binning, gene calling, annotation, taxonomy, phylogenomics, viromics, pangenomes, protein structure, statistics and reports. |
| Literature and metadata | PMC and bioRxiv full-text search, arXiv and bioRxiv metadata search, DOI lookup, public database records and citation impact. |
| Writing and review | Manuscripts, response letters, proposal review, methods sections and review of AI-scientist output. |
| Visualization | Notebooks, figures and Plotly Dash dashboards, greyscale first. |

## Quick start

```bash
git clone https://github.com/fmschulz/omics-skills.git
cd omics-skills
make install
python3 scripts/skill_index.py route "assemble a metagenome and recover MAGs"
```

## Pages

| Goal | Page |
|---|---|
| Install the pack and start an agent | [Install](INSTALL.md) |
| Pick an agent | [Agents](agents.md) |
| Find a skill | [Skills](skills.md) |
| See how a task is routed | [Routing](routing.md) |
| See what the tests and validation cover | [Validation](biological-validation.md) |
| Look up default tools and versions | [Tooling](tooling-survey-2026.md) |
| Change a skill or cut a release | [Contributing](CONTRIBUTING.md) |

## Design principles

The skills tie agents to evidence. An analysis starts from an explicit hypothesis, records its QC decisions, checks the literature for the organism or data type, compares like with like, and reports negative results as well as candidates. The writing and review skills put evidence, reproducibility and stated limits ahead of fluent but unsupported claims.
