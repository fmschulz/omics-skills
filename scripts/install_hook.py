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


def enable_codex_feature_flag() -> str:
    """Codex CLI gates the hook system behind `[features] codex_hooks =
    true` in ~/.codex/config.toml. Insert it idempotently without a TOML
    library dependency — the file is small enough to edit by regex."""
    CODEX_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    text = CODEX_CONFIG.read_text(encoding="utf-8") if CODEX_CONFIG.exists() else ""
    if re.search(r"^\s*codex_hooks\s*=\s*true\s*$", text, re.MULTILINE):
        return "feature flag already set"
    if re.search(r"^\s*\[features\]\s*$", text, re.MULTILINE):
        new_text = re.sub(
            r"(^\s*\[features\]\s*$)",
            r"\1\ncodex_hooks = true",
            text,
            count=1,
            flags=re.MULTILINE,
        )
    else:
        block = "\n[features]\ncodex_hooks = true\n"
        new_text = text.rstrip() + ("\n" if text and not text.endswith("\n") else "") + block
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

    flag_enabled = False
    if CODEX_CONFIG.exists():
        flag_enabled = bool(
            re.search(
                r"^\s*codex_hooks\s*=\s*true\s*$",
                CODEX_CONFIG.read_text(encoding="utf-8"),
                re.MULTILINE,
            )
        )
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
