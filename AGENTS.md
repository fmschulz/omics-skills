# AGENTS.md

Guidance for AI coding agents (Claude Code, Codex CLI, Cursor, Copilot) working in this repository.

Related docs: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) (contributor workflow), [docs/development.md](docs/development.md) (validation commands), [docs/INSTALL.md](docs/INSTALL.md) (installation).

---

## Repository overview

4 agents and 34 skills covering bioinformatics, literature discovery, scientific writing, and data visualization. Runs under Claude Code and the Codex CLI.

Layout:
- `agents/` — 4 agent definitions (markdown)
- `skills/` — skill directories; each has a `SKILL.md`
- `scripts/` — router, catalog builder, hook, installer, benchmark
- `tests/` — unit tests + routing benchmark
- `catalog/` — generated routing artifact (`catalog.json`)
- `docs/` — MkDocs site sources, routing model, benchmark baseline
- `Makefile` — install, catalog, hook, benchmark, uninstall targets

Install: `make install` symlinks agents and skills into `~/.claude/` and `~/.codex/`.

---

## Default Workflow Selection

When working in this repository without a specialized agent prompt, do not choose skills ad hoc.

Start with the catalog:

```bash
python3 scripts/skill_index.py route "<task>"
```

Use the returned agent, primary skills, and suggested order as the default workflow. Then open the referenced agent file in `agents/` and the referenced `SKILL.md` files before proceeding. Only deviate from the returned path when the request clearly falls outside the suggested workflow.

For installed environments outside the repository checkout, use:

```bash
python3 ~/.agents/omics-skills/skill_index.py route "<task>"
```

---

## Scientific Workflow Guardrails

For omics or scientific project work, agents must maintain an explicit reasoning loop instead of treating analysis steps as a linear pipeline.

1. **Hypothesis register**: before the first analysis step, create at least 5 distinct working hypotheses or explanations. Include technical artifacts and null explanations alongside biological mechanisms. If fewer than 5 are plausible, state why and add discriminating negative controls or failure modes.
2. **Intermediate reflection**: after each major intermediate result or QC gate, write a short reflection covering what was observed, whether the result passed QC, which hypotheses gained or lost support, what alternative explanations remain, and the next discriminating check.
3. **Literature context**: after the initial hypothesis register and after any unexpected, central, or final finding, run an additional literature search using `polars-dovmed` or another appropriate literature-search skill. Use broad synonym-aware queries, summarize the relevant evidence with DOI/PMCID when available, and state whether the literature supports, contradicts, or narrows each leading hypothesis.
4. **Hypothesis revision**: revise and rank the hypothesis register as evidence accumulates. Do not silently discard hypotheses; mark them as supported, weakened, ruled out, or unresolved with the evidence that changed the status. Keep at least 5 active hypotheses while the project is exploratory; generate replacements when hypotheses are ruled out.
5. **Final synthesis**: final reports must include hypotheses considered, intermediate reflections, literature context, revised hypothesis ranking, and the next experiments or analyses that would best separate remaining alternatives.

These guardrails apply to agent prompts, skill instructions, examples, and documentation added or edited in this repository.

---

## Literature-Derived Discovery Guardrails

Omics agents must actively ask what is biologically interesting in the data. Do not stop at "workflow completed", "annotation complete", or "QC passed" when the user has provided genomes, contigs, MAGs, viral genomes, proteins, or annotations.

1. **Infer the biological context first**: use the available taxonomy, marker genes, genome statistics, sequence similarity, and QC evidence to infer the likely organism, virus group, sample context, and closest plausible references.
2. **Build a literature-derived analysis playbook**: before deciding what is "interesting", search the relevant literature for that inferred group and summarize what scientists typically analyze, which comparison sets they use, which features/outliers they report, and which tools or markers are considered appropriate. Prefer review papers, recent primary studies, and benchmark/tool papers for the same clade or data type.
3. **Choose methods from that playbook**: select comparative, phylogenetic, annotation, structural, statistical, and visualization analyses because they match the literature and the data, not because a fixed global checklist says so. Document why each chosen analysis is appropriate and which plausible analyses were skipped.
4. **Compare like with like**: identify close relatives or relevant reference sets using literature-supported methods for the inferred group. For example, do not apply a phage-oriented clustering workflow to NCLDV-style giant viruses unless the literature supports it for that case.
5. **Search for outliers and candidate discoveries**: compare query results to the literature-derived expectations and reference set. Report candidate discoveries, unusual absences, expansions, contractions, compositional outliers, topology outliers, annotation conflicts, and high-value unknowns only after separating them from conserved lineage features and likely artifacts.
6. **Interesting-findings table**: every exploratory analysis report must include a table of candidate discoveries with evidence, confidence, comparison baseline, literature context, and follow-up tests. If nothing interesting is found, state the negative finding and the checks that make it credible.

These requirements apply to `omics-scientist` and to bioinformatics skills that produce annotations, viral calls, phylogenies, pangenomes, or final reports.

---

## Comparative Discovery Axes

When close relatives or a literature-supported reference set are available, agents must run the query against ALL of the following structural axes before declaring the analysis complete. The *categories* within each axis (which markers count, which families matter, which neighborhoods are diagnostic) are inferred from the literature for the inferred group — they are not hardcoded. The axes themselves are mandatory; skipping one requires a written reason.

1. **Genome-property frontier**: place each query along the distribution of close relatives and group-level extremes reported in the literature for genome size, gene count, coding density, GC content, and any other group-relevant property. State where each query sits (median, tail, record-class) and cite the literature that defines the group's known range.
2. **Marker-gene census**: for the inferred group, enumerate the marker and machinery categories the literature treats as diagnostic (e.g., for nucleocytoplasmic large DNA viruses: replication, transcription, translation-related, packaging, capsid, chromatin/structural; for prokaryotes: ribosomal proteins, RNA polymerase, single-copy core). For each query and each relative, report presence/absence and copy number per category in a side-by-side table. Negative findings (expected marker absent) are first-class results.
3. **Per-family copy-number (expansion / contraction)**: build a Pfam/InterPro/orthogroup × genome matrix covering queries and relatives. Flag query-specific families, missing-expected families, expansions (query copies >> relative median), and contractions. Rank by absolute and fold differences.
4. **Synteny and conserved neighborhoods**: identify conserved gene neighborhoods (≥2 collinear orthologs in ≥2 relatives) and compare intergenic spacing, gene order, and local copy number between query and relatives. Flag conserved pairs, broken synteny, and unusual spacing or expansions.
5. **Non-coding RNA census**: explicitly screen each assembly for tRNA, rRNA, and other ncRNA classes appropriate to the inferred group, using `tRNAscan-SE` for tRNAs and Infernal `cmsearch` against domain-appropriate Rfam covariance models (bacterial RF00177/RF02541/RF00001; archaeal RF01959/RF02540/RF00001; eukaryotic RF01960/RF02543/RF00002/RF00001). Report counts per class per genome and per relative. A credible negative (e.g., "Infernal `cmsearch --cut_ga` finds no rRNA at default thresholds; relaxed thresholds also fail") is a required result when nothing is found — silence is not acceptable.

Each axis must yield (a) a persisted comparison artifact (TSV/parquet) and (b) a short interpretation linking the result to the hypothesis register and the literature-derived playbook. The interesting-findings table must roll up signals across these axes and identify the comparison baseline used.

---

## Skill Conventions

### Directory structure

```
skills/
  {skill-name}/           # kebab-case directory name
    SKILL.md              # Required: skill definition with YAML frontmatter
    docs/                 # Optional: tool documentation
    examples/             # Optional: usage examples
    references/           # Optional: reference materials
    scripts/              # Optional: helper scripts
    requirements.txt      # Optional: Python dependencies
```

### SKILL.md format

```markdown
---
name: skill-name
description: One sentence describing what this skill does. Include when to use it (e.g., "Use when processing raw sequencing reads").
---

# Skill Title

Brief overview of what the skill does.

## Instructions
## Input Requirements
## Output
## Quality Gates
```

Those four `##` sections are required and each must carry content. `## Quick Reference`, `## Examples`, `## Troubleshooting`, and `## Non-Goals` are optional: add one when it says something the required sections do not.

`scripts/validate-skills.py` enforces: the frontmatter `name` matches the directory name and is a valid kebab-case slug (≤64 chars); the description exists, stays ≤400 characters, contains an explicit "use when" / "use for" / "trigger when" phrase, and fits the 6500-character repository-wide description budget; the four required `##` sections are present and none is empty; the file stays ≤500 lines; and every relative Markdown link resolves on disk.

### Context efficiency

Skills are loaded on demand. To minimize context usage:

- **Keep SKILL.md under 500 lines** — put detailed docs in subdirectories
- **Write specific descriptions** — the router scores them for skill activation
- **Use progressive disclosure** — reference `docs/`, `references/`, and `examples/` files
- **Link explicitly** — include full relative paths (e.g., `[Tool Docs](docs/tool-name.md)`); the validator flags broken links, and unlinked files are invisible to agents
- For supplementary tool/source guides, include the `Last verified`, `Tool version/release checked`, `Official docs/manual`, and `Release/source` provenance lines near the top; `scripts/validate-supplementary-docs.py` enforces them.

### Driver stdout contract

Workflow driver scripts (the `run_*.py` / `build_*_artifacts.py` entry points documented in the bio-* skills) print one JSON envelope as the last line of stdout when they finish. Tools launched under `--execute` may write to stdout first, so read the last line.

- Success: `{"ok": true, "skill": "<skill>", "out": "<abs dir>", "manifest": "<abs run_manifest.json>", "warnings": []}`. Drop `manifest` when the driver writes none (the pangenome driver and `--normalize-only` runs).
- Driver-detected failure: `{"ok": false, "skill": "<skill>", "error": {"code": "<exception class>", "message": "..."}}`, the same message on stderr, exit code 2.
- argparse usage errors keep their existing behavior.

---

## Agent Conventions

Agents are markdown files in `agents/` (kebab-case names): `omics-scientist.md`, `literature-expert.md`, `science-writer.md`, `dataviz-artist.md`.

The router parses three sections of each agent file, so preserve their exact headings and formats:

- **`## Mandatory Skill Usage`** — `### Category` subsections whose `/skill-name` references assign skills to the agent
- **`## Workflow Decision Tree`** — the first fenced code block; `├─`/`└─` branches with `/skill-name` references become workflow edges
- **`## Task Recognition Patterns`** — `- **"phrase", "phrase"** → \`/skill-name\`` lines become routing trigger phrases

Agents also carry a `## Skill Lookup` section pointing at the installed router (pinned by `tests/test_skill_index.py`), plus persona, core principles, communication style, and quality gates that are not parsed.

### Adding or modifying a skill or agent

1. Create or edit `skills/<name>/SKILL.md` (frontmatter `name` must match the directory) or `agents/<agent>.md`.
2. For new skills, add the skill to the owning agent's `Mandatory Skill Usage`, `Workflow Decision Tree`, and `Task Recognition Patterns`.
3. Rebuild the catalog and run the gates ([docs/development.md](docs/development.md) has the full list):

```bash
python3 scripts/skill_index.py build
python3 scripts/validate-skills.py
uv run --no-project --with pytest --with requests pytest -q
make benchmark
```

4. Add a routing benchmark row in `tests/routing_benchmark.yaml` when the skill should be discoverable from natural language.

CI fails when `catalog/catalog.json` is stale, so commit the rebuilt catalog with any agent or skill text change.

---

When adding skills or modifying agents, preserve the YAML frontmatter shape, the `Mandatory Skill Usage` / `Task Recognition Patterns` / `Workflow Decision Tree` sections the router parses, and the `name`-matches-directory invariant enforced by `tests/test_skill_index.py`.
