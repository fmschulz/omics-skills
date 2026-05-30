from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class InstallSelectedIntegrationTests(unittest.TestCase):
    def run_make(self, home: Path, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["NO_COLOR"] = "1"
        return subprocess.run(
            ["make", "--no-print-directory", *args],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=True,
        )

    def run_installed_route(self, home: Path, task: str) -> dict[str, object]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        route = subprocess.run(
            [
                sys.executable,
                str(home / ".agents" / "omics-skills" / "skill_index.py"),
                "route",
                task,
                "--platform",
                "codex",
                "--json",
            ],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(route.stdout)

    def run_uninstall_script(self, home: Path) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["NO_COLOR"] = "1"
        return subprocess.run(
            [str(REPO_ROOT / "scripts" / "uninstall.sh")],
            cwd=REPO_ROOT,
            env=env,
            input="y\n",
            text=True,
            capture_output=True,
            check=True,
        )

    def assert_selected_install_routes_only_selected_components(self, install_method: str) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            self.run_make(
                home,
                "install-selected",
                f"INSTALL_METHOD={install_method}",
                "SELECTED_AGENT_FILES=science-writer.md",
                "SELECTED_SKILL_DIRS=bio-logic scientific-writing",
                "VERBOSE=1",
            )

            index_root = home / ".agents" / "omics-skills"
            catalog = json.loads((index_root / "catalog.json").read_text(encoding="utf-8"))
            self.assertEqual(catalog["metadata"]["agent_count"], 1)
            self.assertEqual(catalog["metadata"]["skill_count"], 2)
            self.assertEqual([agent["name"] for agent in catalog["agents"]], ["science-writer"])
            self.assertEqual(
                [skill["name"] for skill in catalog["skills"]],
                ["bio-logic", "scientific-writing"],
            )
            if install_method == "symlink":
                self.assertFalse(
                    (index_root / "catalog.json").is_symlink(),
                    "selected symlink installs must copy the temporary subset catalog",
                )

            off_subset = self.run_installed_route(home, "assemble a metagenome and recover MAGs")
            self.assertEqual(off_subset["primary_skills"], [])
            self.assertNotIn("bio-assembly-qc", off_subset["ordered_skills"])
            self.assertNotEqual(off_subset["agent"], "omics-scientist")

            writing = self.run_installed_route(home, "write the methods section of a manuscript")
            self.assertEqual(writing["agent"], "science-writer")
            self.assertIn("scientific-writing", writing["primary_skills"])
            self.assertLessEqual(set(writing["ordered_skills"]), {"bio-logic", "scientific-writing"})
            for path in writing["skill_paths"].values():
                self.assertTrue(str(path).startswith(str(home)))
                self.assertTrue(Path(str(path)).exists())

    def test_selected_symlink_install_uses_subset_catalog(self) -> None:
        self.assert_selected_install_routes_only_selected_components("symlink")

    def test_selected_copy_install_uses_subset_catalog(self) -> None:
        self.assert_selected_install_routes_only_selected_components("copy")

    def test_selected_skills_only_install_uses_agentless_subset_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            self.run_make(
                home,
                "install-selected",
                "INSTALL_METHOD=symlink",
                "SELECTED_AGENT_FILES=",
                "SELECTED_SKILL_DIRS=scientific-writing",
            )

            index_root = home / ".agents" / "omics-skills"
            catalog = json.loads((index_root / "catalog.json").read_text(encoding="utf-8"))
            self.assertEqual(catalog["metadata"]["agent_count"], 0)
            self.assertEqual(catalog["metadata"]["skill_count"], 1)
            self.assertEqual(catalog["agents"], [])
            self.assertEqual([skill["name"] for skill in catalog["skills"]], ["scientific-writing"])

            route = self.run_installed_route(home, "write manuscript methods")
            self.assertIsNone(route["agent"])
            self.assertLessEqual(set(route["ordered_skills"]), {"scientific-writing"})
            self.assertNotIn("bio-assembly-qc", route["ordered_skills"])

    def test_uninstall_all_removes_runtime_skills_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            self.run_make(
                home,
                "install-selected",
                "INSTALL_METHOD=symlink",
                "SELECTED_AGENT_FILES=science-writer.md",
                "SELECTED_SKILL_DIRS=scientific-writing",
            )
            self.assertTrue((home / ".claude" / "skills").is_symlink())
            self.assertTrue((home / ".codex" / "skills").is_symlink())

            self.run_make(home, "uninstall-all")

            self.assertFalse((home / ".claude" / "skills").is_symlink())
            self.assertFalse((home / ".codex" / "skills").is_symlink())
            self.assertFalse((home / ".agents" / "omics-skills").exists())

    def test_uninstall_script_removes_runtime_skills_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            self.run_make(
                home,
                "install-selected",
                "INSTALL_METHOD=symlink",
                "SELECTED_AGENT_FILES=science-writer.md",
                "SELECTED_SKILL_DIRS=scientific-writing",
            )
            self.assertTrue((home / ".claude" / "skills").is_symlink())
            self.assertTrue((home / ".codex" / "skills").is_symlink())

            self.run_uninstall_script(home)

            self.assertFalse((home / ".claude" / "skills").is_symlink())
            self.assertFalse((home / ".codex" / "skills").is_symlink())
            self.assertFalse((home / ".agents" / "omics-skills").exists())


if __name__ == "__main__":
    unittest.main()
