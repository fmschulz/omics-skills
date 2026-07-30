#!/usr/bin/env python3
"""Remove skills retired since the previously installed catalog."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
# Catalog files are symlinked in the default installation, so after an update
# they no longer retain the previous release's skill list. Keep explicit
# migrations for retired names that copy-mode installations must also remove.
RETIRED_SKILLS = {"get-api-docs"}
LEGACY_BACKUP = re.compile(
    r"^(?P<name>[a-z0-9]+(?:-[a-z0-9]+)*)\.bak(?:\.\d+)?$"
)


def catalog_skill_names(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"  WARNING installed catalog is unreadable; using explicit retirements: {exc}")
        return set()
    names = {item.get("name") for item in payload.get("skills", [])}
    return {name for name in names if isinstance(name, str) and SKILL_NAME.fullmatch(name)}


def current_skill_names(skills_dir: Path) -> set[str]:
    return {
        path.name
        for path in skills_dir.iterdir()
        if path.is_dir() and SKILL_NAME.fullmatch(path.name)
    }


def frontmatter_name(skill_dir: Path) -> str | None:
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return None
    for line in skill_file.read_text(encoding="utf-8").splitlines()[1:20]:
        if line.startswith("name:"):
            return line.partition(":")[2].strip().strip("'\"")
    return None


def next_backup_path(backup_dir: Path, name: str) -> Path:
    candidate = backup_dir / name
    counter = 1
    while candidate.exists() or candidate.is_symlink():
        candidate = backup_dir / f"{name}.{counter}"
        counter += 1
    return candidate


def prune_removed_skills(
    skills_dir: Path,
    installed_catalog: Path,
    installed_skills_dir: Path,
    backup_dir: Path,
) -> tuple[list[str], list[str]]:
    removed: list[str] = []
    warnings: list[str] = []
    current = current_skill_names(skills_dir)
    retired = sorted((catalog_skill_names(installed_catalog) - current) | (RETIRED_SKILLS - current))

    for target in sorted(installed_skills_dir.glob("*.bak*")):
        match = LEGACY_BACKUP.fullmatch(target.name)
        if not match or match.group("name") not in current or not target.is_dir():
            warnings.append(f"left unrecognized legacy backup untouched: {target}")
            continue
        name = match.group("name")
        if frontmatter_name(target) != name:
            warnings.append(f"left unrecognized legacy backup untouched: {target}")
            continue
        previous_dir = backup_dir.parent / "previous-skills"
        previous_dir.mkdir(parents=True, exist_ok=True)
        destination = next_backup_path(previous_dir, target.name)
        shutil.move(str(target), destination)
        removed.append(f"archived legacy skill backup: {target.name} -> {destination}")

    for name in retired:
        target = installed_skills_dir / name
        if target.is_symlink():
            linked = target.resolve(strict=False)
            if linked.name != name or linked.parent.resolve() != skills_dir.resolve():
                warnings.append(f"left unexpected symlink untouched: {target} -> {linked}")
                continue
            target.unlink()
            removed.append(f"removed retired skill symlink: {name}")
        elif target.is_dir():
            if frontmatter_name(target) != name:
                warnings.append(f"left unrecognized directory untouched: {target}")
                continue
            backup_dir.mkdir(parents=True, exist_ok=True)
            destination = next_backup_path(backup_dir, name)
            shutil.move(str(target), destination)
            removed.append(f"archived retired copied skill: {name} -> {destination}")

    return removed, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-dir", type=Path, required=True)
    parser.add_argument("--installed-catalog", type=Path, required=True)
    parser.add_argument("--installed-skills-dir", type=Path, required=True)
    parser.add_argument("--backup-dir", type=Path, required=True)
    args = parser.parse_args()

    removed, warnings = prune_removed_skills(
        args.skills_dir.resolve(),
        args.installed_catalog.expanduser(),
        args.installed_skills_dir.expanduser(),
        args.backup_dir.expanduser(),
    )
    for message in removed:
        print(f"  OK {message}")
    for message in warnings:
        print(f"  WARNING {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
