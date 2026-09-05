# Installation Guide

Omics Skills supports Claude Code and Codex through the same skill source tree, but the two runtimes use different agent formats. Claude Code reads the canonical Markdown agents. Codex reads TOML agent definitions rendered during installation.

## Requirements

Install Git, Bash, GNU Make, Python 3.11 or newer (Codex agent rendering uses `tomllib`), and at least one supported runtime:

```bash
git --version
python3 --version
claude --version   # if using Claude Code
codex --version    # if using Codex
```

`make install` does not require a system Python environment. Development commands and skill-local Python helpers use [uv](https://docs.astral.sh/uv/).

## Install from a Plugin Marketplace

### Claude Code

```bash
claude plugin marketplace add fmschulz/omics-skills
claude plugin install omics-skills@omics-skills
```

Test a local checkout before publishing it:

```bash
claude plugin validate .
claude plugin marketplace add .
claude plugin install omics-skills@omics-skills
```

### Codex

```bash
codex plugin marketplace add fmschulz/omics-skills
codex plugin list --available --json
codex plugin add omics-skills@omics-skills
```

For a local checkout, use `codex plugin marketplace add .`. The repository includes `.codex-plugin/plugin.json` and a repo marketplace at `.agents/plugins/marketplace.json`.

## Install from a Checkout

Clone the repository and install both runtime integrations:

```bash
git clone https://github.com/fmschulz/omics-skills.git
cd omics-skills
make install
```

Install one runtime only:

```bash
make install-claude
make install-codex
```

The default install links skills and Claude agents to the checkout. Use copies when the checkout will not remain available:

```bash
make install INSTALL_METHOD=copy
```

## Installed Files

The checkout installer writes only runtime configuration and omics-skills-owned entries:

```text
~/.agents/skills/<skill>/          shared skill links or copies
~/.agents/omics-skills/           router and generated catalog
~/.claude/agents/<agent>.md       Claude agent links or copies
~/.claude/skills                  link to ~/.agents/skills
~/.codex/agents/<agent>.toml      rendered Codex subagent definitions
~/.codex/skills                   compatibility link to ~/.agents/skills
```

The canonical skill location for Codex is `~/.agents/skills`. The `~/.codex/skills` link is retained for compatibility. Because Codex agents are generated TOML rather than symlinks, rerun `make install-codex` after editing a Markdown agent source.

Existing files with an omics-skills agent or skill name are moved to timestamped backups. Unrelated files and backups in the shared directories are left alone.

`~/.claude/skills` and `~/.codex/skills` become symlinks to `~/.agents/skills`. If either is already a real directory holding your own skills, installation stops and tells you to move or merge it first, because replacing it with a symlink would hide everything inside.

## Manual Installation

Install shared skills and Claude agents with symlinks:

```bash
mkdir -p ~/.agents/skills ~/.claude/agents
for skill in "$PWD"/skills/*; do
    ln -sfn "$skill" "$HOME/.agents/skills/$(basename "$skill")"
done
for agent in "$PWD"/agents/*.md; do
    ln -sfn "$agent" "$HOME/.claude/agents/$(basename "$agent")"
done
ln -sfn "$HOME/.agents/skills" "$HOME/.claude/skills"
```

Render Codex agents instead of copying the Markdown files:

```bash
mkdir -p ~/.codex/agents
for agent in "$PWD"/agents/*.md; do
    name=$(basename "$agent" .md)
    python3 scripts/render_codex_agent.py "$agent" "$HOME/.codex/agents/$name.toml"
done
ln -sfn "$HOME/.agents/skills" "$HOME/.codex/skills"
```

## Verify the Installation

For a full checkout installation:

```bash
make status
make validate
make test
```

Inspect the relevant files directly when only one runtime was installed:

```bash
ls -l ~/.claude/agents/omics-scientist.md
python3 -c "import pathlib,tomllib; tomllib.loads(pathlib.Path.home().joinpath('.codex/agents/omics-scientist.toml').read_text())"
ls -ld ~/.agents/skills/bio-annotation
python3 ~/.agents/omics-skills/skill_index.py route "annotate these proteins"
```

## Use the Installation

Start Claude Code with a named agent:

```bash
claude --agent omics-scientist
```

Start Codex normally, then ask it to delegate to `omics-scientist`, or mention a skill explicitly with `$bio-annotation`. Codex discovers custom TOML subagents in `~/.codex/agents/`.

The router can be queried independently of either runtime:

```bash
python3 ~/.agents/omics-skills/skill_index.py route \
  "assemble a metagenome and recover MAGs"
```

## Optional Routing Hook

Install a prompt hook that adds a router hint for both runtimes:

```bash
make install-hook
make hook-status
```

Disable it for one shell session without uninstalling it:

```bash
export OMICS_SKILLS_AUTOROUTE=0
```

Remove it with `make uninstall-hook`.

## Python Dependencies

Skill helpers declare their own environment through Pixi or PEP 723 metadata, so `uv run --script <helper>` resolves them on demand. Nothing needs a shared Python environment.

## Update

For linked installs, pull the checkout and rebuild generated artifacts:

```bash
git pull
make install
```

For copied installs, the same command replaces only the selected omics-skills entries. Plugin installs are updated through their respective marketplace commands.

## Select Components

Pass explicit lists to install a subset:

```bash
make install-selected \
  SELECTED_AGENT_FILES="omics-scientist.md" \
  SELECTED_SKILL_DIRS="bio-logic bio-annotation"
```

Missing selected names fail the installation instead of reporting partial success. The generated catalog contains only the selected components.

## Troubleshooting

### Agent changes do not appear in Codex

Codex agents are generated TOML files. Regenerate them:

```bash
make install-codex
```

### Skills disappeared after moving the checkout

Linked installs retain the old absolute paths. Reinstall from the new location:

```bash
make install
```

### A skill is not selected

Check the router result before changing prompts:

```bash
python3 scripts/skill_index.py route "<task>" --json
make benchmark
```

Then inspect the skill description and the owning agent's `Task Recognition Patterns`.

### A local plugin is not listed

```bash
codex plugin marketplace list
codex plugin list --available --json
claude plugin validate .
```

Confirm that the marketplace resolves to the checkout and that both plugin manifests use the same version.

## Uninstall

Use the Makefile for a complete non-interactive uninstall:

```bash
make uninstall
```

Remove one runtime only:

```bash
make uninstall-claude
make uninstall-codex
```

Both uninstallers remove only known omics-skills entries. They preserve unrelated agents, skills, and backups in shared runtime directories.
