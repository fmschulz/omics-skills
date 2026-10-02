# Install

The pack installs from a checkout with `make`, or as a plugin for Claude Code or the Codex CLI. Claude Code reads the Markdown agents; Codex reads TOML agents rendered at install time.

## Requirements

- Git, GNU Make, and Python 3.11 or newer. The installer uses only the Python standard library.
- Claude Code, the Codex CLI, or both.
- [uv](https://docs.astral.sh/uv/) or Pixi for skill helper scripts, which declare their own dependencies.

## Install from a checkout

```bash
git clone https://github.com/fmschulz/omics-skills.git
cd omics-skills
make install
```

`make install` builds the routing catalog, links every skill into `~/.agents/skills`, links the Claude agents, and renders the Codex agents.

| Command | Effect |
|---|---|
| `make install-claude` or `make install-codex` | Installs for one runtime. |
| `make install INSTALL_METHOD=copy` | Copies instead of linking, for a checkout that will not stay on disk. |
| `make install LINK_CLIENT_SKILLS=no` | Leaves `~/.claude/skills` and `~/.codex/skills` untouched, for hosts where another tool manages them. |
| `make install-selected SELECTED_AGENT_FILES="omics-scientist.md" SELECTED_SKILL_DIRS="bio-logic bio-annotation"` | Installs a subset. A missing name fails the install, and the catalog lists only the selection. |

### Installed files

A checkout install writes:

```text
~/.agents/skills/<skill>        skill links or copies
~/.agents/omics-skills/         router (skill_index.py) and catalog.json
~/.claude/agents/<agent>.md     Claude agent links or copies
~/.claude/skills                link to ~/.agents/skills
~/.codex/agents/<agent>.toml    rendered Codex agents
~/.codex/skills                 link to ~/.agents/skills
```

- An existing directory with a pack skill's name is moved to `~/.agents/omics-skills/previous-skills/`. A link with that name is replaced.
- An installed agent identical to the new one is left in place. A differing file is kept once as a timestamped `.bak` file.
- If `~/.claude/skills` or `~/.codex/skills` is a real directory, the installer stops instead of hiding its contents. Merge it into `~/.agents/skills`, or install with `LINK_CLIENT_SKILLS=no`.
- Files that do not belong to the pack are not touched.

## Install as a plugin

Claude Code:

```bash
claude plugin marketplace add fmschulz/omics-skills
claude plugin install omics-skills@omics-skills
```

Codex CLI:

```bash
codex plugin marketplace add fmschulz/omics-skills
codex plugin add omics-skills@omics-skills
```

To test a local checkout, pass `.` to `marketplace add` instead of the repository name.

The Claude Code plugin provides the agents and skills; the Codex plugin provides the skills. The router, the catalog, the routing hint hook and the Codex agents come only with a checkout install.

To update, refresh the marketplace and then the plugin. Claude Code: `claude plugin marketplace update omics-skills`, then `claude plugin update omics-skills@omics-skills` and a restart. Codex CLI: `codex plugin marketplace upgrade omics-skills`, then `codex plugin add omics-skills@omics-skills` again.

## Start an agent

Claude Code:

```bash
claude --agent omics-scientist
```

Codex CLI: start `codex`, then ask it to delegate to `omics-scientist`, or name a skill such as `$bio-annotation`.

After a checkout install, the [router](routing.md) shows which agent and skills fit a task:

```bash
python3 ~/.agents/omics-skills/skill_index.py route "annotate these proteins"
```

## Routing hint hook

The optional hook runs the router on each prompt and adds a short hint for Claude Code and Codex. When the router fails, the hook exits without blocking the prompt.

```bash
make install-hook
make hook-status
```

Turn it off for one shell with `export OMICS_SKILLS_AUTOROUTE=0`. Remove it with `make uninstall-hook`.

## Check, update and remove

| Task | Command |
|---|---|
| Show what is installed | `make status` |
| Check that every agent and skill is installed | `make validate` |
| Update a checkout install | `git pull && make install` |
| Apply an edited agent prompt to Codex | `make install-codex` |
| Remove the pack (pack entries only) | `make uninstall`, `make uninstall-claude` or `make uninstall-codex` |
| Delete agent backups and archived skill directories | `make clean` |

## Troubleshooting

| Problem | Fix |
|---|---|
| Codex does not show an agent change | Run `make install-codex`. |
| Skills are missing after the checkout moved | Run `make install` from the new location; links keep the old path. |
| The router does not pick a skill | Run `python3 scripts/skill_index.py route "<task>" --json`, then check the skill description and the agent's `Task Recognition Patterns`. |
| A local plugin is not listed | Run `codex plugin marketplace list`, `codex plugin list --available --json` and `claude plugin validate .`. |
