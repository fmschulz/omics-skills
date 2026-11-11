# omics-skills

omics-skills is a small skill pack for scientific work in Claude Code and the Codex CLI. It covers omics pipelines, literature search, public database records, notebooks and figures.

A skill is a directory with a `SKILL.md` file and optional references, scripts and templates. The pack holds twelve skills and one agent. It keeps what a current model cannot derive: house rules for running and reporting an analysis, tools the pack maintains, a hosted full-text literature corpus, and small tested helpers.

| Area | Skills cover |
|---|---|
| Omics pipeline | `omics-pipeline` holds the shared rules and one decision page each for read QC and mapping, assembly, binning, gene calling, phylogenomics and structure. Four stage skills add scripts for domain routing and taxonomy, annotation, viromics and interdomain HGT. |
| Project | Project layout, pinned environment, restartable drivers and provenance. |
| Literature and metadata | PMC and bioRxiv full-text search, DOI lookup, citation counts and public database records. |
| Reasoning | Hypothesis register and claim-against-evidence checks. |
| Visualization | Notebooks, figures and Plotly Dash dashboards, greyscale first. |

## Quick start

```bash
git clone https://github.com/fmschulz/omics-skills.git
cd omics-skills
make install
```

## Pages

| Goal | Page |
|---|---|
| Install the pack, or upgrade from 1.x | [Install](INSTALL.md) |
| Find a skill | [Skills](skills.md) |
| Use the literature agent | [Agent](agents.md) |
| See what the tests and validation cover | [Validation](biological-validation.md) |
| Look up default tools and versions | [Tooling](tooling-survey-2026.md) |
| Change a skill or cut a release | [Contributing](CONTRIBUTING.md) |

## Design principles

The skills tie a model to evidence. An analysis starts from an explicit hypothesis register, records its QC decisions, checks the literature for the organism or data type, compares like with like, and reports negative results as well as candidates.
