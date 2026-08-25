#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["PyYAML==6.0.3"]
# ///
"""Validate every skills/<name>/SKILL.md: frontmatter name matches the
directory, name is a valid slug, required sections are present, and the file
stays within the length budget.

Importable (validate_skill / validate_all) so the checks are unit-testable, and
runnable as a CLI for CI and the install smoke test."""
from __future__ import annotations

import re
import shlex
import sys
from pathlib import Path
from urllib.parse import unquote

import yaml

REQUIRED_SECTIONS = [
    "## Instructions",
    "## Input Requirements",
    "## Output",
    "## Quality Gates",
]
MAX_LINES = 500
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 400
MAX_TOTAL_DESCRIPTION_LENGTH = 6500
SLUG_PATTERN = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
TRIGGER_PATTERN = re.compile(r"\b(?:use when|use for|trigger when)\b", re.IGNORECASE)
MARKDOWN_LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
CODE_FENCE_PATTERN = re.compile(r"```(?:bash|sh|shell)?\s*\n(.*?)```", re.DOTALL)
INLINE_CODE_PATTERN = re.compile(r"`([^`\n]+)`")
OUTPUT_EXTENSIONS = {
    "aln",
    "bam",
    "bed",
    "csv",
    "db",
    "duckdb",
    "fa",
    "faa",
    "fasta",
    "fastq",
    "fq",
    "gff",
    "gff3",
    "html",
    "ipynb",
    "json",
    "jsonl",
    "log",
    "md",
    "nwk",
    "parquet",
    "pdf",
    "phy",
    "png",
    "sam",
    "svg",
    "treefile",
    "tsv",
    "txt",
    "yaml",
    "yml",
}


def split_frontmatter(text: str) -> tuple[dict[str, object], str]:
    """Parse YAML frontmatter and return it with the Markdown body."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end < 0:
        raise yaml.YAMLError("unterminated frontmatter")
    parsed = yaml.safe_load(text[4:end]) or {}
    if not isinstance(parsed, dict):
        raise yaml.YAMLError("frontmatter must be a mapping")
    return parsed, text[end + 4 :]


def local_link_targets(text: str) -> list[str]:
    """Return relative Markdown link targets that should exist on disk."""
    targets: list[str] = []
    for raw_target in MARKDOWN_LINK_PATTERN.findall(text):
        target = raw_target.strip()
        if target.startswith("<") and ">" in target:
            target = target[1 : target.index(">")]
        else:
            target = target.split(maxsplit=1)[0]
        target = unquote(target).split("#", 1)[0]
        if not target or target.startswith(("#", "/", "http://", "https://", "mailto:", "data:")):
            continue
        targets.append(target)
    return targets


def section(text: str, heading: str) -> str:
    match = re.search(
        rf"^{re.escape(heading)}\s*$\n(.*?)(?=^##\s|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    return match.group(1) if match else ""


def fenced_commands(text: str) -> list[str]:
    commands: list[str] = []
    for block in CODE_FENCE_PATTERN.findall(text):
        current = ""
        for raw_line in block.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            current = f"{current} {line}".strip()
            if current.endswith("\\"):
                current = current[:-1].rstrip()
                continue
            if "uv run" in current or re.search(r"(?:^|\s)python3?\s", current):
                commands.append(current)
            current = ""
    return commands


def command_script(command: str) -> str | None:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None
    for index, token in enumerate(tokens):
        if token == "--script" and index + 1 < len(tokens):
            return tokens[index + 1]
        if token in {"python", "python3"} and index + 1 < len(tokens):
            candidate = tokens[index + 1]
            if candidate != "-m":
                return candidate
    return None


def resolve_script_path(skill_dir: Path, raw_path: str) -> Path | None:
    if any(marker in raw_path for marker in ("$", "<", ">")):
        return None
    installed_prefix = f"~/.agents/skills/{skill_dir.name}/"
    if raw_path.startswith(installed_prefix):
        return skill_dir / raw_path.removeprefix(installed_prefix)
    if raw_path.startswith("skills/"):
        return skill_dir.parent.parent / raw_path
    if raw_path.startswith("/"):
        return Path(raw_path)
    return skill_dir / raw_path


def has_pep723_dependencies(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    metadata = re.search(
        r"^#\s*///\s+script\s*$\n(.*?)^#\s*///\s*$",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not metadata:
        return False
    dependencies = re.search(
        r"dependencies\s*=\s*\[(.*?)\]",
        metadata.group(1),
        re.DOTALL,
    )
    return bool(dependencies and re.search(r"[\"'][^\"']+[\"']", dependencies.group(1)))


def validate_documented_commands(skill_dir: Path, text: str) -> list[str]:
    errors: list[str] = []
    for command in fenced_commands(text):
        raw_script = command_script(command)
        if not raw_script:
            continue
        path = resolve_script_path(skill_dir, raw_script)
        if path is None:
            continue
        if not path.is_file():
            errors.append(f"documented command script is missing ({raw_script})")
            continue
        if (
            re.search(r"\buv\s+run\b.*\s--no-project\b.*\spython3?\s", command)
            and has_pep723_dependencies(path)
        ):
            errors.append(
                f"documented command bypasses PEP 723 dependencies; use uv run --script ({raw_script})"
            )
    return errors


def output_artifacts(text: str) -> list[tuple[str, str]]:
    artifacts: list[tuple[str, str]] = []
    for line in section(text, "## Output").splitlines():
        if "agent-authored" in line.lower():
            continue
        for token in INLINE_CODE_PATTERN.findall(line):
            clean = token.strip().rstrip(".,;:")
            if clean.startswith("."):
                continue
            suffix = clean.rsplit(".", 1)[-1].lower() if "." in clean else ""
            if suffix in OUTPUT_EXTENSIONS:
                artifacts.append((clean, line.strip()))
    return artifacts


def validate_output_contract(skill_dir: Path, text: str) -> list[str]:
    scripts_dir = skill_dir / "scripts"
    script_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in sorted(scripts_dir.rglob("*"))
        if path.is_file()
    ) if scripts_dir.is_dir() else ""
    errors: list[str] = []
    for artifact, _line in output_artifacts(text):
        if (skill_dir / artifact).exists():
            continue
        literal = re.sub(r"<[^>]+>|\{[^}]+\}", "", artifact)
        if literal and literal not in script_text:
            errors.append(
                f"output artifact is not emitted by bundled scripts ({artifact}); "
                "mark it (agent-authored) when the agent creates it"
            )
    return errors


def validate_markdown_links(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    for markdown in sorted(skill_dir.rglob("*.md")):
        text = markdown.read_text(encoding="utf-8")
        for target in local_link_targets(text):
            if not (markdown.parent / target).resolve().exists():
                relative = markdown.relative_to(skill_dir)
                errors.append(f"{relative}: broken local Markdown link ({target})")
    return errors


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
    try:
        frontmatter, _ = split_frontmatter(text)
    except yaml.YAMLError as error:
        return [f"{name}: invalid YAML frontmatter ({error})"]
    fm_name = str(frontmatter.get("name") or "").strip()
    if fm_name != name:
        errors.append(f"{name}: frontmatter name mismatch ({fm_name})")
    if not SLUG_PATTERN.fullmatch(fm_name):
        errors.append(f"{name}: frontmatter name invalid ({fm_name})")
    if len(fm_name) > MAX_NAME_LENGTH:
        errors.append(f"{name}: frontmatter name too long ({len(fm_name)})")
    description = str(frontmatter.get("description") or "").strip()
    if not description:
        errors.append(f"{name}: missing frontmatter description")
    elif len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(
            f"{name}: frontmatter description over {MAX_DESCRIPTION_LENGTH} characters "
            f"({len(description)})"
        )
    elif not TRIGGER_PATTERN.search(description):
        errors.append(f"{name}: frontmatter description must say when to use the skill")
    missing = [heading for heading in REQUIRED_SECTIONS if heading not in text]
    if missing:
        errors.append(f"{name}: missing sections {missing}")
    for heading in REQUIRED_SECTIONS:
        if heading in text and not section(text, heading).strip():
            errors.append(f"{name}: empty section {heading}")
    line_count = len(text.splitlines())
    if line_count > MAX_LINES:
        errors.append(f"{name}: SKILL.md over {MAX_LINES} lines ({line_count})")
    errors.extend(f"{name}: {error}" for error in validate_markdown_links(skill_dir))
    errors.extend(f"{name}: {error}" for error in validate_documented_commands(skill_dir, text))
    errors.extend(f"{name}: {error}" for error in validate_output_contract(skill_dir, text))
    return errors


def validate_all(skills_dir: Path) -> list[str]:
    """Validate every skill directory under ``skills_dir``."""
    errors: list[str] = []
    total_description_length = 0
    for entry in sorted(skills_dir.iterdir()):
        if entry.is_dir():
            errors.extend(validate_skill(entry))
            skill_md = entry / "SKILL.md"
            if skill_md.exists():
                try:
                    frontmatter, _ = split_frontmatter(
                        skill_md.read_text(encoding="utf-8")
                    )
                except yaml.YAMLError:
                    continue
                total_description_length += len(
                    str(frontmatter.get("description") or "").strip()
                )
    if total_description_length > MAX_TOTAL_DESCRIPTION_LENGTH:
        errors.append(
            "skill descriptions exceed the repository discovery budget "
            f"({total_description_length}/{MAX_TOTAL_DESCRIPTION_LENGTH} characters)"
        )
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
