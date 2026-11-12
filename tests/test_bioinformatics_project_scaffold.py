from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "skills" / "bioinformatics-project"
SCRIPT = SKILL_DIR / "scripts" / "scaffold_project.py"


def tree_digest(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class BioinformaticsProjectScaffoldTests(unittest.TestCase):
    def run_scaffold(self, project: Path, *extra: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(project),
                "--name",
                "Coastal metagenomes",
                "--objective",
                "Recover and compare metagenome-assembled genomes.",
                *extra,
            ],
            text=True,
            capture_output=True,
            check=check,
        )

    def test_scaffold_is_complete_idempotent_and_checkable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "coastal-metagenomes"
            first = self.run_scaffold(project)
            before = tree_digest(project)
            second = self.run_scaffold(project)
            after = tree_digest(project)
            checked = self.run_scaffold(project, "--check")

            self.assertIn("14 created, 0 unchanged", first.stdout)
            self.assertIn("0 created, 14 unchanged", second.stdout)
            self.assertIn("Scaffold valid", checked.stdout)
            self.assertEqual(before, after)
            self.assertTrue((project / "results" / "runall.example").stat().st_mode & 0o111)
            self.assertFalse((project / "tasks" / "lessons.md").exists())
            self.assertIn('[workspace]', (project / "pixi.toml").read_text(encoding="utf-8"))
            project_text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in project.rglob("*")
                if path.is_file()
            )
            self.assertNotIn("arctic", project_text.lower())

    def test_scaffold_refuses_to_overwrite_a_changed_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "coastal-metagenomes"
            self.run_scaffold(project)
            readme = project / "README.md"
            readme.write_text("user-owned content\n", encoding="utf-8")

            result = self.run_scaffold(project, check=False)

            self.assertEqual(result.returncode, 2)
            self.assertIn("README.md", result.stdout)
            self.assertEqual(readme.read_text(encoding="utf-8"), "user-owned content\n")

    def test_check_reports_an_incomplete_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "coastal-metagenomes"
            project.mkdir()

            result = self.run_scaffold(project, "--check", check=False)

            self.assertEqual(result.returncode, 1)
            self.assertIn("Scaffold is incomplete", result.stdout)
            self.assertIn("README.md", result.stdout)

    def test_check_passes_after_a_scaffolded_file_is_edited(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "coastal-metagenomes"
            self.run_scaffold(project)
            hypotheses = project / "tasks" / "hypotheses.md"
            hypotheses.write_text("H1: filled in by the user\n", encoding="utf-8")

            result = self.run_scaffold(project, "--check", check=False)

            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("Scaffold valid", result.stdout)

    def test_check_fails_when_a_scaffolded_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "coastal-metagenomes"
            self.run_scaffold(project)
            (project / "README.md").unlink()

            result = self.run_scaffold(project, "--check", check=False)

            self.assertEqual(result.returncode, 1)
            self.assertIn("README.md", result.stdout)

    def test_check_fails_when_a_directory_replaces_a_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "coastal-metagenomes"
            self.run_scaffold(project)
            (project / "README.md").unlink()
            (project / "README.md").mkdir()

            result = self.run_scaffold(project, "--check", check=False)

            self.assertEqual(result.returncode, 1)
            self.assertIn("README.md", result.stdout)

    def test_numbered_layout_with_first_experiment_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "coastal-metagenomes"
            options = (
                "--layout",
                "numbered",
                "--first-experiment",
                "2026-07-11_read-qc",
            )
            first = self.run_scaffold(project, *options)
            before = tree_digest(project)
            second = self.run_scaffold(project, *options)
            checked = self.run_scaffold(project, *options, "--check")

            experiment = (
                project
                / "02_analyses"
                / "00_read-qc"
                / "00_2026-07-11_read-qc"
            )
            self.assertIn("19 created, 0 unchanged", first.stdout)
            self.assertIn("0 created, 19 unchanged", second.stdout)
            self.assertIn("Scaffold valid", checked.stdout)
            self.assertEqual(before, tree_digest(project))
            self.assertTrue((experiment / "runall").stat().st_mode & 0o111)
            self.assertTrue((project / "00_data" / "00_raw" / ".gitkeep").is_file())
            self.assertTrue((project / "01_shared_preprocessing" / "README.md").is_file())
            self.assertTrue((project / "03_publication_outputs" / "README.md").is_file())
            gitignore = (project / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("!00_data/00_raw/.gitkeep", gitignore)
            self.assertIn("!02_analyses/*/*/runall", gitignore)
            self.assertIn("!tasks/METHODS.md", gitignore)

    def test_canonical_layout_can_add_a_dated_first_experiment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "coastal-metagenomes"
            result = self.run_scaffold(
                project,
                "--first-experiment",
                "2026-07-11_assembly",
            )

            experiment = project / "results" / "2026-07-11_assembly"
            self.assertIn("16 created, 0 unchanged", result.stdout)
            self.assertTrue((experiment / "README.md").is_file())
            self.assertTrue((experiment / "runall").stat().st_mode & 0o111)

    def test_invalid_first_experiment_does_not_create_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "coastal-metagenomes"

            result = self.run_scaffold(
                project,
                "--first-experiment",
                "2026-02-30_bad-date",
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("invalid calendar date", result.stderr)
            self.assertFalse(project.exists())

    def test_first_experiment_conflict_stops_all_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "coastal-metagenomes"
            options = ("--first-experiment", "2026-07-11_assembly")
            self.run_scaffold(project, *options)
            driver = project / "results" / "2026-07-11_assembly" / "runall"
            driver.write_text("user-owned driver\n", encoding="utf-8")
            missing = project / "SUMMARY.md"
            missing.unlink()

            result = self.run_scaffold(project, *options, check=False)

            self.assertEqual(result.returncode, 2)
            self.assertIn("results/2026-07-11_assembly/runall", result.stdout)
            self.assertFalse(missing.exists())
            self.assertEqual(driver.read_text(encoding="utf-8"), "user-owned driver\n")

    def test_directory_at_file_path_is_reported_as_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "coastal-metagenomes"
            (project / "README.md").mkdir(parents=True)

            result = self.run_scaffold(project, check=False)

            self.assertEqual(result.returncode, 2)
            self.assertIn("README.md", result.stdout)
            self.assertFalse((project / "pixi.toml").exists())

    def test_publication_files_are_opt_in_and_use_explicit_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "coastal-metagenomes"
            result = self.run_scaffold(
                project,
                "--license", "MIT",
                "--author", "Coastal Genomics Team",
                "--copyright-year", "2026",
            )
            self.assertIn("16 created, 0 unchanged", result.stdout)
            self.assertIn("Copyright (c) 2026 Coastal Genomics Team", (project / "LICENSE").read_text())
            citation = (project / "CITATION.cff").read_text()
            self.assertIn('name: "Coastal Genomics Team"', citation)
            self.assertIn("license: MIT", citation)

    def test_partial_publication_metadata_is_rejected_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "coastal-metagenomes"
            result = self.run_scaffold(project, "--license", "MIT", check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("must be supplied together", result.stderr)
            self.assertFalse(project.exists())

    def test_sample_sheets_use_sample_id_r1_r2_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            canonical = Path(tmpdir) / "canonical"
            numbered = Path(tmpdir) / "numbered"
            self.run_scaffold(canonical)
            self.run_scaffold(numbered, "--layout", "numbered")

            sheets = [
                canonical / "data" / "samples.tsv",
                numbered / "00_data" / "01_metadata" / "samples.tsv",
                SKILL_DIR / "examples" / "samples.tsv",
            ]
            for sheet in sheets:
                header = sheet.read_text(encoding="utf-8").splitlines()[0].split("\t")
                self.assertEqual(header[:3], ["sample_id", "r1", "r2"], sheet)

    def test_gitignore_tracks_hand_written_files_and_ignores_stage_outputs(
        self,
    ) -> None:
        tracked = [
            "results/lab_notebook.md",
            "results/2026-07-11_assembly/runall",
            "results/2026-07-11_assembly/README.md",
            "results/2026-07-11_assembly/Snakefile",
            "results/2026-07-11_assembly/config.yaml",
            "results/2026-07-11_assembly/main.nf",
            "results/2026-07-11_assembly/reformat_one_off.awk",
        ]
        ignored = [
            "results/2026-07-11_assembly/provenance.txt",
            "results/2026-07-11_assembly/qc/reads.tsv",
            "results/2026-07-11_assembly/assembly/contigs.fasta",
            "results/taxonomy/domain_routing.tsv",
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            shutil.copy(
                SKILL_DIR / "examples" / "gitignore.example", repo / ".gitignore"
            )
            for name in [*tracked, *ignored]:
                path = repo / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("x\n", encoding="utf-8")

            def is_ignored(name: str) -> bool:
                result = subprocess.run(
                    ["git", "-C", str(repo), "check-ignore", "-q", name], check=False
                )
                return result.returncode == 0

            self.assertEqual([n for n in tracked if is_ignored(n)], [])
            self.assertEqual([n for n in ignored if not is_ignored(n)], [])


if __name__ == "__main__":
    unittest.main()
