# AGENTS.md

Guidance for AI coding agents (Claude Code, Codex CLI, Cursor, Copilot) working in this repository.

Related docs: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) (contributor workflow and validation commands), [docs/INSTALL.md](docs/INSTALL.md) (installation).

---

## Repository overview

One agent and a small set of skills covering omics pipelines, literature discovery, notebooks, and data visualization. Runs under Claude Code and the Codex CLI.

Layout:
- `agents/` — the agent definition (markdown)
- `skills/` — skill directories; each has a `SKILL.md`
- `scripts/` — installer helpers and validators
- `tests/` — unit tests
- `docs/` — MkDocs site sources
- `Makefile` — the installer: install, uninstall, status, validate, test

Install: `make install` links the skills into `~/.agents/skills`, links the Claude agent, and renders the Codex agent.

The omics pipeline has one model-visible entry, the `omics-pipeline` skill. It holds the shared rules and one decision page per stage under `references/`. A stage that keeps a driver is a hidden stage skill (see Pipeline stages below). Manuscript prose, manuscript review, proposal review, evaluation of AI-scientist output, PDF conversion and claim-graph extraction are not part of this pack; the agent and the skills name such skills (`academic-writing`, `stop-slop`, `nelli-paper-review`, `proposal-review`, `ai-scientist-evaluator`, `pdf-to-md`, `csag-extraction`) in prose only, and no manifest lists them.

---

## Scientific Workflow Guardrails

Omics work follows an explicit reasoning loop, not a linear pipeline. The rules have one home each; link to it and do not copy it into another skill, agent or doc:

- **Shared pipeline rules** (hypothesis register of at least five, reflection after each QC gate, the five comparative axes, the retry and driver-envelope rules, environment, scheduler): [skills/omics-pipeline/SKILL.md](skills/omics-pipeline/SKILL.md), rules 1 to 7.
- **Discovery, literature and reporting** (infer the group, take methods and comparison sets from the literature, compare like with like, close with an interesting-findings table and the final report contents; when to search and what to record): the same file, rules 8 and 9.
- **Per-axis detail** (marker categories and family copy number; Rfam models for the ncRNA census): the stage skill `bio-annotation`, and the pages [gene-calling.md](skills/omics-pipeline/references/gene-calling.md) and [infernal.md](skills/omics-pipeline/references/infernal.md).

These guardrails apply to the agent prompt, skill instructions, examples, and documentation added or edited in this repository.

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

### Pipeline stages

A stage is a skill only when it ships scripts that projects call by path: `tracking-taxonomy-updates`, `bio-annotation`, `bio-viromics` and `bio-interdomain-hgt`. Every other stage is one decision page under `skills/omics-pipeline/references/`, with the sections `Use when`, `Tool choice`, `Rules a model would not guess`, `Commands`, `QC gates to record` and `Outputs`, and the provenance lines of a tool guide. A page states what a current model would get wrong; it is not a tool manual. Add a tool note beside the pages only for a tool that models know poorly.

A stage skill carries `disable-model-invocation: true` in its frontmatter and `policy.allow_implicit_invocation: false` in `agents/openai.yaml`. Projects call its scripts by path, so its directory, name and driver stay stable. It opens with one line that sends the reader to `~/.agents/skills/omics-pipeline/SKILL.md` for the shared rules. The validator checks that each hidden skill has a row in the stage-skill table of `skills/omics-pipeline/SKILL.md`, that every stage skill `omics-pipeline` names exists, and that the Codex policy file agrees.

### Context efficiency

Skills are loaded on demand. To minimize context usage:

- **Keep SKILL.md under 500 lines** — put detailed docs in subdirectories
- **Write specific descriptions** — the model selects a skill by its description
- **Use progressive disclosure** — reference `docs/`, `references/`, and `examples/` files
- **Link explicitly** — include full relative paths (e.g., `[Tool Docs](docs/tool-name.md)`); the validator flags broken links, and unlinked files are invisible to agents
- For supplementary tool/source guides, include the `Last verified`, `Tool version/release checked`, `Official docs/manual`, and `Release/source` provenance lines near the top; `scripts/validate-supplementary-docs.py` enforces them.
- Write citations so the DOI can be checked against what the prose claims: `- Tool: Surname et al. (YEAR) *Venue* https://doi.org/...`, or the multi-line `Surname A, Other B. (YEAR)` form. `scripts/validate-citations.py` compares the stated year and author surnames against the registered record (cached in `scripts/citation-cache.json`), so a DOI swapped for another registered DOI fails. It cannot tell whether the paper supports the claim it is cited for; that still needs a human.

### Driver stdout contract

The three stage drivers (`build_annotation_artifacts.py`, `build_viromics_evidence.py`, `run_hgt_evidence.py`) print one JSON envelope as the last line of stdout when they finish. Tools launched under `--execute` may write to stdout first, so read the last line.

- Success: `{"ok": true, "skill": "<skill>", "out": "<abs dir>", "manifest": "<abs run_manifest.json>", "warnings": []}`.
- Driver-detected failure: `{"ok": false, "skill": "<skill>", "error": {"code": "<exception class>", "message": "..."}}`, the same message on stderr, exit code 2.
- argparse usage errors keep their existing behavior.

---

## Agent Conventions

The pack ships one agent, `agents/literature-expert.md`. An agent is a Markdown file in `agents/` with a kebab-case name. Add an agent only for a role that needs its own tool set or model; rules that every session needs belong in a skill.

An agent lists its skills in one `## Skills` table with the columns `Skill` (the skill name in backticks) and `Use for`. A skill from another repository goes in prose, never in the table. An agent also carries persona, principles, communication style, and quality gates.

### Adding or modifying a skill or agent

1. Create or edit `skills/<name>/SKILL.md` (frontmatter `name` must match the directory) or `agents/<agent>.md`.
2. For a skill the agent uses, add one row to its `## Skills` table. For a new pipeline stage, add a page and its row to the stage-page table in `skills/omics-pipeline/SKILL.md`; when the stage ships a driver, make it a hidden stage skill with a row in the stage-skill table instead. Add a new agent to `AGENT_FILES` in the `Makefile`.
3. Run the gate ([docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) has the full list):

```bash
make test
```

When adding skills or modifying the agent, preserve the YAML frontmatter shape, the `## Skills` table, and the name-matches-directory rule that `scripts/validate-skills.py` enforces. When a skill or agent leaves the pack, add its name to `RETIRED_SKILLS` or `MOVED_SKILLS` in `scripts/prune_removed_skills.py`, or to `RETIRED_AGENTS` in `scripts/prune_removed_agents.py`, so the installer removes its link.
