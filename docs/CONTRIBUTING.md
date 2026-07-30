# Contributing to Omics Skills

This guide covers the contributor workflow. Structural conventions (skill layout, SKILL.md format, validator rules, router-parsed agent sections) live in [AGENTS.md](https://github.com/fmschulz/omics-skills/blob/main/AGENTS.md); validation commands live in [Development](development.md).

## Setup

You need Git, Python 3, [uv](https://docs.astral.sh/uv/), and Claude Code or the Codex CLI.

```bash
git clone https://github.com/yourusername/omics-skills.git
cd omics-skills
git checkout -b feature/your-feature-name
make install        # symlink install, so edits apply immediately
```

## Adding a Skill

1. Create `skills/your-skill-name/SKILL.md` following the format and naming rules in AGENTS.md. Put long tool notes, examples, and reference material in `docs/`, `examples/`, or `references/` subdirectories and link them from `SKILL.md` with relative paths.
2. Register the skill in the owning agent file under `Mandatory Skill Usage`, the `Workflow Decision Tree`, and `Task Recognition Patterns`.
3. Rebuild the catalog: `python3 scripts/skill_index.py build`. Commit the regenerated `catalog/catalog.json` — CI rejects a stale catalog.
4. Add a routing case to `tests/routing_benchmark.yaml` when the skill should be discoverable from natural language, then refresh `docs/routing_baseline.json` only after reviewing the benchmark delta.

## Modifying Skills or Agents

Edit the source file, keep the frontmatter and router-parsed sections intact, rebuild the catalog, and rerun the gates. Symlinked installs pick up edits immediately; Codex agent TOML must be re-rendered with `make install-codex-agents` after agent prompt changes.

## Testing Your Changes

Run the same gates CI runs:

```bash
python3 scripts/validate-skills.py
python3 scripts/validate-supplementary-docs.py
python3 scripts/skill_index.py build --repo . --out catalog && git diff --exit-code -- catalog/
uv run --no-project --with pytest --with requests pytest -q
make benchmark
uvx --from mkdocs --with 'mkdocs-material==9.5.*' --with pymdown-extensions mkdocs build --strict
```

For installer-affecting changes, also run `make install`, `make status`, and `make validate`, and exercise the changed behavior in a live Claude Code or Codex session.

## Submitting Changes

- Confirm the gates above pass and documentation (`README.md`, `docs/`) reflects any behavior change.
- Commit with a conventional message, e.g. `feat(skills): add your-skill-name`.
- Push the branch and open a pull request describing the change, why it is needed, and how it was tested.

## Style

- Imperative, concise Markdown; fenced code blocks with language tags; tables for structured data.
- Skill names: kebab-case with a category prefix (`bio-reads-qc-mapping`), descriptive, no abbreviations.
- Skills stay single-purpose with explicit inputs, outputs, and quality gates; compose workflows by referencing other skills rather than widening one skill.
- Record exact tool versions, parameters, and URLs whenever reproducibility depends on them.

## Getting Help

Open a GitHub issue (include `make status` output and steps to reproduce) or use GitHub Discussions.
