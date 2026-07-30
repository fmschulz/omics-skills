# Development

## Repository Layout

```text
agents/       Markdown agent prompts
skills/       Skill directories; each has a SKILL.md
catalog/      Generated router artifacts
scripts/      Router, hook installer, validation, and benchmark scripts
tests/        Unit tests and routing benchmark cases
docs/         MkDocs source files
```

## Add or Edit a Skill

1. Create or edit `skills/<skill-name>/SKILL.md`.
2. Keep the YAML `name` field identical to the directory name.
3. Put long tool notes, examples, and references in subdirectories rather than crowding `SKILL.md`.
4. Update the relevant agent file:
   - `Mandatory Skill Usage`
   - `Workflow Decision Tree`
   - `Task Recognition Patterns`
5. Rebuild the catalog.
6. Add routing benchmark coverage when the skill should be discoverable from natural language.

Commands:

```bash
python3 scripts/skill_index.py build
uv run --script scripts/validate-skills.py
python3 scripts/validate-supplementary-docs.py
uv run --no-project --with pytest --with requests --with PyYAML python -m pytest tests -q
make benchmark
```

## Documentation Style

Keep documentation concrete:

- Say what a skill is for, what it expects, and what it produces.
- Keep frontmatter descriptions concise and include an explicit `Use when` or `Use for` trigger.
- Prefer short examples over abstract descriptions.
- Record exact tool versions, database names, URLs, and commands when a result needs to be reproducible.
- For supplementary tool/source guides, include `Last verified`, `Tool version/release checked`, `Official docs/manual`, and `Release/source` lines near the top.
- Keep `SKILL.md` focused; move detailed tool notes into `docs/`, `references/`, or `examples/` inside the skill directory.

## Work on the MkDocs Site

Preview locally:

```bash
uvx --from mkdocs --with 'mkdocs-material==9.5.*' --with pymdown-extensions mkdocs serve
```

Build strictly:

```bash
uvx --from mkdocs --with 'mkdocs-material==9.5.*' --with pymdown-extensions mkdocs build --strict
```

The GitHub Pages workflow runs the same strict build before deployment.

## Validation Checklist

Before opening a pull request:

```bash
uv run --script scripts/validate-skills.py
python3 scripts/validate-supplementary-docs.py
uv run --no-project --with pytest --with requests --with PyYAML python -m pytest tests -q
make benchmark
uvx --from mkdocs --with 'mkdocs-material==9.5.*' --with pymdown-extensions mkdocs build --strict
```

The skill validator also checks the 500-line limit, a 400-character per-description limit, the aggregate discovery budget, and local Markdown links. Validate both plugin surfaces when their metadata changes:

```bash
claude plugin validate .
codex plugin marketplace add .
codex plugin list --available --json
```

If routing behavior changes, update `tests/routing_benchmark.yaml` and refresh `docs/routing_baseline.json` only after reviewing the benchmark delta.

The [Skill Quality](skill-quality.md) page records current per-skill improvement priorities. For contribution workflow details, see [Contributing](CONTRIBUTING.md). Distribution and marketplace notes live in [Distribution](DISTRIBUTION.md).
