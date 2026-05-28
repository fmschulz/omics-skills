#!/usr/bin/env python3
"""Validate every skills/<name>/SKILL.md: frontmatter name matches the
directory, name is a valid slug, required sections are present, and the file
stays within the length budget.

Importable (validate_skill / validate_all) so the checks are unit-testable, and
runnable as a CLI for CI and the install smoke test."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import skill_index  # noqa: E402  (reuse the single frontmatter parser)

REQUIRED_SECTIONS = [
    "## Instructions",
    "## Quick Reference",
    "## Input Requirements",
    "## Output",
    "## Quality Gates",
    "## Examples",
    "## Troubleshooting",
]
MAX_LINES = 500
MAX_NAME_LENGTH = 64
SLUG_PATTERN = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


def validate_skill(skill_dir: Path) -> list[str]:
    """Return a list of human-readable validation errors for one skill dir."""
    name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [f"{name}: missing SKILL.md"]

    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return [f"{name}: missing frontmatter"]

    errors: list[str] = []
    frontmatter, _ = skill_index.split_frontmatter(text)
    fm_name = (frontmatter.get("name") or "").strip()
    if fm_name != name:
        errors.append(f"{name}: frontmatter name mismatch ({fm_name})")
    if not SLUG_PATTERN.fullmatch(fm_name):
        errors.append(f"{name}: frontmatter name invalid ({fm_name})")
    if len(fm_name) > MAX_NAME_LENGTH:
        errors.append(f"{name}: frontmatter name too long ({len(fm_name)})")
    missing = [section for section in REQUIRED_SECTIONS if section not in text]
    if missing:
        errors.append(f"{name}: missing sections {missing}")
    line_count = len(text.splitlines())
    if line_count > MAX_LINES:
        errors.append(f"{name}: SKILL.md over {MAX_LINES} lines ({line_count})")
    return errors


def validate_all(skills_dir: Path) -> list[str]:
    """Validate every skill directory under ``skills_dir``."""
    errors: list[str] = []
    for entry in sorted(skills_dir.iterdir()):
        if entry.is_dir():
            errors.extend(validate_skill(entry))
    return errors


def main(argv: list[str] | None = None) -> int:
    skills_dir = Path(__file__).resolve().parent.parent / "skills"
    errors = validate_all(skills_dir)
    if errors:
        print("Skill validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1
    print("Skill validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
