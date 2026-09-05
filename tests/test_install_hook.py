"""`make install-hook` edits the user's own ~/.codex/config.toml. The earlier
regex insert appended a second `codex_hooks` key whenever one was already set
to false, which makes the whole file unparseable and breaks the Codex CLI.
These tests pin the pure text transform; they never touch a real config."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "install_hook.py"
SPEC = importlib.util.spec_from_file_location("install_hook", MODULE_PATH)
install_hook = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = install_hook
SPEC.loader.exec_module(install_hook)


CONFIGS = {
    "empty file": "",
    "flag already false": "[features]\ncodex_hooks = false\n",
    "flag already true": "[features]\ncodex_hooks = true\n",
    "features table with other keys": (
        '[features]\nmulti_agent_v2 = true\ncodex_hooks = false\n\n'
        '[projects."/repo"]\ntrust_level = "trusted"\n'
    ),
    "no features table": 'model = "example"\n\n[projects."/repo"]\ntrust_level = "trusted"\n',
    "features table without the key": 'model = "example"\n\n[features]\nmulti_agent_v2 = true\n',
    "same key name in another table": "[other]\ncodex_hooks = false\n\n[features]\nmulti_agent_v2 = true\n",
}


class SetCodexHooksTrueTests(unittest.TestCase):
    def test_result_is_valid_toml_with_the_flag_enabled(self) -> None:
        for label, text in CONFIGS.items():
            with self.subTest(label):
                result = install_hook.set_codex_hooks_true(text)
                parsed = tomllib.loads(result)
                self.assertIs(parsed["features"]["codex_hooks"], True)

    def test_unrelated_tables_and_keys_survive(self) -> None:
        result = install_hook.set_codex_hooks_true(CONFIGS["same key name in another table"])
        parsed = tomllib.loads(result)
        self.assertIs(parsed["other"]["codex_hooks"], False)
        self.assertIs(parsed["features"]["multi_agent_v2"], True)

    def test_projects_block_is_preserved(self) -> None:
        result = install_hook.set_codex_hooks_true(CONFIGS["features table with other keys"])
        parsed = tomllib.loads(result)
        self.assertEqual(parsed["projects"]["/repo"]["trust_level"], "trusted")


class CodexFlagEnabledTests(unittest.TestCase):
    """Reading the flag by text search reported "on" for a key in the wrong
    table and "off" for a value with a trailing comment."""

    CASES = {
        "[features]\ncodex_hooks = true\n": True,
        "[features]\ncodex_hooks = true # enabled\n": True,
        "[unrelated]\ncodex_hooks = true\n": False,
        "[features]\ncodex_hooks = false\n": False,
        "": False,
        "not = valid = toml\n": False,
    }

    def test_flag_is_read_from_the_features_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config.toml"
            for text, expected in self.CASES.items():
                with self.subTest(text):
                    config.write_text(text, encoding="utf-8")
                    with patch.object(install_hook, "CODEX_CONFIG", config):
                        self.assertIs(install_hook.codex_flag_enabled(), expected)


if __name__ == "__main__":
    unittest.main()
