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
python3 scripts/validate-skills.py
python3 scripts/validate-supplementary-docs.py
python3 -m unittest discover -s tests -v
make benchmark
```

## Documentation Style

Keep documentation concrete:

- Say what a skill is for, what it expects, and what it produces.
- Prefer short examples over abstract descriptions.
- Record exact tool versions, database names, URLs, and commands when a result needs to be reproducible.
- For supplementary tool/source guides, include `Last verified`, `Tool version/release checked`, `Official docs/manual`, and `Release/source` lines near the top.
- Keep `SKILL.md` focused; move detailed tool notes into `docs/`, `references/`, `examples/`, or `summaries/` inside the skill directory.

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
python3 scripts/validate-skills.py
python3 scripts/validate-supplementary-docs.py
python3 -m unittest discover -s tests -v
make benchmark
uvx --from mkdocs --with 'mkdocs-material==9.5.*' --with pymdown-extensions mkdocs build --strict
```

If routing behavior changes, update `tests/routing_benchmark.yaml` and refresh `docs/routing_baseline.json` only after reviewing the benchmark delta.

For contribution workflow details, see [Contributing](CONTRIBUTING.md). Distribution and marketplace notes live in [Distribution](DISTRIBUTION.md).
