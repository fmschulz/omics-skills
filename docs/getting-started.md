# Getting Started

## Requirements

You need Git, Bash, and at least one supported runtime:

- Claude Code
- Codex CLI

Python is needed for the router, catalog generation, and some skill-local helper scripts. Development and documentation commands use `uv` for Python tooling.

## Install

Clone the repository and install both Claude Code and Codex integrations:

```bash
git clone https://github.com/fmschulz/omics-skills.git
cd omics-skills
make install
```

The default install uses symlinks. That keeps the installed agents and skills in sync with the repository after `git pull`.

Install for only one runtime:

```bash
make install-claude
make install-codex
```

Use copies instead of symlinks when the checkout will not stay on disk:

```bash
make install INSTALL_METHOD=copy
```

## Enable Routing Hints

The optional hook runs the router for each prompt and injects a short routing hint into Claude Code or Codex:

```bash
make install-hook
make hook-status
```

Temporarily disable the hook for one shell session:

```bash
export OMICS_SKILLS_AUTOROUTE=0
```

Remove the hook:

```bash
make uninstall-hook
```

## Use an Agent

Claude Code:

```bash
claude --agent omics-scientist
```

Codex CLI:

```bash
codex --system-prompt ~/.codex/agents/omics-scientist.md
```

You can also run the router directly before choosing an agent:

```bash
python3 scripts/skill_index.py route "draft a response letter for reviewer comments"
```

## Verify the Install

```bash
make status
make test
```

For more installation details and troubleshooting, use the [Installation Guide](INSTALL.md).
