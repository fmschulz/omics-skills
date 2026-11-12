# Install

The pack installs from a checkout with `make`, or as a plugin for Claude Code or the Codex CLI. Claude Code reads the Markdown agent; Codex reads a TOML agent rendered at install time.

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

`make install` links every skill into `~/.agents/skills`, links the Claude agent, and renders the Codex agent. It also removes the links of skills and agents that left the pack. It removes a link only when the link points into the checkout and the name is on the pack's list of retired or moved skills or retired agents. Everything else stays: a copied skill directory, a copied agent file, a rendered Codex agent such as `~/.codex/agents/omics-scientist.toml`, an independent skill or agent with a retired name, a `.bak` link to another repository, a copied `.bak` directory, and a moved skill such as `pdf-to-md` that another repository now owns. Delete those by hand when you no longer want them.

| Command | Effect |
|---|---|
| `make install-claude` or `make install-codex` | Installs for one runtime. |
| `make install INSTALL_METHOD=copy` | Copies instead of linking, for a checkout that will not stay on disk. |
| `make install LINK_CLIENT_SKILLS=no` | Leaves `~/.claude/skills` and `~/.codex/skills` untouched, for hosts where another tool manages them. |
| `make install-selected SELECTED_AGENT_FILES="literature-expert.md" SELECTED_SKILL_DIRS="polars-dovmed crossref-lookup"` | Installs exactly the selection. A missing name fails the install. |

A skill selection works with every install target, so `make install-claude SELECTED_SKILL_DIRS="..."` is valid too. A selection that holds `omics-pipeline` or a stage skill gets the whole pipeline group, because `omics-pipeline` names the stage skills and each stage skill points back to it; `make` prints one line that names what it added. A directory under `skills/` without a `SKILL.md` is not a skill. Ignored files such as `__pycache__` can leave one behind after an update, and the installer skips it.

### Installed files

A checkout install writes:

```text
~/.agents/skills/<skill>        skill links or copies
~/.agents/omics-skills/         archives of replaced and retired entries, created when needed
~/.claude/agents/<agent>.md     Claude agent link or copy
~/.claude/skills                link to ~/.agents/skills
~/.codex/agents/<agent>.toml    rendered Codex agent
~/.codex/skills                 link to ~/.agents/skills
```

- An existing directory with a pack skill's name is moved to `~/.agents/omics-skills/previous-skills/`. A link with that name is replaced. A `.bak` symlink into the checkout moves there too; a copied `.bak` directory stays where it is, even when its `SKILL.md` names a pack skill.
- The install deletes `skill_index.py`, `catalog.json` and `README.md` in `~/.agents/omics-skills/`, which earlier versions installed there.
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

The Claude Code plugin provides the agent and the skills; the Codex plugin provides the skills. The Codex agent comes only with a checkout install. The pipeline stage skills are sibling directories of `omics-pipeline`, so the plugin layout resolves them as `../<name>/SKILL.md` without any `~/.agents/skills` link.

To update, refresh the marketplace and then the plugin. Claude Code: `claude plugin marketplace update omics-skills`, then `claude plugin update omics-skills@omics-skills` and a restart. Codex CLI: `codex plugin marketplace upgrade omics-skills`, then `codex plugin add omics-skills@omics-skills` again.

## Use the skills and the agent

A session loads a skill when its description fits the task. To load one directly, name it: `/omics-pipeline` in Claude Code, `$omics-pipeline` in Codex. Pipeline stage skills such as `bio-annotation` are hidden from implicit use; `omics-pipeline` names them, and you can name one yourself.

For a literature task in its own context, start the agent with `claude --agent literature-expert`, or ask Codex to delegate to `literature-expert`.

## Upgrade from 1.x

Version 2.0.0 removed 15 skills, two agents and the keyword router. The [release notes](https://github.com/fmschulz/omics-skills/releases/tag/v2.0.0) list them.

1. If you installed the routing hint hook, run `make uninstall-hook` in the 1.x checkout before you update. Version 2.0.0 has no such target.
2. Update the checkout and run `make install`. It removes the links of removed skills and agents that point into the checkout, and the router files under `~/.agents/omics-skills/`.
3. Delete by hand what the installer cannot attribute to the pack: `~/.codex/agents/omics-scientist.toml`, `~/.codex/agents/science-writer.toml`, and, after a copy install, the directories of removed skills under `~/.agents/skills/`.
4. Scripts of the removed skills are gone. A project that calls one by path needs its own copy, taken from tag `v1.7.1`.

## Check, update and remove

| Task | Command |
|---|---|
| Show what is installed | `make status` |
| Check that the agent and every skill are installed | `make validate` |
| Update a checkout install | `git pull && make install` |
| Apply the edited agent prompt to Codex | `make install-codex` |
| Remove the pack (pack entries only) | `make uninstall`, `make uninstall-claude` or `make uninstall-codex` |
| Delete agent backups and archived skill and agent files | `make clean` |

## Troubleshooting

| Problem | Fix |
|---|---|
| Codex does not show an agent change | Run `make install-codex`. |
| Skills are missing after the checkout moved | Run `make install` from the new location; links keep the old path. |
| A local plugin is not listed | Run `codex plugin marketplace list`, `codex plugin list --available --json` and `claude plugin validate .`. |
