#!/usr/bin/env python3
"""Install / uninstall the omics-skills routing-hint hook in the user's
Claude Code and Codex CLI settings. Idempotent: running twice is a no-op.

The hook runs `scripts/emit_routing_hint.py` on every user prompt so the
catalog actually gets consulted instead of only being advertised in agent
system prompts.

Usage:
  python3 scripts/install_hook.py install         # both Claude Code + Codex CLI
  python3 scripts/install_hook.py install --claude-only
  python3 scripts/install_hook.py install --codex-only
  python3 scripts/install_hook.py uninstall
  python3 scripts/install_hook.py status
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
import tempfile
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_SCRIPT = REPO_ROOT / "scripts" / "emit_routing_hint.py"
MARKER = "omics-skills-autoroute"

CLAUDE_SETTINGS = Path.home() / ".claude" / "settings.json"
CODEX_HOOKS = Path.home() / ".codex" / "hooks.json"
CODEX_CONFIG = Path.home() / ".codex" / "config.toml"

# Anchor pattern: shlex-quoted interpreter + quoted hook script path +
# trailing end-of-line marker. Matching the full pattern (not just the
# bare MARKER substring) avoids false positives when a user's existing
# hook happens to mention "omics-skills" elsewhere in the config.
HOOK_CMD_CLAUDE = f"{shlex.quote(sys.executable)} {shlex.quote(str(HOOK_SCRIPT))} --platform claude  # {MARKER}"
HOOK_CMD_CODEX = f"{shlex.quote(sys.executable)} {shlex.quote(str(HOOK_SCRIPT))} --platform codex  # {MARKER}"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    return json.loads(text)


def atomic_write_json(path: Path, payload: dict) -> None:
    """Write `payload` as pretty JSON atomically so a concurrent reader
    never sees a half-written file and so a crash mid-write can't leave
    the settings unusable."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    try:
        tmp.write(json.dumps(payload, indent=2) + "\n")
        tmp.flush()
        os.fsync(tmp.fileno())
    finally:
        tmp.close()
    os.replace(tmp.name, path)


def ensure_hooks_skeleton(payload: dict) -> list[dict]:
    """Return payload['hooks']['UserPromptSubmit'], coercing missing or
    wrong-typed intermediates to {} / [] so later appends do not crash on
    hand-edited settings files."""
    hooks = payload.get("hooks")
    if not isinstance(hooks, dict):
        hooks = {}
        payload["hooks"] = hooks
    user_prompt = hooks.get("UserPromptSubmit")
    if not isinstance(user_prompt, list):
        user_prompt = []
        hooks["UserPromptSubmit"] = user_prompt
    return user_prompt


def marker_in_entry(entry: dict) -> bool:
    for hook in entry.get("hooks", []) if isinstance(entry, dict) else []:
        if not isinstance(hook, dict):
            continue
        command = hook.get("command", "")
        # Structural anchor: must mention both the marker comment AND the
        # hook script path. Guards against incidental `omics-skills` mentions.
        if MARKER in command and str(HOOK_SCRIPT) in command:
            return True
    return False


def install_common(settings_path: Path, hook_command: str) -> str:
    """Shared install path used for both Claude Code and Codex CLI: their
    UserPromptSubmit hook contracts (stdin JSON with a `prompt` field,
    `hookSpecificOutput.additionalContext` out) are identical. The same
    JSON settings shape is valid in both files."""
    payload = load_json(settings_path)
    user_prompt = ensure_hooks_skeleton(payload)
    if any(marker_in_entry(entry) for entry in user_prompt):
        return "already installed"
    user_prompt.append(
        {
            "matcher": "",
            "hooks": [
                {"type": "command", "command": hook_command},
            ],
        }
    )
    atomic_write_json(settings_path, payload)
    return f"installed in {settings_path}"


def uninstall_common(settings_path: Path) -> str:
    if not settings_path.exists():
        return "nothing to do (no settings file)"
    payload = load_json(settings_path)
    hooks = payload.get("hooks") if isinstance(payload.get("hooks"), dict) else {}
    user_prompt = hooks.get("UserPromptSubmit") if isinstance(hooks.get("UserPromptSubmit"), list) else []
    cleaned_entries: list[dict] = []
    removed = 0
    for entry in user_prompt:
        if not isinstance(entry, dict):
            cleaned_entries.append(entry)
            continue
        remaining = [
            hook
            for hook in entry.get("hooks", [])
            if not (
                isinstance(hook, dict)
                and MARKER in hook.get("command", "")
                and str(HOOK_SCRIPT) in hook.get("command", "")
            )
        ]
        if len(remaining) != len(entry.get("hooks", [])):
            removed += 1
        if remaining:
            entry["hooks"] = remaining
            cleaned_entries.append(entry)
    if removed == 0:
        return "not installed"
    if cleaned_entries:
        hooks["UserPromptSubmit"] = cleaned_entries
    else:
        hooks.pop("UserPromptSubmit", None)
    if hooks:
        payload["hooks"] = hooks
    else:
        payload.pop("hooks", None)
    atomic_write_json(settings_path, payload)
    return f"uninstalled {removed} entry(ies) from {settings_path}"


def install_claude() -> str:
    return install_common(CLAUDE_SETTINGS, HOOK_CMD_CLAUDE)


def uninstall_claude() -> str:
    return uninstall_common(CLAUDE_SETTINGS)


FEATURES_HEADER = re.compile(r"^[ \t]*\[features\][ \t]*$", re.MULTILINE)
CODEX_HOOKS_KEY = re.compile(r"^[ \t]*codex_hooks[ \t]*=.*$", re.MULTILINE)


def codex_flag_enabled() -> bool:
    """True only when `[features] codex_hooks` really is `true`."""
    if not CODEX_CONFIG.exists():
        return False
    try:
        config = tomllib.loads(CODEX_CONFIG.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return False
    return config.get("features", {}).get("codex_hooks") is True


def set_codex_hooks_true(text: str) -> str:
    """Return `text` with `[features] codex_hooks = true`. Replaces an existing
    key in that table instead of appending a second one, which would make the
    file unparseable."""
    header = FEATURES_HEADER.search(text)
    if header is None:
        return text.rstrip() + ("\n\n" if text.strip() else "") + "[features]\ncodex_hooks = true\n"
    next_table = re.compile(r"^[ \t]*\[", re.MULTILINE).search(text, header.end())
    end = next_table.start() if next_table else len(text)
    existing = CODEX_HOOKS_KEY.search(text, header.end(), end)
    if existing:
        # Replace the value, not the line: a trailing comment is the user's note.
        line = existing.group(0)
        comment = line[line.index("#"):] if "#" in line.split("=", 1)[1] else ""
        replacement = "codex_hooks = true" + (f" {comment}" if comment else "")
        return text[: existing.start()] + replacement + text[existing.end() :]
    return text[: header.end()] + "\ncodex_hooks = true" + text[header.end() :]


def enable_codex_feature_flag() -> str:
    """Codex CLI gates the hook system behind `[features] codex_hooks = true`
    in ~/.codex/config.toml. Never write a file tomllib cannot parse: this is
    the user's own config, not ours."""
    CODEX_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    text = CODEX_CONFIG.read_text(encoding="utf-8") if CODEX_CONFIG.exists() else ""
    try:
        current = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        return f"left {CODEX_CONFIG} alone: it is not valid TOML ({exc})"
    if current.get("features", {}).get("codex_hooks") is True:
        return "feature flag already set"
    new_text = set_codex_hooks_true(text)
    try:
        parsed = tomllib.loads(new_text)
    except tomllib.TOMLDecodeError as exc:
        return f"left {CODEX_CONFIG} alone: edit would break it ({exc})"
    # Verify the flag, not just that the file still parses. A `[features]` header
    # inside a multi-line string, for instance, is text we must not treat as a table.
    if parsed.get("features", {}).get("codex_hooks") is not True:
        return (
            f"could not enable the flag in {CODEX_CONFIG}; "
            "set [features] codex_hooks = true by hand"
        )
    CODEX_CONFIG.write_text(new_text, encoding="utf-8")
    return f"enabled in {CODEX_CONFIG}"


def install_codex() -> str:
    hooks_result = install_common(CODEX_HOOKS, HOOK_CMD_CODEX)
    flag_result = enable_codex_feature_flag()
    return f"{hooks_result}; {flag_result}"


def uninstall_codex() -> str:
    return uninstall_common(CODEX_HOOKS)


def status() -> None:
    def installed(path: Path) -> bool:
        if not path.exists():
            return False
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return False
        hooks = payload.get("hooks") if isinstance(payload.get("hooks"), dict) else {}
        user_prompt = hooks.get("UserPromptSubmit") if isinstance(hooks.get("UserPromptSubmit"), list) else []
        return any(marker_in_entry(entry) for entry in user_prompt if isinstance(entry, dict))

    # Parse the config rather than grepping it: a text search reports "on" for
    # `[unrelated] codex_hooks = true` and "off" for a trailing comment.
    flag_enabled = codex_flag_enabled()
    print(f"Claude Code ({CLAUDE_SETTINGS}): {'installed' if installed(CLAUDE_SETTINGS) else 'not installed'}")
    print(
        f"Codex CLI  ({CODEX_HOOKS}): {'installed' if installed(CODEX_HOOKS) else 'not installed'}"
        f"  [feature flag: {'on' if flag_enabled else 'off'}]"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    install = sub.add_parser("install", help="Install the routing hook.")
    install.add_argument("--claude-only", action="store_true")
    install.add_argument("--codex-only", action="store_true")
    sub.add_parser("uninstall", help="Remove the routing hook.")
    sub.add_parser("status", help="Show install state for each runtime.")
    args = parser.parse_args(argv)

    if args.command == "status":
        status()
        return 0

    if args.command == "install":
        targets = []
        if not args.codex_only:
            targets.append(("Claude Code", install_claude))
        if not args.claude_only:
            targets.append(("Codex CLI", install_codex))
        for label, fn in targets:
            print(f"{label}: {fn()}")
        return 0

    if args.command == "uninstall":
        print(f"Claude Code: {uninstall_claude()}")
        print(f"Codex CLI: {uninstall_codex()}")
        return 0

    parser.error(f"Unknown command {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
