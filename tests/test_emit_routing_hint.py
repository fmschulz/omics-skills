"""Tests for the routing hint hook script + the install_hook installer.
The hook script must never block a user prompt: broken catalog, empty
prompt, opt-out env var, etc., all exit 0."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_SCRIPT = REPO_ROOT / "scripts" / "emit_routing_hint.py"
INSTALLER = REPO_ROOT / "scripts" / "install_hook.py"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import install_hook  # noqa: E402


def run_hook(stdin: str, *args: str, env_overrides: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, str(HOOK_SCRIPT), *args],
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
    )


class HookScriptTests(unittest.TestCase):
    def test_empty_stdin_exits_clean(self) -> None:
        result = run_hook("")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def test_opt_out_env_var_exits_silently(self) -> None:
        payload = json.dumps({"prompt": "assemble a metagenome and recover MAGs"})
        result = run_hook(payload, env_overrides={"OMICS_SKILLS_AUTOROUTE": "0"})
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")

    def test_json_mode_emits_hookSpecificOutput(self) -> None:
        payload = json.dumps({"prompt": "assemble a metagenome and recover MAGs"})
        result = run_hook(payload)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        parsed = json.loads(result.stdout)
        self.assertIn("hookSpecificOutput", parsed)
        inner = parsed["hookSpecificOutput"]
        self.assertEqual(inner["hookEventName"], "UserPromptSubmit")
        self.assertIn("bio-assembly-qc", inner["additionalContext"])
        self.assertIn("omics-scientist", inner["additionalContext"])

    def test_text_mode_emits_plain_markdown(self) -> None:
        payload = json.dumps({"prompt": "assemble a metagenome and recover MAGs"})
        result = run_hook(payload, "--text")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Routing hint", result.stdout)
        self.assertIn("bio-assembly-qc", result.stdout)

    def test_prompt_flag_bypasses_stdin(self) -> None:
        result = run_hook("", "--text", "--prompt", "find recent arxiv preprints on protein language models")
        self.assertEqual(result.returncode, 0)
        self.assertIn("arxiv-search", result.stdout)
        self.assertIn("literature-expert", result.stdout)

    def test_bare_prompt_input_not_json(self) -> None:
        # Some harnesses pass the prompt as plain text on stdin.
        result = run_hook("assemble a metagenome and recover MAGs", "--text")
        self.assertEqual(result.returncode, 0)
        self.assertIn("bio-assembly-qc", result.stdout)

    def test_no_routing_match_emits_nothing(self) -> None:
        # A deliberately off-topic query should surface no hint at all.
        result = run_hook(json.dumps({"prompt": "tell me a joke"}), "--text")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")


class InstallerTests(unittest.TestCase):
    def test_install_and_uninstall_are_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            with patch.object(install_hook, "CLAUDE_SETTINGS", home / ".claude" / "settings.json"), \
                 patch.object(install_hook, "CODEX_HOOKS", home / ".codex" / "hooks.toml"):
                first = install_hook.install_claude()
                second = install_hook.install_claude()
                self.assertIn("installed", first)
                self.assertIn("already installed", second)

                payload = json.loads(install_hook.CLAUDE_SETTINGS.read_text())
                entries = payload["hooks"]["UserPromptSubmit"]
                marker_hooks = [
                    hook
                    for entry in entries
                    for hook in entry.get("hooks", [])
                    if install_hook.MARKER in hook.get("command", "")
                ]
                self.assertEqual(len(marker_hooks), 1)

                removed = install_hook.uninstall_claude()
                self.assertIn("uninstalled", removed)
                no_op = install_hook.uninstall_claude()
                self.assertIn("not installed", no_op)

    def test_codex_install_writes_hooks_json_and_feature_flag(self) -> None:
        """Codex CLI expects `~/.codex/hooks.json` (same UserPromptSubmit
        schema as Claude Code) plus `[features] codex_hooks = true` in
        `config.toml`. Both must be idempotent and round-trip cleanly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            codex_dir = Path(tmpdir) / ".codex"
            hooks_path = codex_dir / "hooks.json"
            config_path = codex_dir / "config.toml"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text("[persistence]\nenabled = true\n", encoding="utf-8")

            with patch.object(install_hook, "CODEX_HOOKS", hooks_path), \
                 patch.object(install_hook, "CODEX_CONFIG", config_path):
                first = install_hook.install_codex()
                self.assertIn("installed in", first)
                payload = json.loads(hooks_path.read_text(encoding="utf-8"))
                entries = payload["hooks"]["UserPromptSubmit"]
                self.assertEqual(len(entries), 1)

                toml_text = config_path.read_text(encoding="utf-8")
                self.assertIn("[features]", toml_text)
                self.assertIn("codex_hooks = true", toml_text)
                # Pre-existing section must survive intact.
                self.assertIn("[persistence]", toml_text)

                second = install_hook.install_codex()
                self.assertIn("already installed", second)

                install_hook.uninstall_codex()
                payload_after = json.loads(hooks_path.read_text(encoding="utf-8"))
                self.assertNotIn("hooks", payload_after)

    def test_claude_install_survives_hand_edited_nonstandard_types(self) -> None:
        """If a user has scribbled `hooks: []` or missing keys into their
        settings, the installer must coerce to the right shape instead of
        crashing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = Path(tmpdir) / "settings.json"
            settings.write_text(
                json.dumps({"hooks": [], "unrelated": {"keep": "me"}}),
                encoding="utf-8",
            )
            with patch.object(install_hook, "CLAUDE_SETTINGS", settings):
                result = install_hook.install_claude()
                self.assertIn("installed in", result)
                payload = json.loads(settings.read_text())
                self.assertEqual(payload["unrelated"], {"keep": "me"})
                self.assertIn("UserPromptSubmit", payload["hooks"])


if __name__ == "__main__":
    unittest.main()
