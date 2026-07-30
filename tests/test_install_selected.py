from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import tomllib
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

    def run_install_script(
        self, home: Path, *args: str
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["NO_COLOR"] = "1"
        return subprocess.run(
            [str(REPO_ROOT / "scripts" / "install.sh"), *args],
            cwd=REPO_ROOT,
            env=env,
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

            claude_agent = home / ".claude" / "agents" / "science-writer.md"
            codex_agent = home / ".codex" / "agents" / "science-writer.toml"
            self.assertTrue(claude_agent.exists())
            self.assertTrue(codex_agent.exists())
            self.assertFalse((home / ".codex" / "agents" / "science-writer.md").exists())
            parsed_agent = tomllib.loads(codex_agent.read_text(encoding="utf-8"))
            self.assertEqual(parsed_agent["name"], "science-writer")
            self.assertIn("developer_instructions", parsed_agent)

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

    def test_clean_preserves_unrelated_backups(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            unrelated_files = [
                home / ".claude" / "agents" / "unrelated.md.bak",
                home / ".codex" / "agents" / "unrelated.toml.bak",
            ]
            unrelated_dir = home / ".agents" / "skills" / "unrelated.bak"
            for path in unrelated_files:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("keep\n", encoding="utf-8")
            unrelated_dir.mkdir(parents=True)

            self.run_make(home, "clean")

            for path in unrelated_files:
                self.assertTrue(path.exists(), f"clean removed unrelated backup {path}")
            self.assertTrue(unrelated_dir.exists())

    def test_missing_selected_skill_fails_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["NO_COLOR"] = "1"
            result = subprocess.run(
                [
                    "make",
                    "--no-print-directory",
                    "install-skills",
                    "SELECTED_SKILL_DIRS=not-a-real-skill",
                ],
                cwd=REPO_ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not-a-real-skill not found", result.stdout)

    def test_install_prunes_retired_symlink_from_previous_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            catalog_dir = home / ".agents" / "omics-skills"
            skills_dir = home / ".agents" / "skills"
            catalog_dir.mkdir(parents=True)
            skills_dir.mkdir(parents=True)
            (catalog_dir / "catalog.json").write_text("not json\n", encoding="utf-8")
            retired = skills_dir / "get-api-docs"
            retired.symlink_to(REPO_ROOT / "skills" / "get-api-docs")

            self.run_make(
                home,
                "install-skills",
                "SELECTED_SKILL_DIRS=bio-logic",
            )

            self.assertFalse(retired.exists())
            self.assertFalse(retired.is_symlink())
            self.assertTrue((skills_dir / "bio-logic").exists())

    def test_install_archives_retired_copy_outside_active_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            catalog_dir = home / ".agents" / "omics-skills"
            skills_dir = home / ".agents" / "skills"
            retired = skills_dir / "get-api-docs"
            catalog_dir.mkdir(parents=True)
            retired.mkdir(parents=True)
            (catalog_dir / "catalog.json").write_text(
                json.dumps({"skills": [{"name": "bio-logic"}]}) + "\n",
                encoding="utf-8",
            )
            (retired / "SKILL.md").write_text(
                "---\nname: get-api-docs\ndescription: retired fixture\n---\n",
                encoding="utf-8",
            )

            self.run_make(
                home,
                "install-skills",
                "SELECTED_SKILL_DIRS=bio-logic",
            )

            self.assertFalse(retired.exists())
            archived = catalog_dir / "retired-skills" / "get-api-docs"
            self.assertTrue((archived / "SKILL.md").is_file())

    def test_install_archives_replaced_skill_outside_active_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            skills_dir = home / ".agents" / "skills"
            existing = skills_dir / "bio-logic"
            existing.mkdir(parents=True)
            (existing / "SKILL.md").write_text(
                "---\nname: bio-logic\ndescription: old copy\n---\n",
                encoding="utf-8",
            )

            self.run_make(
                home,
                "install-skills",
                "INSTALL_METHOD=copy",
                "SELECTED_SKILL_DIRS=bio-logic",
            )

            self.assertTrue((existing / "SKILL.md").is_file())
            previous = home / ".agents" / "omics-skills" / "previous-skills"
            backups = list(previous.glob("bio-logic.*"))
            self.assertEqual(len(backups), 1)
            self.assertIn("old copy", (backups[0] / "SKILL.md").read_text(encoding="utf-8"))
            self.assertEqual(list(skills_dir.glob("bio-logic.bak*")), [])

    def test_install_archives_recognized_legacy_backup_outside_active_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            skills_dir = home / ".agents" / "skills"
            legacy = skills_dir / "bio-logic.bak"
            legacy.mkdir(parents=True)
            (legacy / "SKILL.md").write_text(
                "---\nname: bio-logic\ndescription: legacy copy\n---\n",
                encoding="utf-8",
            )
            unrelated = skills_dir / "unrelated.bak"
            unrelated.mkdir()

            self.run_make(
                home,
                "install-skills",
                "SELECTED_SKILL_DIRS=bio-logic",
            )

            self.assertFalse(legacy.exists())
            archived = (
                home
                / ".agents"
                / "omics-skills"
                / "previous-skills"
                / "bio-logic.bak"
                / "SKILL.md"
            )
            self.assertTrue(archived.is_file())
            self.assertTrue(unrelated.is_dir())

    def test_shell_installer_archives_replaced_skill_outside_active_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            existing = home / ".agents" / "skills" / "bio-logic"
            existing.mkdir(parents=True)
            (existing / "SKILL.md").write_text(
                "---\nname: bio-logic\ndescription: old shell copy\n---\n",
                encoding="utf-8",
            )

            self.run_install_script(home, "--copy")

            previous = home / ".agents" / "omics-skills" / "previous-skills"
            backups = list(previous.glob("bio-logic.*"))
            self.assertEqual(len(backups), 1)
            self.assertIn(
                "old shell copy",
                (backups[0] / "SKILL.md").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                list((home / ".agents" / "skills").glob("bio-logic.bak*")),
                [],
            )

    def test_install_leaves_foreign_retired_symlink_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            catalog_dir = home / ".agents" / "omics-skills"
            skills_dir = home / ".agents" / "skills"
            foreign_dir = home / "foreign" / "skills"
            catalog_dir.mkdir(parents=True)
            skills_dir.mkdir(parents=True)
            foreign_dir.mkdir(parents=True)
            (catalog_dir / "catalog.json").write_text(
                json.dumps({"skills": [{"name": "bio-logic"}]}) + "\n",
                encoding="utf-8",
            )
            retired = skills_dir / "get-api-docs"
            retired.symlink_to(foreign_dir / "get-api-docs")

            result = self.run_make(
                home,
                "install-skills",
                "SELECTED_SKILL_DIRS=bio-logic",
            )

            self.assertTrue(retired.is_symlink())
            self.assertIn("left unexpected symlink untouched", result.stdout)

    def test_install_leaves_name_mismatched_directory_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            catalog_dir = home / ".agents" / "omics-skills"
            retired = home / ".agents" / "skills" / "get-api-docs"
            catalog_dir.mkdir(parents=True)
            retired.mkdir(parents=True)
            (catalog_dir / "catalog.json").write_text(
                json.dumps({"skills": [{"name": "bio-logic"}]}) + "\n",
                encoding="utf-8",
            )
            (retired / "SKILL.md").write_text(
                "---\nname: user-owned-skill\ndescription: keep\n---\n",
                encoding="utf-8",
            )

            result = self.run_make(
                home,
                "install-skills",
                "SELECTED_SKILL_DIRS=bio-logic",
            )

            self.assertTrue((retired / "SKILL.md").is_file())
            self.assertIn("left unrecognized directory untouched", result.stdout)


if __name__ == "__main__":
    unittest.main()
