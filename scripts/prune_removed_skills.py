#!/usr/bin/env python3
"""Remove skills retired since the previously installed catalog.

A retired name alone proves nothing: another repository, or the user, may keep
an independent skill under it. This script therefore acts only on what it can
tie to this pack:

* A symlink is retired when it points into this checkout's ``skills/``
  directory, for a name on the explicit lists or in the previous catalog.
* A copied directory is archived only when the installed catalog is a real
  file, which a copy install wrote, and lists the name. A catalog that links
  elsewhere is rewritten by every update and records nothing.
* A ``.bak`` backup that is a symlink follows the same target rule as any link.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
# Catalog files are symlinked in the default installation, so after an update
# they no longer retain the previous release's skill list. Keep explicit
# migrations for retired names whose symlinks into this checkout must go.
RETIRED_SKILLS = {
    "arxiv-search",
    "bio-prefect-dask-nextflow",
    "biorxiv-search",
    "get-api-docs",
    "jgi-lakehouse",
    "manuscript-review-council",
    "plotly-dashboard-skill",
    "scientific-impact-assessment",
    "scientific-writing",
}
# These skills left the pack but live on in another repository, whose installer
# owns them. Retire only a link into this checkout; never a copied directory,
# which may be the other repository's install, whatever the catalog lists.
MOVED_SKILLS = {"csag-extraction", "pdf-to-md"}
LEGACY_BACKUP = re.compile(
    r"^(?P<name>[a-z0-9]+(?:-[a-z0-9]+)*)\.bak(?:\.\d+)?$"
)


def catalog_is_a_copy(path: Path) -> bool:
    """Tell whether the installed catalog is a real file that this pack wrote.

    A link is rewritten by every update, so it cannot show what an earlier
    install put on disk.
    """
    return path.is_file() and not path.is_symlink()


def links_into(target: Path, name: str, skills_dir: Path) -> bool:
    """Tell whether ``target`` is a symlink to ``skills_dir/name``, even if gone."""
    if not target.is_symlink():
        return False
    linked = target.resolve(strict=False)
    return linked.name == name and linked.parent.resolve() == skills_dir.resolve()


def catalog_skill_names(path: Path) -> set[str]:
    """Return the skill names a copied catalog lists, else nothing."""
    if not catalog_is_a_copy(path):
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


def is_our_backup(target: Path, name: str, skills_dir: Path) -> bool:
    """Tell whether a ``.bak`` entry is a backup of this pack's skill ``name``.

    A symlink is ours only through its target. A directory is ours when its
    frontmatter names the skill.
    """
    if target.is_symlink():
        return links_into(target, name, skills_dir)
    return target.is_dir() and frontmatter_name(target) == name


def prune_removed_skills(
    skills_dir: Path,
    installed_catalog: Path,
    installed_skills_dir: Path,
    backup_dir: Path,
) -> tuple[list[str], list[str]]:
    removed: list[str] = []
    warnings: list[str] = []
    current = current_skill_names(skills_dir)
    listed = catalog_skill_names(installed_catalog) - current
    retired = sorted(listed | (RETIRED_SKILLS - current) | (MOVED_SKILLS - current))

    # A backup of a skill we just retired is ours too: matching only against
    # `current` stranded `jgi-lakehouse.bak` beside the active skills forever.
    ours = current | set(retired)
    for target in sorted(installed_skills_dir.glob("*.bak*")):
        match = LEGACY_BACKUP.fullmatch(target.name)
        name = match.group("name") if match else ""
        if name not in ours or not is_our_backup(target, name, skills_dir):
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
            if not links_into(target, name, skills_dir):
                linked = target.resolve(strict=False)
                warnings.append(f"left unexpected symlink untouched: {target} -> {linked}")
                continue
            target.unlink()
            removed.append(f"removed retired skill symlink: {name}")
        elif target.is_dir() and name in listed and name not in MOVED_SKILLS:
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
