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

    def assert_selected_install_routes_only_selected_components(self, install_method: str) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            self.run_make(
                home,
                "install-selected",
                f"INSTALL_METHOD={install_method}",
                "SELECTED_AGENT_FILES=science-writer.md",
                "SELECTED_SKILL_DIRS=bio-logic proposal-review",
            )

            index_root = home / ".agents" / "omics-skills"
            catalog = json.loads((index_root / "catalog.json").read_text(encoding="utf-8"))
            self.assertEqual(catalog["metadata"]["agent_count"], 1)
            self.assertEqual(catalog["metadata"]["skill_count"], 2)
            self.assertEqual([agent["name"] for agent in catalog["agents"]], ["science-writer"])
            self.assertEqual(
                [skill["name"] for skill in catalog["skills"]],
                ["bio-logic", "proposal-review"],
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

            review = self.run_installed_route(
                home,
                "review a research proposal for methodological rigor and feasibility",
            )
            self.assertEqual(review["agent"], "science-writer")
            self.assertIn("proposal-review", review["primary_skills"])
            self.assertLessEqual(
                set(review["ordered_skills"]), {"bio-logic", "proposal-review"}
            )
            for path in review["skill_paths"].values():
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
                "SELECTED_SKILL_DIRS=proposal-review",
            )

            index_root = home / ".agents" / "omics-skills"
            catalog = json.loads((index_root / "catalog.json").read_text(encoding="utf-8"))
            self.assertEqual(catalog["metadata"]["agent_count"], 0)
            self.assertEqual(catalog["metadata"]["skill_count"], 1)
            self.assertEqual(catalog["agents"], [])
            self.assertEqual(
                [skill["name"] for skill in catalog["skills"]], ["proposal-review"]
            )

            route = self.run_installed_route(
                home, "review a research proposal for funding"
            )
            self.assertIsNone(route["agent"])
            self.assertLessEqual(set(route["ordered_skills"]), {"proposal-review"})
            self.assertNotIn("bio-assembly-qc", route["ordered_skills"])

    def test_uninstall_all_removes_runtime_skills_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            self.run_make(
                home,
                "install-selected",
                "INSTALL_METHOD=symlink",
                "SELECTED_AGENT_FILES=science-writer.md",
                "SELECTED_SKILL_DIRS=proposal-review",
            )
            self.assertTrue((home / ".claude" / "skills").is_symlink())
            self.assertTrue((home / ".codex" / "skills").is_symlink())

            self.run_make(home, "uninstall")

            self.assertFalse((home / ".claude" / "skills").is_symlink())
            self.assertFalse((home / ".codex" / "skills").is_symlink())
            self.assertFalse((home / ".agents" / "omics-skills").exists())

    def stage_skill_names(self) -> list[str]:
        return sorted(
            path.parent.name
            for path in (REPO_ROOT / "skills").glob("*/SKILL.md")
            if "disable-model-invocation: true" in path.read_text(encoding="utf-8")
        )

    def test_selecting_a_stage_installs_the_router_and_says_so(self) -> None:
        stages = self.stage_skill_names()
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            result = self.run_make(
                home,
                "install-selected",
                "SELECTED_AGENT_FILES=omics-scientist.md",
                "SELECTED_SKILL_DIRS=bio-logic bio-annotation",
            )

            added = [line for line in result.stderr.splitlines() if "expanded" in line]
            self.assertEqual(len(added), 1, result.stderr)
            self.assertIn("omics-pipeline", added[0])
            catalog = json.loads(
                (home / ".agents" / "omics-skills" / "catalog.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                [skill["name"] for skill in catalog["skills"]],
                sorted([*stages, "bio-logic", "omics-pipeline"]),
            )
            skills_dir = home / ".agents" / "skills"
            self.assertTrue((skills_dir / "omics-pipeline" / "SKILL.md").is_file())
            route = self.run_installed_route(
                home, "annotate proteins with eggnog-mapper"
            )
            self.assertEqual(route["primary_skills"][0], "omics-pipeline")

    def test_selecting_the_router_installs_every_stage_it_names(self) -> None:
        stages = self.stage_skill_names()
        self.assertGreater(len(stages), 10)
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            result = self.run_make(
                home,
                "install-selected",
                "SELECTED_AGENT_FILES=",
                "SELECTED_SKILL_DIRS=omics-pipeline",
            )

            skills_dir = home / ".agents" / "skills"
            for name in stages:
                self.assertTrue((skills_dir / name / "SKILL.md").is_file(), name)
            added = [line for line in result.stderr.splitlines() if "expanded" in line]
            self.assertEqual(len(added), 1, result.stderr)

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
                json.dumps(
                    {"skills": [{"name": "bio-logic"}, {"name": "get-api-docs"}]}
                )
                + "\n",
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

    def test_install_archives_a_retired_skills_legacy_backup(self) -> None:
        """A backup of a skill that was just retired is ours too. Matching only
        against skills still on disk stranded `jgi-lakehouse.bak` beside the
        active skills forever."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            skills_dir = home / ".agents" / "skills"
            retired_backup = skills_dir / "jgi-lakehouse.bak"
            retired_backup.mkdir(parents=True)
            (retired_backup / "SKILL.md").write_text(
                "---\nname: jgi-lakehouse\ndescription: retired copy\n---\n",
                encoding="utf-8",
            )

            self.run_make(home, "install-skills", "SELECTED_SKILL_DIRS=bio-logic")

            self.assertFalse(retired_backup.exists())
            archived = (
                home / ".agents" / "omics-skills" / "previous-skills"
                / "jgi-lakehouse.bak" / "SKILL.md"
            )
            self.assertTrue(archived.is_file())

    def test_install_removes_links_to_skills_deleted_from_the_pack(self) -> None:
        """A symlinked install updates catalog.json in place, so the previous
        skill list is gone; the deleted names must be retired by name."""
        deleted = (
            "arxiv-search",
            "biorxiv-search",
            "bio-prefect-dask-nextflow",
            "manuscript-review-council",
            "plotly-dashboard-skill",
            "scientific-impact-assessment",
            "scientific-writing",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            skills_dir = home / ".agents" / "skills"
            skills_dir.mkdir(parents=True)
            for name in deleted:
                (skills_dir / name).symlink_to(REPO_ROOT / "skills" / name)

            self.run_make(home, "install-skills", "SELECTED_SKILL_DIRS=bio-logic")

            for name in deleted:
                self.assertFalse(
                    (skills_dir / name).is_symlink(), f"{name} link was not retired"
                )

    def test_install_keeps_skills_that_moved_to_another_repository(self) -> None:
        """pdf-to-md and csag-extraction left this pack but live on in another
        repository, whose installer owns them. Only a link into this checkout
        is retired; a copied directory or a link elsewhere stays."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            skills_dir = home / ".agents" / "skills"
            elsewhere = home / "other-repo" / "skills"
            skills_dir.mkdir(parents=True)
            (elsewhere / "csag-extraction").mkdir(parents=True)
            (skills_dir / "csag-extraction").symlink_to(elsewhere / "csag-extraction")
            copied = skills_dir / "pdf-to-md"
            copied.mkdir()
            (copied / "SKILL.md").write_text(
                "---\nname: pdf-to-md\ndescription: canonical copy\n---\n",
                encoding="utf-8",
            )

            self.run_make(home, "install-skills", "SELECTED_SKILL_DIRS=bio-logic")

            self.assertTrue((skills_dir / "csag-extraction").is_symlink())
            self.assertTrue((copied / "SKILL.md").is_file())

    def test_install_retires_a_link_to_a_moved_skill_in_this_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            skills_dir = home / ".agents" / "skills"
            skills_dir.mkdir(parents=True)
            (skills_dir / "pdf-to-md").symlink_to(REPO_ROOT / "skills" / "pdf-to-md")

            self.run_make(home, "install-skills", "SELECTED_SKILL_DIRS=bio-logic")

            self.assertFalse((skills_dir / "pdf-to-md").is_symlink())

    def write_agent_files(self, home: Path) -> tuple[Path, Path]:
        claude_agents = home / ".claude" / "agents"
        codex_agents = home / ".codex" / "agents"
        claude_agents.mkdir(parents=True)
        codex_agents.mkdir(parents=True)
        return claude_agents, codex_agents

    def install_one_agent(self, home: Path) -> None:
        self.run_make(
            home,
            "install-selected",
            "SELECTED_AGENT_FILES=science-writer.md",
            "SELECTED_SKILL_DIRS=bio-logic",
        )

    def test_install_retires_the_dataviz_artist_agent_this_pack_installed(self) -> None:
        """The link into this checkout goes. Copied files go to the archive only
        when a catalog that this pack copied lists the agent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            claude_agents, codex_agents = self.write_agent_files(home)
            (claude_agents / "dataviz-artist.md").symlink_to(
                REPO_ROOT / "agents" / "dataviz-artist.md"
            )
            (codex_agents / "dataviz-artist.toml").write_text(
                'name = "dataviz-artist"\ndescription = "x"\n'
                'developer_instructions = "x"\n',
                encoding="utf-8",
            )
            catalog_dir = home / ".agents" / "omics-skills"
            catalog_dir.mkdir(parents=True)
            (catalog_dir / "catalog.json").write_text(
                json.dumps({"skills": [], "agents": [{"name": "dataviz-artist"}]})
                + "\n",
                encoding="utf-8",
            )

            self.install_one_agent(home)

            self.assertFalse((claude_agents / "dataviz-artist.md").is_symlink())
            self.assertFalse((codex_agents / "dataviz-artist.toml").exists())
            archived = catalog_dir / "retired-agents"
            self.assertEqual(len(list(archived.glob("dataviz-artist.toml*"))), 1)

    def test_install_leaves_an_independent_dataviz_artist_agent_untouched(self) -> None:
        """Same name, valid definition, no record that this pack installed it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            claude_agents, codex_agents = self.write_agent_files(home)
            own = "---\nname: dataviz-artist\ndescription: my own\n---\nI draw.\n"
            (claude_agents / "dataviz-artist.md").write_text(own, encoding="utf-8")
            (codex_agents / "dataviz-artist.toml").write_text(
                'name = "dataviz-artist"\ndescription = "my own"\n'
                'developer_instructions = "I draw."\n',
                encoding="utf-8",
            )
            foreign = home / "other-repo" / "dataviz-artist.md"
            foreign.parent.mkdir()
            foreign.write_text(own, encoding="utf-8")
            (codex_agents / "dataviz-artist.md").symlink_to(foreign)

            self.install_one_agent(home)

            self.assertEqual(
                (claude_agents / "dataviz-artist.md").read_text(encoding="utf-8"), own
            )
            self.assertTrue((codex_agents / "dataviz-artist.toml").is_file())
            self.assertTrue((codex_agents / "dataviz-artist.md").is_symlink())
            self.assertFalse(
                (home / ".agents" / "omics-skills" / "retired-agents").exists()
            )

    def test_install_ignores_a_symlinked_catalog_for_agent_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            claude_agents, _ = self.write_agent_files(home)
            listed = home / "elsewhere.json"
            listed.write_text(
                json.dumps({"skills": [], "agents": [{"name": "dataviz-artist"}]})
                + "\n",
                encoding="utf-8",
            )
            catalog_dir = home / ".agents" / "omics-skills"
            catalog_dir.mkdir(parents=True)
            (catalog_dir / "catalog.json").symlink_to(listed)
            (claude_agents / "dataviz-artist.md").write_text(
                "---\nname: dataviz-artist\n---\n", encoding="utf-8"
            )

            self.install_one_agent(home)

            self.assertTrue((claude_agents / "dataviz-artist.md").is_file())

    def write_skill_copy(self, path: Path, name: str) -> None:
        path.mkdir(parents=True)
        (path / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: independent copy\n---\n",
            encoding="utf-8",
        )

    def test_install_leaves_an_independent_copy_of_a_retired_name_untouched(
        self,
    ) -> None:
        """A directory with a retired name and a valid frontmatter is not ours
        unless a catalog that this pack copied lists it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            skills_dir = home / ".agents" / "skills"
            catalog_dir = home / ".agents" / "omics-skills"
            catalog_dir.mkdir(parents=True)
            self.write_skill_copy(
                skills_dir / "scientific-writing", "scientific-writing"
            )
            (catalog_dir / "catalog.json").write_text(
                json.dumps({"skills": [{"name": "bio-logic"}]}) + "\n", encoding="utf-8"
            )

            self.run_make(home, "install-skills", "SELECTED_SKILL_DIRS=bio-logic")

            self.assertTrue((skills_dir / "scientific-writing" / "SKILL.md").is_file())
            self.assertFalse((catalog_dir / "retired-skills").exists())

    def test_install_ignores_a_symlinked_catalog_as_ownership_evidence(self) -> None:
        """A catalog that links to another file is rewritten by every update, so
        it records nothing about what this pack installed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            skills_dir = home / ".agents" / "skills"
            catalog_dir = home / ".agents" / "omics-skills"
            catalog_dir.mkdir(parents=True)
            listed = home / "elsewhere.json"
            listed.write_text(
                json.dumps({"skills": [{"name": "scientific-writing"}]}) + "\n",
                encoding="utf-8",
            )
            (catalog_dir / "catalog.json").symlink_to(listed)
            self.write_skill_copy(
                skills_dir / "scientific-writing", "scientific-writing"
            )

            self.run_make(home, "install-skills", "SELECTED_SKILL_DIRS=bio-logic")

            self.assertTrue((skills_dir / "scientific-writing" / "SKILL.md").is_file())

    def test_install_archives_a_copy_that_a_copied_catalog_lists(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            skills_dir = home / ".agents" / "skills"
            catalog_dir = home / ".agents" / "omics-skills"
            catalog_dir.mkdir(parents=True)
            self.write_skill_copy(
                skills_dir / "scientific-writing", "scientific-writing"
            )
            (catalog_dir / "catalog.json").write_text(
                json.dumps({"skills": [{"name": "scientific-writing"}]}) + "\n",
                encoding="utf-8",
            )

            self.run_make(home, "install-skills", "SELECTED_SKILL_DIRS=bio-logic")

            self.assertFalse((skills_dir / "scientific-writing").exists())
            archived = (
                catalog_dir / "retired-skills" / "scientific-writing" / "SKILL.md"
            )
            self.assertTrue(archived.is_file())

    def test_install_leaves_a_foreign_backup_symlink_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            skills_dir = home / ".agents" / "skills"
            skills_dir.mkdir(parents=True)
            foreign = home / "other-repo" / "skills" / "pdf-to-md"
            self.write_skill_copy(foreign, "pdf-to-md")
            (skills_dir / "pdf-to-md.bak").symlink_to(foreign)

            result = self.run_make(
                home, "install-skills", "SELECTED_SKILL_DIRS=bio-logic"
            )

            self.assertTrue((skills_dir / "pdf-to-md.bak").is_symlink())
            self.assertTrue((foreign / "SKILL.md").is_file())
            self.assertIn("left unrecognized legacy backup untouched", result.stdout)

    def test_install_archives_a_backup_symlink_into_this_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            skills_dir = home / ".agents" / "skills"
            skills_dir.mkdir(parents=True)
            (skills_dir / "bio-logic.bak").symlink_to(
                REPO_ROOT / "skills" / "bio-logic"
            )

            self.run_make(home, "install-skills", "SELECTED_SKILL_DIRS=bio-logic")

            self.assertFalse((skills_dir / "bio-logic.bak").is_symlink())
            archived = home / ".agents" / "omics-skills" / "previous-skills"
            self.assertTrue((archived / "bio-logic.bak").is_symlink())

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
                json.dumps(
                    {"skills": [{"name": "bio-logic"}, {"name": "get-api-docs"}]}
                )
                + "\n",
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
