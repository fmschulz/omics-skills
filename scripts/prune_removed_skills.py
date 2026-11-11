#!/usr/bin/env python3
"""Remove links to skills that left this pack.

A retired name alone proves nothing: another repository, or the user, may keep
an independent skill under it. This script therefore acts only on what it can
tie to this checkout:

* A symlink into this checkout's ``skills/`` directory is removed when its name
  is on the explicit lists below and the checkout no longer ships the skill.
* A ``.bak`` backup that is a symlink follows the same target rule. A ``.bak``
  directory is archived when its frontmatter names the skill.
* A copied skill directory is never touched.
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
# Skills that left the pack. A link into this checkout under one of these names
# is removed.
RETIRED_SKILLS = {
    "arxiv-search",
    "bio-assembly-qc",
    "bio-binning-qc",
    "bio-fasta-database-curator",
    "bio-foundation-housekeeping",
    "bio-gene-calling",
    "bio-phylogenomics",
    "bio-prefect-dask-nextflow",
    "bio-protein-clustering-pangenome",
    "bio-reads-qc-mapping",
    "bio-stats-ml-reporting",
    "bio-structure-annotation",
    "bio-workflow-methods-docwriter",
    "biorxiv-search",
    "exploratory-data-analysis",
    "get-api-docs",
    "jgi-lakehouse",
    "manuscript-review-council",
    "plotly-dashboard-skill",
    "preprint-search",
    "scientific-impact-assessment",
    "scientific-writing",
}
# These skills left the pack but live on in another repository, whose installer
# owns them. Retire only a link into this checkout, never a copied directory,
# which may be the other repository's install.
MOVED_SKILLS = {
    "ai-scientist-evaluator",
    "csag-extraction",
    "pdf-to-md",
    "proposal-review",
}
LEGACY_BACKUP = re.compile(
    r"^(?P<name>[a-z0-9]+(?:-[a-z0-9]+)*)\.bak(?:\.\d+)?$"
)


def links_into(target: Path, name: str, skills_dir: Path) -> bool:
    """Tell whether ``target`` is a symlink to ``skills_dir/name``, even if gone."""
    if not target.is_symlink():
        return False
    linked = target.resolve(strict=False)
    return linked.name == name and linked.parent.resolve() == skills_dir.resolve()


def current_skill_names(skills_dir: Path) -> set[str]:
    """Return the names of the skills this checkout ships.

    A directory without a ``SKILL.md`` is not a skill: ignored files such as
    ``__pycache__`` keep the directory of a deleted skill alive after an update.
    """
    return {
        path.parent.name
        for path in skills_dir.glob("*/SKILL.md")
        if SKILL_NAME.fullmatch(path.parent.name)
    }


def frontmatter_name(skill_dir: Path) -> str | None:
    """Return the ``name`` in a skill directory's ``SKILL.md``, if it has one."""
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return None
    for line in skill_file.read_text(encoding="utf-8").splitlines()[1:20]:
        if line.startswith("name:"):
            return line.partition(":")[2].strip().strip("'\"")
    return None


def next_backup_path(backup_dir: Path, name: str) -> Path:
    """Return the first unused path for ``name`` inside ``backup_dir``."""
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
    installed_skills_dir: Path,
    archive_dir: Path,
) -> tuple[list[str], list[str]]:
    """Retire installed links and backups that belong to skills of this pack.

    Args:
        skills_dir: The checkout's ``skills/`` directory.
        installed_skills_dir: The shared ``~/.agents/skills`` directory.
        archive_dir: Where recognized ``.bak`` backups are moved.

    Returns:
        The messages for what was removed or archived, then the warnings for
        what was left alone.
    """
    removed: list[str] = []
    warnings: list[str] = []
    current = current_skill_names(skills_dir)
    retired = sorted((RETIRED_SKILLS | MOVED_SKILLS) - current)

    # A backup of a skill we just retired is ours too: matching only against
    # `current` stranded `jgi-lakehouse.bak` beside the active skills forever.
    ours = current | set(retired)
    for target in sorted(installed_skills_dir.glob("*.bak*")):
        match = LEGACY_BACKUP.fullmatch(target.name)
        name = match.group("name") if match else ""
        if name not in ours or not is_our_backup(target, name, skills_dir):
            warnings.append(f"left unrecognized legacy backup untouched: {target}")
            continue
        archive_dir.mkdir(parents=True, exist_ok=True)
        destination = next_backup_path(archive_dir, target.name)
        shutil.move(str(target), destination)
        removed.append(f"archived legacy skill backup: {target.name} -> {destination}")

    for name in retired:
        target = installed_skills_dir / name
        if not target.is_symlink():
            continue
        if not links_into(target, name, skills_dir):
            # A moved skill linked from the repository that owns it now is the
            # expected state, not a finding.
            if name not in MOVED_SKILLS:
                linked = target.resolve(strict=False)
                warnings.append(
                    f"left unexpected symlink untouched: {target} -> {linked}"
                )
            continue
        target.unlink()
        removed.append(f"removed retired skill symlink: {name}")

    return removed, warnings


def main() -> int:
    """Parse the paths, retire the links and print what happened."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-dir", type=Path, required=True)
    parser.add_argument("--installed-skills-dir", type=Path, required=True)
    parser.add_argument("--archive-dir", type=Path, required=True)
    args = parser.parse_args()

    removed, warnings = prune_removed_skills(
        args.skills_dir.resolve(),
        args.installed_skills_dir.expanduser(),
        args.archive_dir.expanduser(),
    )
    for message in removed:
        print(f"  OK {message}")
    for message in warnings:
        print(f"  WARNING {message}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
