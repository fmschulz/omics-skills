#!/usr/bin/env python3
"""Render a repository Markdown agent as a Codex TOML agent definition."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Split the ``---`` frontmatter of an agent file from its body.

    Agent files hold single-line ``key: value`` entries, so nothing more is parsed.
    """
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    entries: dict[str, str] = {}
    for line in text[4:end].splitlines():
        key, separator, value = line.partition(":")
        if separator:
            entries[key.strip()] = value.strip().strip("\"'")
    return entries, text[end + 5 :]


def render_agent(source: Path) -> str:
    frontmatter, body = split_frontmatter(source.read_text(encoding="utf-8"))
    name = (frontmatter.get("name") or source.stem).strip()
    description = (frontmatter.get("description") or "").strip()
    instructions = body.strip()
    if not name or not description or not instructions:
        raise ValueError(f"{source}: agent requires name, description, and instructions")

    rendered = "\n".join(
        (
            f"name = {json.dumps(name)}",
            f"description = {json.dumps(description)}",
            f"developer_instructions = {json.dumps(instructions)}",
            "",
        )
    )
    tomllib.loads(rendered)
    return rendered


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Source agents/<name>.md file")
    parser.add_argument("output", type=Path, help="Destination <name>.toml file")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rendered = render_agent(args.source)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
