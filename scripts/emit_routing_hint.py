#!/usr/bin/env python3
"""Emit a compact routing hint for the current user prompt. Designed to be
wired as a Claude Code `UserPromptSubmit` hook or a Codex CLI pre-prompt
hook so the skill graph actually gets consulted instead of merely
advertised in agent prompts.

Hook input (Claude Code, stdin JSON):
  {"session_id": "...", "transcript_path": "...", "prompt": "..."}

Output contract:
  - Default: prints a `hookSpecificOutput` JSON object that Claude Code
    injects into context as `additionalContext`.
  - `--text` flag: emit the same hint as plain text for shells that
    cannot parse JSON. Useful for Codex CLI hooks.
  - Exits 0 even on routing errors so a broken catalog never blocks
    user prompts.

Opt-out: set `OMICS_SKILLS_AUTOROUTE=0` in the environment. The hook
exits silently in that case.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

DISABLED = {"0", "false", "no", "off"}


def load_skill_index():
    """Import skill_index lazily so a broken repo doesn't tank the hook."""
    import importlib

    return importlib.import_module("skill_index")


def format_hint(result: dict) -> str:
    """Render a compact, Markdown-ish block that fits in a few hundred
    tokens. Suppressed entirely when the router has no confident match."""
    agent = result.get("agent")
    primary = result.get("primary_skills") or []
    supporting = result.get("supporting_skills") or []
    ordered = result.get("ordered_skills") or []
    skill_paths = result.get("skill_paths") or {}
    if not primary:
        # No confident skill match. Suppress the hint entirely rather than
        # nudging the model toward whichever agent won by alphabetical
        # tiebreak on a zero-signal query.
        return ""
    lines = ["## Routing hint (omics-skills)"]
    if agent:
        lines.append(f"- Agent: `{agent}`")
    if primary:
        lines.append(f"- Primary skills: {', '.join(f'`/{s}`' for s in primary)}")
    if supporting:
        lines.append(f"- Supporting skills: {', '.join(f'`/{s}`' for s in supporting)}")
    if ordered and ordered != primary:
        lines.append(f"- Suggested order: {' → '.join(f'`/{s}`' for s in ordered)}")
    if skill_paths:
        lines.append("- Skill files:")
        for name, path in skill_paths.items():
            lines.append(f"  - `/{name}` → `{path}`")
    lines.append(
        "- Override with `OMICS_SKILLS_AUTOROUTE=0` or ignore if a specialist "
        "skill is not called out above."
    )
    return "\n".join(lines)


def run(prompt: str, platform: str) -> str:
    skill_index = load_skill_index()
    try:
        result = skill_index.route_request(
            task=prompt,
            agent=None,
            platform=platform,
            top_k=4,
            repo=None,
            index_root=None,
        )
    except SystemExit as exc:
        # No catalog found, etc. Never block the user prompt.
        return f"<!-- omics-skills routing hint skipped: {exc} -->"
    return format_hint(result)


def main(argv: list[str] | None = None) -> int:
    if os.environ.get("OMICS_SKILLS_AUTOROUTE", "").lower() in DISABLED:
        return 0

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--platform",
        default=os.environ.get("OMICS_SKILLS_PLATFORM", "generic"),
        choices=("claude", "codex", "generic"),
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help="Emit plain text instead of the Claude Code hookSpecificOutput JSON.",
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Use this string as the prompt instead of reading stdin JSON.",
    )
    args = parser.parse_args(argv)

    prompt = args.prompt
    if prompt is None:
        raw = sys.stdin.read().strip()
        if not raw:
            return 0
        try:
            payload = json.loads(raw)
            prompt = payload.get("prompt") or payload.get("user_message") or ""
        except json.JSONDecodeError:
            # Some harnesses pass the bare prompt, not JSON.
            prompt = raw
    if not prompt:
        return 0

    hint = run(prompt=prompt, platform=args.platform)
    if not hint:
        return 0

    if args.text:
        print(hint)
        return 0

    # Claude Code `UserPromptSubmit` contract: emit JSON with
    # hookSpecificOutput.additionalContext; Claude prepends it to the
    # user prompt before the main model sees it.
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": hint,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
