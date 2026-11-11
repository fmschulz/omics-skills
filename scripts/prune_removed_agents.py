#!/usr/bin/env python3
"""Remove installed agent links for agents that left this pack.

A retired name alone proves nothing: a user may keep an independent agent under
it. This script acts only on a symlink that points at this checkout's
``agents/<name>.md``. A copied agent file and a rendered Codex file cannot be
tied to this pack, so they stay.
"""

from __future__ import annotations

import argparse
from pathlib import Path

# Agents that left the pack.
RETIRED_AGENTS = {"dataviz-artist", "omics-scientist", "science-writer"}
INSTALLED_SUFFIXES = (".md", ".toml")


def prune_removed_agents(agents_dir: Path, installed_agents_dir: Path) -> list[str]:
    """Remove installed links to agents that this checkout no longer ships.

    Args:
        agents_dir: The checkout's ``agents/`` directory.
        installed_agents_dir: The runtime's agent directory (Claude or Codex).

    Returns:
        One message per removed link.
    """
    removed: list[str] = []
    shipped = {path.stem for path in agents_dir.glob("*.md")}
    for name in sorted(RETIRED_AGENTS - shipped):
        source = agents_dir.resolve() / f"{name}.md"
        for suffix in INSTALLED_SUFFIXES:
            target = installed_agents_dir / f"{name}{suffix}"
            if target.is_symlink() and target.resolve(strict=False) == source:
                target.unlink()
                removed.append(f"removed retired agent link: {target.name}")
    return removed


def main() -> int:
    """Parse the paths, remove the links and print what happened."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agents-dir", type=Path, required=True)
    parser.add_argument("--installed-agents-dir", type=Path, required=True)
    args = parser.parse_args()

    for message in prune_removed_agents(
        args.agents_dir.resolve(),
        args.installed_agents_dir.expanduser(),
    ):
        print(f"  OK {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
