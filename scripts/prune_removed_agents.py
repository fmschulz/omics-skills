#!/usr/bin/env python3
"""Remove installed agents that left this pack.

A retired name alone proves nothing: a user may keep an independent agent under
it. This script acts only on what it can tie to this pack:

* A symlink is removed when it points at this checkout's ``agents/<name>.md``.
* A copied or rendered file is archived only when the installed catalog is a
  real file, which a copy install wrote, and lists the agent. A catalog that
  links elsewhere is rewritten by every update and records nothing.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from prune_removed_skills import catalog_is_a_copy, next_backup_path

# Agents that left the pack. The default install links a Claude agent but
# renders a Codex file, so an old Codex file is archived only with a record.
RETIRED_AGENTS = {"dataviz-artist"}
INSTALLED_SUFFIXES = (".md", ".toml")


def catalog_agent_names(path: Path) -> set[str]:
    """Return the agent names a copied catalog lists, else nothing."""
    if not catalog_is_a_copy(path):
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    names = {item.get("name") for item in payload.get("agents", [])}
    return {name for name in names if isinstance(name, str)}


def prune_removed_agents(
    agents_dir: Path,
    installed_catalog: Path,
    installed_agents_dir: Path,
    backup_dir: Path,
) -> list[str]:
    """Retire installed agents that this checkout no longer ships.

    Args:
        agents_dir: The checkout's ``agents/`` directory.
        installed_catalog: The installed ``catalog.json``.
        installed_agents_dir: The runtime's agent directory (Claude or Codex).
        backup_dir: Where archived files go.

    Returns:
        One message per retired or archived file.
    """
    removed: list[str] = []
    listed = catalog_agent_names(installed_catalog)
    shipped = {path.stem for path in agents_dir.glob("*.md")}
    for name in sorted(RETIRED_AGENTS - shipped):
        for suffix in INSTALLED_SUFFIXES:
            target = installed_agents_dir / f"{name}{suffix}"
            if target.is_symlink():
                source = agents_dir.resolve() / f"{name}.md"
                if target.resolve(strict=False) == source:
                    target.unlink()
                    removed.append(f"removed retired agent link: {target.name}")
            elif target.is_file() and name in listed:
                backup_dir.mkdir(parents=True, exist_ok=True)
                destination = next_backup_path(backup_dir, target.name)
                shutil.move(str(target), destination)
                removed.append(
                    f"archived retired agent: {target.name} -> {destination}"
                )
    return removed


def main() -> int:
    """Parse the paths, retire the agents and print what happened."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agents-dir", type=Path, required=True)
    parser.add_argument("--installed-catalog", type=Path, required=True)
    parser.add_argument("--installed-agents-dir", type=Path, required=True)
    parser.add_argument("--backup-dir", type=Path, required=True)
    args = parser.parse_args()

    for message in prune_removed_agents(
        args.agents_dir.resolve(),
        args.installed_catalog.expanduser(),
        args.installed_agents_dir.expanduser(),
        args.backup_dir.expanduser(),
    ):
        print(f"  OK {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
