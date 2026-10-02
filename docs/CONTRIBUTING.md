# Contributing

[AGENTS.md](https://github.com/fmschulz/omics-skills/blob/main/AGENTS.md) holds the structural rules: skill layout, the `SKILL.md` format, validator limits and the agent sections the router parses. This page covers the workflow.

## Set up

Without push access, fork the repository, work on a branch of the fork, and open a pull request.

```bash
git clone https://github.com/<your-account>/omics-skills.git
cd omics-skills
make install
```

The default linked install picks up edits at once. Codex agents are rendered files: run `make install-codex` after editing an agent prompt.

## Add or change a skill

1. Create or edit `skills/<name>/SKILL.md`. The frontmatter `name` must equal the directory name, and the description needs a trigger phrase (`Use when`, `Use for` or `Trigger when`). Put long tool notes, examples and references in `docs/`, `examples/` or `references/` inside the skill directory.
2. Register a new skill in the owning agent file under `Mandatory Skill Usage`, `Workflow Decision Tree` and `Task Recognition Patterns`.
3. Run `make build-catalog` and commit `catalog/catalog.json`. CI rejects a stale catalog.
4. When the skill should be found from plain language, add a case to `tests/routing_benchmark.yaml` (see [Routing](routing.md#benchmark)).

Keep each skill to one purpose and compose workflows by referencing other skills. A supplementary tool guide starts with `Last verified`, `Tool version/release checked`, `Official docs/manual` and `Release/source` lines. A version in a skill is the version its commands were checked against, not an install pin: install commands add packages without a version, and projects lock what they install. To refresh checked versions, run `python3 scripts/check_tool_versions.py`, re-check the commands of each guide it flags, and update the guide. Examples use `you@example.org`. A real email address in a tracked file fails the tests.

## Run the checks

CI runs these on every push to `main`:

```bash
make test
make build-catalog && git diff --exit-code -- catalog/
find scripts skills validation -name '*.sh' -print0 | xargs -0 -r -n 1 bash -n
uvx --from mkdocs --with 'mkdocs-material==9.5.*' --with pymdown-extensions mkdocs build --strict
```

`make test` runs the skill, supplementary-doc and citation validators, the unit tests and the routing benchmark. The skill validator also enforces 500 lines per `SKILL.md`, 400 characters per description, 6,500 characters across all descriptions, and working local links.

When a plugin manifest changes, also run `claude plugin validate .`, `codex plugin marketplace add .` and `codex plugin list --available --json`. For installer changes, run `make install`, `make status` and `make validate`, and try the change in a Claude Code or Codex session.

## Documentation site

MkDocs Material builds the site from `docs/` and leaves out `docs/handoffs/`. Preview it with:

```bash
uvx --from mkdocs --with 'mkdocs-material==9.5.*' --with pymdown-extensions mkdocs serve
```

A push to `main` that changes `docs/`, `mkdocs.yml` or `.github/workflows/pages.yml` builds the site with `--strict` and deploys it to <https://fmschulz.github.io/omics-skills/>. Deployment needs the repository's Pages source set to **GitHub Actions** (Settings, Pages), a one-time setting.

## Release

Release notes live in GitHub Releases. The repository has no `CHANGELOG.md`.

1. Set the same version in `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`, and write `.github/releases/vX.Y.Z.md`.
2. Push to `main` and wait for CI and the docs build to pass.
3. Run `python3 scripts/check_release_sync.py --tag vX.Y.Z --main-ref origin/main`.
4. Create an annotated tag on that `main` commit and push it. `.github/workflows/release.yml` checks the tag, both manifests, the release notes and `origin/main`, then publishes the release.
5. Check the release page, the source archives, the version of an installed plugin, and the docs site.

Questions and bug reports go to GitHub issues; include the `make status` output and the steps to reproduce.
