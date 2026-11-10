# AGENTS.md

Guidance for AI coding agents (Claude Code, Codex CLI, Cursor, Copilot) working in this repository.

Related docs: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) (contributor workflow and validation commands), [docs/INSTALL.md](docs/INSTALL.md) (installation), [docs/routing.md](docs/routing.md) (router and catalog).

---

## Repository overview

Agents and skills covering bioinformatics pipelines, literature discovery, project evaluation, and data visualization. Runs under Claude Code and the Codex CLI. `catalog/catalog.json` is the countable source of truth for how many of each exist; do not restate the counts in prose.

Layout:
- `agents/` — agent definitions (markdown)
- `skills/` — skill directories; each has a `SKILL.md`
- `scripts/` — router, catalog builder, hook installer, validators, benchmark
- `tests/` — unit tests + routing benchmark
- `catalog/` — generated routing artifact (`catalog.json`)
- `docs/` — MkDocs site sources, routing model, benchmark baseline
- `Makefile` — the installer: install, catalog, hook, benchmark, uninstall, status, validate

Install: `make install` symlinks agents and skills into `~/.claude/` and `~/.codex/`.

The omics pipeline has one model-visible entry, the `omics-pipeline` skill. The stage skills it names are hidden (see Pipeline stage skills below). Manuscript prose, manuscript review, PDF conversion and claim-graph extraction are not part of this pack; agents name `academic-writing`, `stop-slop`, `nelli-paper-review`, `pdf-to-md` and `csag-extraction` in prose only, and no catalog or manifest lists them.

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

Omics work follows an explicit reasoning loop, not a linear pipeline. The rules have one home each; link to it and do not copy it into another skill, agent or doc:

- **Shared pipeline rules** (hypothesis register of at least five, reflection after each QC gate, literature search after the first register and after unexpected findings, the five comparative axes, the retry and driver-envelope rules, environment, scheduler): [skills/omics-pipeline/SKILL.md](skills/omics-pipeline/SKILL.md).
- **Discovery** (infer the group, build a literature-derived playbook, compare like with like, close with an interesting-findings table and the final report contents): `agents/omics-scientist.md`, Principles.
- **Per-axis detail** (marker categories, family copy number, conserved neighborhoods, Rfam models for the ncRNA census): the stage skills `bio-annotation`, `bio-protein-clustering-pangenome` and `bio-gene-calling`.

These guardrails apply to agent prompts, skill instructions, examples, and documentation added or edited in this repository.

---

## Skill Conventions

### Personal data

Never write a person's email address into skills, scripts, tests, docs, or commits; examples use `you@example.org`. Contact options for public APIs (Crossref `--email`, OpenAlex `--mailto`, NCBI `--email`) are flags, never environment variables, and stay unset unless the user gave an address for that purpose. A skill script sends a service key (`NCBI_API_KEY`, `ALTMETRIC_API_KEY`) only from the environment, sends an optional service such as Altmetric only on an explicit flag, and prints neither the key nor the address. `tests/test_no_personal_emails.py` fails on any other address in a tracked file.

### Tool versions

A version in a skill records what its commands were last checked against; it is not an install pin. The version rules and the tool-guide provenance lines are in [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md). `python3 scripts/check_tool_versions.py` is a maintenance report, never a CI gate.

### Figures

Every chart, figure, dashboard view, or web visual produced by a skill or agent follows `/beautiful-data-viz`.

### Directory structure

```
skills/
  {skill-name}/           # kebab-case directory name
    SKILL.md              # Required: skill definition with YAML frontmatter
    docs/                 # Optional: tool documentation
    examples/             # Optional: usage examples
    references/           # Optional: reference materials
    scripts/              # Optional: helper scripts
    agents/openai.yaml    # Codex metadata; required for a hidden stage skill
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

`scripts/validate-skills.py` enforces: the frontmatter `name` matches the directory name and is a valid kebab-case slug (≤64 chars); the description exists, stays ≤400 characters, and contains an explicit "use when" / "use for" / "trigger when" phrase; the descriptions of model-visible skills fit the 3,500-character repository-wide budget; the four required `##` sections are present and none is empty; the file stays ≤500 lines; and every relative Markdown link resolves on disk. Keep the description of a model-visible skill to 300 characters, with the object and the action in the first 60, because Codex shows only the start.

### Pipeline stage skills

A stage skill carries `disable-model-invocation: true` in its frontmatter and `policy.allow_implicit_invocation: false` in `agents/openai.yaml`. It keeps its directory, name, drivers and tests, because projects call its scripts by path. It opens with one line that sends the reader to `~/.agents/skills/omics-pipeline/SKILL.md` for the shared rules. The validator checks that each hidden skill has a row in the stage table of `skills/omics-pipeline/SKILL.md`, that every stage file the router names exists, and that the Codex policy file agrees.

### Context efficiency

Skills are loaded on demand. To minimize context usage:

- **Keep SKILL.md under 500 lines** — put detailed docs in subdirectories
- **Write specific descriptions** — the router scores them for skill activation
- **Use progressive disclosure** — reference `docs/`, `references/`, and `examples/` files
- **Link explicitly** — include full relative paths (e.g., `[Tool Docs](docs/tool-name.md)`); the validator flags broken links, and unlinked files are invisible to agents
- For supplementary tool/source guides, include the `Last verified`, `Tool version/release checked`, `Official docs/manual`, and `Release/source` provenance lines near the top; `scripts/validate-supplementary-docs.py` enforces them.
- Write citations so the DOI can be checked against what the prose claims: `- Tool: Surname et al. (YEAR) *Venue* https://doi.org/...`, or the multi-line `Surname A, Other B. (YEAR)` form. `scripts/validate-citations.py` compares the stated year and author surnames against the registered record, so a DOI swapped for another registered DOI fails. It cannot tell whether the paper supports the claim it is cited for; that still needs a human.

### Driver stdout contract

Workflow driver scripts (the `run_*.py` / `build_*_artifacts.py` entry points documented in the pipeline stage skills) print one JSON envelope as the last line of stdout when they finish. Tools launched under `--execute` may write to stdout first, so read the last line.

- Success: `{"ok": true, "skill": "<skill>", "out": "<abs dir>", "manifest": "<abs run_manifest.json>", "warnings": []}`. Drop `manifest` when the driver writes none (the pangenome driver and `--normalize-only` runs).
- Driver-detected failure: `{"ok": false, "skill": "<skill>", "error": {"code": "<exception class>", "message": "..."}}`, the same message on stderr, exit code 2.
- argparse usage errors keep their existing behavior.

---

## Agent Conventions

Agents are markdown files in `agents/` (kebab-case names): `omics-scientist.md`, `literature-expert.md`, `science-writer.md`.

The router reads one section of each agent file, `## Skills`, which holds one table with a row per skill. Preserve the heading and the column names:

| Column | Required | Meaning |
|---|---|---|
| `Skill` | yes | The skill name in backticks |
| `Use for` | yes | A short label that groups the agent's skills |
| `Phrases` | no | Quoted trigger phrases; never a bare generic word such as "write" or "review" |
| `After` | no | Skills, in backticks, that normally run first |

Agents also carry a `## Skill Lookup` section pointing at the installed router (pinned by `tests/test_skill_index.py`), plus persona, principles, communication style, and quality gates that are not parsed. A skill from another repository goes in prose, never in the table.

### Adding or modifying a skill or agent

1. Create or edit `skills/<name>/SKILL.md` (frontmatter `name` must match the directory) or `agents/<agent>.md`.
2. For a new skill, add one row to the `## Skills` table of the owning agent. For a new pipeline stage, also add its row to the stage table in `skills/omics-pipeline/SKILL.md` and hide it as described above.
3. Rebuild the catalog and run the gates ([docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) has the full list):

```bash
make build-catalog
make test
```

4. Add a routing benchmark row in `tests/routing_benchmark.yaml` when the skill should be discoverable from natural language.

CI fails when `catalog/catalog.json` is stale, so commit the rebuilt catalog with any agent or skill text change.

When adding skills or modifying agents, preserve the YAML frontmatter shape, the `## Skills` table the router parses, and the `name`-matches-directory invariant enforced by `tests/test_skill_index.py`.
