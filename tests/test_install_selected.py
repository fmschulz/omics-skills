from __future__ import annotations

import os
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT = "literature-expert"


def is_hidden_stage(skill_md: Path) -> bool:
    """Tell whether the SKILL.md frontmatter sets ``disable-model-invocation: true``."""
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        return False
    for line in lines[1:]:
        if line == "---":
            return False
        if line.replace(" ", "") == "disable-model-invocation:true":
            return True
    return False


def installed_names(directory: Path) -> list[str]:
    """Return the sorted entry names of ``directory``."""
    return sorted(path.name for path in directory.iterdir())


class InstallSelectedIntegrationTests(unittest.TestCase):
    def run_make(
        self, home: Path, *args: str, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["NO_COLOR"] = "1"
        return subprocess.run(
            ["make", "--no-print-directory", *args],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=check,
        )

    def stage_skill_names(self) -> list[str]:
        return sorted(
            path.parent.name
            for path in (REPO_ROOT / "skills").glob("*/SKILL.md")
            if is_hidden_stage(path)
        )

    def assert_selected_install_holds_only_selected_components(
        self, install_method: str
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            self.run_make(
                home,
                "install-selected",
                f"INSTALL_METHOD={install_method}",
                f"SELECTED_AGENT_FILES={AGENT}.md",
                "SELECTED_SKILL_DIRS=bio-logic polars-dovmed",
            )

            skills_dir = home / ".agents" / "skills"
            self.assertEqual(
                installed_names(skills_dir), ["bio-logic", "polars-dovmed"]
            )
            for name in ("bio-logic", "polars-dovmed"):
                installed = skills_dir / name
                source = REPO_ROOT / "skills" / name
                if install_method == "symlink":
                    self.assertEqual(installed.resolve(), source)
                else:
                    self.assertFalse(installed.is_symlink(), name)
                    self.assertEqual(
                        (installed / "SKILL.md").read_text(encoding="utf-8"),
                        (source / "SKILL.md").read_text(encoding="utf-8"),
                    )

            claude_agents = home / ".claude" / "agents"
            codex_agents = home / ".codex" / "agents"
            self.assertEqual(installed_names(claude_agents), [f"{AGENT}.md"])
            self.assertEqual(installed_names(codex_agents), [f"{AGENT}.toml"])
            claude_agent = claude_agents / f"{AGENT}.md"
            source_agent = REPO_ROOT / "agents" / f"{AGENT}.md"
            if install_method == "symlink":
                self.assertEqual(claude_agent.resolve(), source_agent)
            else:
                self.assertFalse(claude_agent.is_symlink())
                self.assertEqual(
                    claude_agent.read_text(encoding="utf-8"),
                    source_agent.read_text(encoding="utf-8"),
                )
            parsed_agent = tomllib.loads(
                (codex_agents / f"{AGENT}.toml").read_text(encoding="utf-8")
            )
            self.assertEqual(parsed_agent["name"], AGENT)
            self.assertIn("developer_instructions", parsed_agent)

            state_dir = home / ".agents" / "omics-skills"
            for stale in ("skill_index.py", "catalog.json", "README.md"):
                self.assertFalse(os.path.lexists(state_dir / stale), stale)

    def test_selected_symlink_install_holds_only_selected_components(self) -> None:
        self.assert_selected_install_holds_only_selected_components("symlink")

    def test_selected_copy_install_holds_only_selected_components(self) -> None:
        self.assert_selected_install_holds_only_selected_components("copy")

    def test_selected_skills_only_install_installs_no_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            result = self.run_make(
                home,
                "install-selected",
                "INSTALL_METHOD=symlink",
                "SELECTED_AGENT_FILES=",
                "SELECTED_SKILL_DIRS=beautiful-data-viz",
            )

            self.assertEqual(
                installed_names(home / ".agents" / "skills"), ["beautiful-data-viz"]
            )
            self.assertIn("Skipping agents", result.stdout)
            self.assertFalse((home / ".claude" / "agents").exists())
            self.assertFalse((home / ".codex" / "agents").exists())

    def test_install_without_a_skill_selection_installs_the_selected_agent_only(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            result = self.run_make(
                home,
                "install-selected",
                f"SELECTED_AGENT_FILES={AGENT}.md",
                "SELECTED_SKILL_DIRS=",
            )

            self.assertIn("Skipping shared skills", result.stdout)
            self.assertFalse((home / ".agents" / "skills").exists())
            self.assertEqual(
                installed_names(home / ".claude" / "agents"), [f"{AGENT}.md"]
            )

    def test_uninstall_removes_skill_links_agents_and_the_state_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            self.run_make(
                home,
                "install-selected",
                "INSTALL_METHOD=symlink",
                f"SELECTED_AGENT_FILES={AGENT}.md",
                "SELECTED_SKILL_DIRS=beautiful-data-viz",
            )
            archive = home / ".agents" / "omics-skills" / "previous-skills"
            archive.mkdir(parents=True)
            self.assertTrue((home / ".claude" / "skills").is_symlink())
            self.assertTrue((home / ".codex" / "skills").is_symlink())

            self.run_make(home, "uninstall")

            self.assertFalse((home / ".claude" / "skills").is_symlink())
            self.assertFalse((home / ".codex" / "skills").is_symlink())
            self.assertFalse((home / ".claude" / "agents" / f"{AGENT}.md").exists())
            self.assertFalse((home / ".codex" / "agents" / f"{AGENT}.toml").exists())
            self.assertEqual(installed_names(home / ".agents" / "skills"), [])
            self.assertFalse((home / ".agents" / "omics-skills").exists())

    def test_install_matches_the_machine_setup_script_call(self) -> None:
        """The machine setup script installs a skill subset with client links off
        and the Claude agents in ~/.agents/agents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            agents_dir = home / ".agents" / "agents"

            self.run_make(
                home,
                "install",
                "LINK_CLIENT_SKILLS=no",
                f"CLAUDE_AGENTS_DIR={agents_dir}",
                "SELECTED_SKILL_DIRS=bio-logic polars-dovmed",
            )

            skills_dir = home / ".agents" / "skills"
            self.assertEqual(
                installed_names(skills_dir), ["bio-logic", "polars-dovmed"]
            )
            for name in ("bio-logic", "polars-dovmed"):
                self.assertEqual(
                    (skills_dir / name).resolve(), REPO_ROOT / "skills" / name
                )
            shipped = sorted(path.name for path in (REPO_ROOT / "agents").glob("*.md"))
            self.assertEqual(installed_names(agents_dir), shipped)
            for name in shipped:
                self.assertEqual(
                    (agents_dir / name).resolve(), REPO_ROOT / "agents" / name
                )
            self.assertFalse(os.path.lexists(home / ".claude" / "skills"))
            self.assertFalse(os.path.lexists(home / ".codex" / "skills"))

    def test_install_removes_the_router_files_an_older_version_installed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            state_dir = home / ".agents" / "omics-skills"
            state_dir.mkdir(parents=True)
            (state_dir / "skill_index.py").symlink_to(
                REPO_ROOT / "scripts" / "skill_index.py"
            )
            (state_dir / "catalog.json").write_text("{}\n", encoding="utf-8")
            (state_dir / "README.md").symlink_to(REPO_ROOT / "catalog" / "README.md")
            archive = state_dir / "previous-skills"
            archive.mkdir()

            self.run_make(home, "install-skills", "SELECTED_SKILL_DIRS=bio-logic")

            for stale in ("skill_index.py", "catalog.json", "README.md"):
                self.assertFalse(os.path.lexists(state_dir / stale), stale)
            self.assertTrue(archive.is_dir())

    def test_selecting_a_stage_installs_the_pipeline_group_and_says_so(self) -> None:
        stages = self.stage_skill_names()
        self.assertIn("bio-annotation", stages)
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            result = self.run_make(
                home,
                "install-selected",
                f"SELECTED_AGENT_FILES={AGENT}.md",
                "SELECTED_SKILL_DIRS=bio-logic bio-annotation",
            )

            added = [line for line in result.stderr.splitlines() if "expanded" in line]
            self.assertEqual(len(added), 1, result.stderr)
            named = added[0].split("added ", 1)[1].split(" (", 1)[0].split()
            self.assertEqual(
                sorted(named),
                sorted({"omics-pipeline", *stages} - {"bio-annotation"}),
            )
            skills_dir = home / ".agents" / "skills"
            self.assertEqual(
                installed_names(skills_dir),
                sorted([*stages, "bio-logic", "omics-pipeline"]),
            )
            self.assertTrue((skills_dir / "omics-pipeline" / "SKILL.md").is_file())

    def test_selecting_omics_pipeline_installs_every_stage_it_names(self) -> None:
        stages = self.stage_skill_names()
        self.assertTrue(stages)
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

    def test_a_runtime_install_with_a_pipeline_selection_adds_the_stage_group(
        self,
    ) -> None:
        """Another tool installs through install-claude with a selection. The
        pipeline group must be complete there too, not only in install-selected."""
        stages = self.stage_skill_names()
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)

            result = self.run_make(
                home,
                "install-claude",
                "LINK_CLIENT_SKILLS=no",
                f"CLAUDE_AGENTS_DIR={home / '.agents' / 'agents'}",
                "SELECTED_SKILL_DIRS=omics-pipeline",
            )

            self.assertEqual(
                installed_names(home / ".agents" / "skills"),
                sorted([*stages, "omics-pipeline"]),
            )
            self.assertIn("Selection expanded", result.stderr)

    def test_a_leftover_directory_without_a_skill_file_is_not_a_skill(self) -> None:
        """Ignored files such as __pycache__ keep the directory of a deleted
        skill alive in an updated checkout. It must not be installed, and it
        must not stop the retirement of the old link."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            pack_skills = home / "pack" / "skills"
            (pack_skills / "bio-logic").mkdir(parents=True)
            (pack_skills / "bio-logic" / "SKILL.md").write_text(
                "---\nname: bio-logic\ndescription: kept\n---\n", encoding="utf-8"
            )
            leftover = pack_skills / "preprint-search" / "scripts" / "__pycache__"
            leftover.mkdir(parents=True)
            (leftover / "search.cpython-312.pyc").write_bytes(b"")
            skills_dir = home / ".agents" / "skills"
            skills_dir.mkdir(parents=True)
            (skills_dir / "preprint-search").symlink_to(pack_skills / "preprint-search")

            result = self.run_make(
                home,
                "install-skills",
                f"SKILLS_DIR={pack_skills}",
                "SELECTED_SKILL_DIRS=bio-logic preprint-search",
            )
            status = self.run_make(home, "status", f"SKILLS_DIR={pack_skills}")

            self.assertEqual(installed_names(skills_dir), ["bio-logic"])
            self.assertIn("skipped preprint-search", result.stdout)
            self.assertIn("1/1", status.stdout)

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
            result = self.run_make(
                Path(tmpdir),
                "install-skills",
                "SELECTED_SKILL_DIRS=not-a-real-skill",
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not-a-real-skill not found", result.stdout)

    def test_install_removes_a_retired_symlink_into_this_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            skills_dir = home / ".agents" / "skills"
            skills_dir.mkdir(parents=True)
            retired = skills_dir / "get-api-docs"
            retired.symlink_to(REPO_ROOT / "skills" / "get-api-docs")

            self.run_make(home, "install-skills", "SELECTED_SKILL_DIRS=bio-logic")

            self.assertFalse(retired.exists())
            self.assertFalse(retired.is_symlink())
            self.assertTrue((skills_dir / "bio-logic").exists())

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

            self.run_make(home, "install-skills", "SELECTED_SKILL_DIRS=bio-logic")

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
        deleted = (
            "arxiv-search",
            "biorxiv-search",
            "bio-assembly-qc",
            "bio-binning-qc",
            "bio-fasta-database-curator",
            "bio-foundation-housekeeping",
            "bio-gene-calling",
            "bio-phylogenomics",
            "bio-prefect-dask-nextflow",
            "bio-protein-clustering-pangenome",
            "bio-reads-qc-mapping",
            "bio-stats-ml-reporting",
            "bio-structure-annotation",
            "bio-workflow-methods-docwriter",
            "exploratory-data-analysis",
            "preprint-search",
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
        """A moved skill left this pack but lives on in another repository,
        whose installer owns it. Only a link into this checkout is retired; a
        copied directory or a link elsewhere stays, and a link elsewhere is
        the expected state, so it draws no warning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            skills_dir = home / ".agents" / "skills"
            elsewhere = home / "other-repo" / "skills"
            skills_dir.mkdir(parents=True)
            linked = ("csag-extraction", "proposal-review", "ai-scientist-evaluator")
            for name in linked:
                (elsewhere / name).mkdir(parents=True)
                (skills_dir / name).symlink_to(elsewhere / name)
            copied = skills_dir / "pdf-to-md"
            copied.mkdir()
            (copied / "SKILL.md").write_text(
                "---\nname: pdf-to-md\ndescription: canonical copy\n---\n",
                encoding="utf-8",
            )

            result = self.run_make(
                home, "install-skills", "SELECTED_SKILL_DIRS=bio-logic"
            )

            for name in linked:
                self.assertTrue((skills_dir / name).is_symlink(), name)
            self.assertTrue((copied / "SKILL.md").is_file())
            self.assertNotIn("WARNING", result.stdout)

    def test_install_retires_a_link_to_a_moved_skill_in_this_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            skills_dir = home / ".agents" / "skills"
            skills_dir.mkdir(parents=True)
            (skills_dir / "pdf-to-md").symlink_to(REPO_ROOT / "skills" / "pdf-to-md")

            self.run_make(home, "install-skills", "SELECTED_SKILL_DIRS=bio-logic")

            self.assertFalse((skills_dir / "pdf-to-md").is_symlink())

    def write_agent_dirs(self, home: Path) -> tuple[Path, Path]:
        claude_agents = home / ".claude" / "agents"
        codex_agents = home / ".codex" / "agents"
        claude_agents.mkdir(parents=True)
        codex_agents.mkdir(parents=True)
        return claude_agents, codex_agents

    def install_one_agent(self, home: Path) -> None:
        self.run_make(
            home,
            "install-selected",
            f"SELECTED_AGENT_FILES={AGENT}.md",
            "SELECTED_SKILL_DIRS=bio-logic",
        )

    def test_install_retires_the_dataviz_artist_link_but_keeps_rendered_files(
        self,
    ) -> None:
        """The link into this checkout goes. A rendered Codex file cannot be tied
        to this pack, so it stays."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            claude_agents, codex_agents = self.write_agent_dirs(home)
            (claude_agents / "dataviz-artist.md").symlink_to(
                REPO_ROOT / "agents" / "dataviz-artist.md"
            )
            rendered = codex_agents / "dataviz-artist.toml"
            rendered.write_text(
                'name = "dataviz-artist"\ndescription = "x"\n'
                'developer_instructions = "x"\n',
                encoding="utf-8",
            )

            self.install_one_agent(home)

            self.assertFalse(os.path.lexists(claude_agents / "dataviz-artist.md"))
            self.assertTrue(rendered.is_file())
            self.assertFalse(
                (home / ".agents" / "omics-skills" / "retired-agents").exists()
            )

    def test_install_retires_the_links_of_the_agents_removed_in_2_0(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            claude_agents, _ = self.write_agent_dirs(home)
            retired = ("omics-scientist", "science-writer")
            for name in retired:
                (claude_agents / f"{name}.md").symlink_to(
                    REPO_ROOT / "agents" / f"{name}.md"
                )

            self.install_one_agent(home)

            for name in retired:
                self.assertFalse(os.path.lexists(claude_agents / f"{name}.md"), name)
            self.assertTrue((claude_agents / f"{AGENT}.md").is_symlink())

    def test_install_leaves_an_independent_dataviz_artist_agent_untouched(self) -> None:
        """Same name, valid definition, no link into this checkout."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            claude_agents, codex_agents = self.write_agent_dirs(home)
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

    def write_skill_copy(self, path: Path, name: str) -> None:
        path.mkdir(parents=True)
        (path / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: independent copy\n---\n",
            encoding="utf-8",
        )

    def test_install_leaves_a_copied_skill_with_a_retired_name_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            skills_dir = home / ".agents" / "skills"
            self.write_skill_copy(
                skills_dir / "scientific-writing", "scientific-writing"
            )

            self.run_make(home, "install-skills", "SELECTED_SKILL_DIRS=bio-logic")

            self.assertTrue((skills_dir / "scientific-writing" / "SKILL.md").is_file())
            self.assertFalse(
                (home / ".agents" / "omics-skills" / "retired-skills").exists()
            )

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
            skills_dir = home / ".agents" / "skills"
            foreign_dir = home / "foreign" / "skills"
            skills_dir.mkdir(parents=True)
            foreign_dir.mkdir(parents=True)
            retired = skills_dir / "get-api-docs"
            retired.symlink_to(foreign_dir / "get-api-docs")

            result = self.run_make(
                home,
                "install-skills",
                "SELECTED_SKILL_DIRS=bio-logic",
            )

            self.assertTrue(retired.is_symlink())
            self.assertIn("left unexpected symlink untouched", result.stdout)


if __name__ == "__main__":
    unittest.main()
