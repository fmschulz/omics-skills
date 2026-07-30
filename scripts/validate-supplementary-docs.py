#!/usr/bin/env python3
"""Validate provenance headers for supplementary skill documentation."""
from __future__ import annotations

import re
import sys
from pathlib import Path

DATE_RE = re.compile(r"^(?:\*\*)?Last verified(?:\*\*)?:(?:\*\*)?\s+20\d\d-\d\d-\d\d", re.MULTILINE)
VERSION_RE = re.compile(r"^(?:\*\*)?Tool version/release checked(?:\*\*)?:(?:\*\*)?\s+.+", re.MULTILINE)
DOCS_RE = re.compile(r"^(?:\*\*)?Official docs/manual(?:\*\*)?:(?:\*\*)?\s+.+", re.MULTILINE)
SOURCE_RE = re.compile(r"^(?:\*\*)?Release/source(?:\*\*)?:(?:\*\*)?\s+.+", re.MULTILINE)
BANNED_ENV_COMMAND_RE = re.compile(
    r"\b(?:conda\s+install|mamba\s+(?:install|create))\b",
    re.IGNORECASE,
)
PINNED_PIXI_GATE_RE = re.compile(r"\b(?:pinned\s+pixi|pixi\.lock)\b", re.IGNORECASE)

ROOT = Path(__file__).resolve().parent.parent
REQUIRED_SUPPLEMENTARY_DOCS = (
    "skills/tracking-taxonomy-updates/reference/sources.md",
    "skills/tracking-taxonomy-updates/reference/tools.md",
)


def supplementary_doc_files(root: Path) -> list[Path]:
    """Return supplementary Markdown docs that describe tools or data sources."""
    skills = root / "skills"
    if not skills.exists():
        return []
    files: list[Path] = []
    for skill_dir in sorted(p for p in skills.iterdir() if p.is_dir()):
        docs = skill_dir / "docs"
        if docs.exists():
            files.extend(sorted(p for p in docs.glob("*.md") if p.is_file()))
        if skill_dir.name == "bio-prefect-dask-nextflow":
            files.extend(sorted(p for p in skill_dir.glob("*.md") if p.name != "SKILL.md"))
        if skill_dir.name == "bio-fasta-database-curator":
            path = skill_dir / "tools.md"
            if path.exists():
                files.append(path)
        if skill_dir.name == "tracking-taxonomy-updates":
            for rel in ("reference/sources.md", "reference/tools.md"):
                path = skill_dir / rel
                if path.exists():
                    files.append(path)
    return sorted(set(files))


def is_tool_or_source_doc(path: Path, text: str) -> bool:
    """Filter out prose-only references that are not tool/source guides."""
    lower = text.lower()
    markers = (
        "official documentation",
        "official docs",
        "official website",
        "official site",
        "github",
        "manual",
        "source:",
        "sources",
        "version",
        "install",
        "command",
        "database",
        "release",
        "api",
    )
    return any(marker in lower for marker in markers)


def validate_doc(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if not is_tool_or_source_doc(path, text):
        return []
    errors: list[str] = []
    if not DATE_RE.search(text):
        errors.append("missing '**Last verified:** YYYY-MM-DD'")
    if not VERSION_RE.search(text):
        errors.append("missing '**Tool version/release checked:** ...'")
    if not DOCS_RE.search(text):
        errors.append("missing '**Official docs/manual:** ...'")
    if not SOURCE_RE.search(text):
        errors.append("missing '**Release/source:** ...'")
    return errors


def validate_all(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    taxonomy_skill = root / "skills" / "tracking-taxonomy-updates"
    if taxonomy_skill.is_dir():
        for relative in REQUIRED_SUPPLEMENTARY_DOCS:
            path = root / relative
            if not path.is_file():
                errors.append(f"{relative}: required supplementary document is missing")
    for path in supplementary_doc_files(root):
        for err in validate_doc(path):
            errors.append(f"{path.relative_to(root)}: {err}")
    skills_dir = root / "skills"
    if skills_dir.is_dir():
        for path in sorted(skills_dir.rglob("*")):
            if not path.is_file() or path.suffix not in {".md", ".py", ".sh"}:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for match in BANNED_ENV_COMMAND_RE.finditer(text):
                line = text[: match.start()].count("\n") + 1
                errors.append(
                    f"{path.relative_to(root)}:{line}: banned conda/mamba environment command"
                )
        for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
            text = skill_md.read_text(encoding="utf-8")
            match = re.search(
                r"^## Quality Gates\s*$\n(.*?)(?=^##\s|\Z)",
                text,
                re.MULTILINE | re.DOTALL,
            )
            if not match or not PINNED_PIXI_GATE_RE.search(match.group(1)):
                continue
            skill_dir = skill_md.parent
            if not (skill_dir / "pixi.toml").is_file() or not (skill_dir / "pixi.lock").is_file():
                errors.append(
                    f"{skill_md.relative_to(root)}: pinned Pixi quality gate requires "
                    "skill-local pixi.toml and pixi.lock"
                )
    return errors


def main() -> int:
    errors = validate_all()
    if errors:
        print("Supplementary doc validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1
    print("Supplementary doc validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
