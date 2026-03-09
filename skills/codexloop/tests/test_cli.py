from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from codexloop.cli import collect_planner_context, default_config


REPO_ROOT = Path(__file__).resolve().parents[3]
PYTHONPATH_ROOT = REPO_ROOT / "skills"


def git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=True,
    )


def write_fake_codex(bin_dir: Path) -> Path:
    script_path = bin_dir / "codex"
    script_path.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import json
            import os
            import sys
            from pathlib import Path

            args = sys.argv[1:]
            if "--help" in args:
                sys.exit(0)

            output_last_message = None
            output_schema = None
            model = None
            session_id = None
            mode = "task"
            empty_output = os.environ.get("CODEXLOOP_FAKE_EMPTY_OUTPUT") == "1"

            i = 0
            while i < len(args):
                arg = args[i]
                if arg == "exec":
                    i += 1
                    continue
                if arg == "resume":
                    mode = "resume"
                    session_id = args[i + 1]
                    i += 2
                    continue
                if arg in {"-o", "--output-last-message"}:
                    output_last_message = Path(args[i + 1])
                    i += 2
                    continue
                if arg == "--output-schema":
                    output_schema = Path(args[i + 1])
                    i += 2
                    continue
                if arg == "-m":
                    model = args[i + 1]
                    i += 2
                    continue
                i += 1

            prompt = sys.stdin.read()
            cwd = Path.cwd()

            if output_last_message is None:
                raise SystemExit("missing --output-last-message")

            if output_schema is not None:
                print(json.dumps({"type": "thread.started", "thread_id": "planner-thread"}))
                if empty_output:
                    print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1, "cached_input_tokens": 0, "output_tokens": 1}}))
                    sys.exit(0)
                payload = {
                    "tasks": [
                        {
                            "id": "001",
                            "slug": "create-markers",
                            "title": "Create marker files",
                            "summary": "Create the marker files needed for verification.",
                            "dependencies": [],
                            "files_to_edit": ["done.txt", "ok.txt"],
                            "acceptance_criteria": ["done.txt exists", "ok.txt exists"],
                            "verification": ["test -f done.txt", "test -f ok.txt"],
                            "implementation_notes": ["Create the files in the repository root."]
                        }
                    ]
                }
                output_last_message.parent.mkdir(parents=True, exist_ok=True)
                output_last_message.write_text(json.dumps(payload), encoding="utf-8")
                print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1, "cached_input_tokens": 0, "output_tokens": 1}}))
                sys.exit(0)

            actual_session = session_id or f"thread-{cwd.name}"
            print(json.dumps({"type": "thread.started", "thread_id": actual_session}))
            (cwd / "done.txt").write_text("done\\n", encoding="utf-8")
            if mode == "resume":
                (cwd / "ok.txt").write_text("ok\\n", encoding="utf-8")
            output_last_message.parent.mkdir(parents=True, exist_ok=True)
            output_last_message.write_text(
                json.dumps({"mode": mode, "model": model, "cwd": str(cwd), "prompt": prompt[:80]}),
                encoding="utf-8",
            )
            print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1, "cached_input_tokens": 0, "output_tokens": 1}}))
            sys.exit(0)
            """
        ),
        encoding="utf-8",
    )
    script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC)
    return script_path


class CodexLoopCLITest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)
        self.repo = self.root / "target"
        self.repo.mkdir()
        git(["init", "-b", "main"], cwd=self.repo)
        git(["config", "user.email", "codexloop@example.com"], cwd=self.repo)
        git(["config", "user.name", "CodexLoop Test"], cwd=self.repo)
        (self.repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
        git(["add", "README.md"], cwd=self.repo)
        git(["commit", "-m", "init"], cwd=self.repo)

        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        write_fake_codex(self.bin_dir)

        self.env = os.environ.copy()
        self.env["PATH"] = f"{self.bin_dir}:{self.env['PATH']}"
        self.env["PYTHONPATH"] = str(PYTHONPATH_ROOT)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def run_cli(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", "-m", "codexloop", *args],
            cwd=str(REPO_ROOT),
            env=self.env,
            text=True,
            capture_output=True,
            check=check,
        )

    def configure_repo(self, *, max_attempts_per_task: int) -> None:
        config_path = self.repo / ".codexloop" / "config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["codex_bin"] = str(self.bin_dir / "codex")
        config["doctor_command"] = "test -f ok.txt"
        config["max_attempts_per_task"] = max_attempts_per_task
        config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    def test_init_plan_run_resume_flow(self) -> None:
        self.run_cli("init", str(self.repo))
        self.configure_repo(max_attempts_per_task=1)

        self.assertTrue((self.repo / "docs" / "plans" / "implementation-plan.md").exists())
        self.assertTrue((self.repo / "docs" / "plans" / "CODEXLOOP_AGENT.md").exists())
        self.assertTrue((self.repo / "MEMORY.md").exists())

        plan = self.run_cli("plan", "--repo", str(self.repo))
        self.assertIn("Wrote 1 tasks", plan.stdout)

        run = self.run_cli("run", "--repo", str(self.repo), "--run-id", "testrun", check=False)
        self.assertEqual(run.returncode, 2)
        self.assertIn("001 needs_resume", run.stdout)
        self.assertTrue((self.repo / "docs" / "plans" / "active" / "testrun.md").exists())

        status = self.run_cli("status", "--repo", str(self.repo), "--run-id", "testrun")
        self.assertIn("001 needs_resume", status.stdout)

        resumed = self.run_cli("resume", "--repo", str(self.repo), "--run-id", "testrun")
        self.assertIn("001 merged", resumed.stdout)

        integration_worktree = self.repo / ".codexloop" / "worktrees" / "testrun" / "integration"
        self.assertTrue((integration_worktree / "done.txt").exists())
        self.assertTrue((integration_worktree / "ok.txt").exists())
        self.assertTrue((self.repo / "docs" / "plans" / "completed" / "testrun.md").exists())

        run_state = json.loads(
            (self.repo / ".codexloop" / "runs" / "testrun" / "run.json").read_text(encoding="utf-8")
        )
        self.assertEqual(run_state["tasks"]["001"]["status"], "merged")
        self.assertTrue(run_state["tasks"]["001"]["session_id"])
        memory_text = (self.repo / "MEMORY.md").read_text(encoding="utf-8")
        self.assertIn("What failed", memory_text)
        self.assertIn("How it was solved", memory_text)

    def test_run_auto_retries_until_verification_passes(self) -> None:
        self.run_cli("init", str(self.repo))
        self.configure_repo(max_attempts_per_task=2)

        self.run_cli("plan", "--repo", str(self.repo))
        run = self.run_cli("run", "--repo", str(self.repo), "--run-id", "autorun")
        self.assertIn("001 merged", run.stdout)

        completed_plan = self.repo / "docs" / "plans" / "completed" / "autorun.md"
        self.assertTrue(completed_plan.exists())
        completed_text = completed_plan.read_text(encoding="utf-8")
        self.assertIn("attempt 1/2 started", completed_text)
        self.assertIn("verification failed", completed_text)
        self.assertIn("merged into", completed_text)

    def test_collect_planner_context_prefers_curated_inputs(self) -> None:
        self.run_cli("init", str(self.repo))
        (self.repo / "configs").mkdir(exist_ok=True)
        (self.repo / "scripts").mkdir(exist_ok=True)
        (self.repo / "docs" / "results").mkdir(parents=True, exist_ok=True)
        (self.repo / "configs" / "autoplan.json").write_text('{"campaign":"demo"}\n', encoding="utf-8")
        (self.repo / "scripts" / "doctor.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        (self.repo / "docs" / "results" / "README.md").write_text("# Results\n", encoding="utf-8")

        config = default_config(self.repo)
        plan_path = self.repo / "docs" / "plans" / "implementation-plan.md"
        context = collect_planner_context(self.repo, config, plan_path)

        self.assertIn("Top-Level Entries", context)
        self.assertIn("scripts/doctor.sh", context)
        self.assertIn("Plan Input Path", context)
        self.assertNotIn(".git/", context)

    def test_plan_falls_back_when_planner_returns_no_output_file(self) -> None:
        self.run_cli("init", str(self.repo))
        self.configure_repo(max_attempts_per_task=1)
        plan_path = self.repo / "docs" / "plans" / "implementation-plan.md"
        plan_path.write_text(
            textwrap.dedent(
                """\
                # Implementation Plan

                ## Objective

                Ship a small repo change.

                ### P0: Prepare verification

                Goal:
                - Create a minimal verification path.

                Acceptance:
                - `scripts/doctor.sh` exists
                """
            ),
            encoding="utf-8",
        )
        env = self.env.copy()
        env["CODEXLOOP_FAKE_EMPTY_OUTPUT"] = "1"
        result = subprocess.run(
            ["python3", "-m", "codexloop", "plan", "--repo", str(self.repo)],
            cwd=str(REPO_ROOT),
            env=env,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("planner fallback", result.stdout)
        backlog = json.loads((self.repo / ".codexloop" / "tasks" / "backlog.json").read_text(encoding="utf-8"))
        self.assertEqual(len(backlog["tasks"]), 1)


if __name__ == "__main__":
    unittest.main()
