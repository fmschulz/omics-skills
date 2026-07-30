# Distribution Guide

How omics-skills is published and discovered across registries and marketplaces, and how releases are cut.

The repository follows the [Agent Skills open standard](https://agentskills.io/specification): every skill is a `SKILL.md` with YAML frontmatter, portable across Claude Code, the Codex CLI, and other platforms that adopt the standard.

## Distribution Channels

### Claude Code / Cowork Plugin Marketplace (primary)

The repository ships `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`; Claude Code discovers `agents/` and `skills/` as plugin components.

Validate and test before submitting:

```bash
claude plugin validate --strict .
claude plugin marketplace add fmschulz/omics-skills
claude plugin install omics-skills@omics-skills
```

Submit the public repository URL at <https://claude.ai/settings/plugins/submit> or <https://platform.claude.com/plugins/submit>. Anthropic's review runs `claude plugin validate` plus automated screening; approved community plugins track the GitHub repository for updates.

### Codex Plugin Marketplace

`.codex-plugin/plugin.json` plus the repo marketplace at `.agents/plugins/marketplace.json` make the pack installable with `codex plugin marketplace add fmschulz/omics-skills` and `codex plugin add omics-skills@omics-skills`.

### Official skill repositories

- [github.com/anthropics/skills](https://github.com/anthropics/skills) — fork, add selected skills under `skills/`, open a PR referencing this repository.
- [github.com/openai/skills](https://github.com/openai/skills) — same flow for the Codex skills catalog.

Lead with agent-agnostic, high-impact skills (`bio-logic`, `scientific-writing`, `beautiful-data-viz`, `notebooks`, `bio-reads-qc-mapping`).

### Community aggregators

[SkillsMP](https://skillsmp.com) and [SkillHub](https://www.skillhub.club/) index public GitHub repositories automatically; [MCP Market](https://mcpmarket.com/tools/skills) and the awesome-claude-skills lists ([travisvn](https://github.com/travisvn/awesome-claude-skills), [ComposioHQ](https://github.com/ComposioHQ/awesome-claude-skills)) take submissions. GitHub topics (`claude-skills`, `agent-skills`, `bioinformatics`, `computational-biology`) are what these aggregators key on, so keep them set on the repository.

## Release Process

GitHub Releases are the canonical release-note surface; there is no root `CHANGELOG.md`.

For each release:

1. Choose a semantic version tag such as `v1.6.0` and set the same version in `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`.
2. Add human-written release notes at `.github/releases/vX.Y.Z.md`.
3. Commit and push the release-ready docs, skills, agents, catalog, and tests.
4. Wait for CI and Docs to pass on `main`, then run `python3 scripts/check_release_sync.py --tag vX.Y.Z --main-ref origin/main`.
5. Create an annotated tag from the verified `main` commit and push it.
6. `.github/workflows/release.yml` re-verifies the tag, both plugin manifests, release notes, and `origin/main` before publishing the GitHub Release from `.github/releases/<tag>.md`.
7. Verify the published release, source archives, installed plugin version, and documentation site.

Release notes should cover major user-facing changes, agent and skill coverage, installation or compatibility notes, and the validation commands run before release. Keep the README version badge pointed at the repository releases page.

## Facts to Cite

Claims the repository can substantiate when announcing or submitting it:

- Four agent definitions (omics-scientist, literature-expert, science-writer, dataviz-artist) mapping task patterns and workflow steps to 34 installed skills.
- Coverage from reads QC through assembly, annotation, comparative genomics, literature discovery, scientific writing, and visualization.
- A generated routing catalog with a regression benchmark, skill validators, installer tests, and strict docs builds in CI.
- Make, shell, and plugin-marketplace installation paths for Claude Code and the Codex CLI.
- Citation metadata checked by repository validation, and a reproducibility-first workflow contract.

Keep this page current when the agent or skill counts change.
