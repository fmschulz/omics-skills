from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "check_release_sync.py"
SPEC = importlib.util.spec_from_file_location("check_release_sync", MODULE_PATH)
check_release_sync = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = check_release_sync
SPEC.loader.exec_module(check_release_sync)

CURRENT_VERSION = json.loads(
    (REPO_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
)["version"]
CURRENT_TAG = f"v{CURRENT_VERSION}"


class ReleaseSyncTests(unittest.TestCase):
    def test_release_candidate_matches_manifest_notes_and_head(self) -> None:
        errors = check_release_sync.release_errors(
            REPO_ROOT,
            CURRENT_TAG,
            "HEAD",
        )
        self.assertEqual(errors, [])

    def test_wrong_tag_is_rejected(self) -> None:
        errors = check_release_sync.release_errors(
            REPO_ROOT,
            "v1.3.0",
            "HEAD",
        )
        self.assertTrue(any("does not match manifest version" in error for error in errors))

    def test_missing_annotated_tag_is_rejected_before_release(self) -> None:
        original = check_release_sync.git_output

        def missing_tag_git_output(repo: Path, *args: str) -> str | None:
            if args in {
                ("cat-file", "-t", CURRENT_TAG),
                ("rev-parse", f"{CURRENT_TAG}^{{commit}}"),
            }:
                return None
            return original(repo, *args)

        with patch.object(
            check_release_sync,
            "git_output",
            side_effect=missing_tag_git_output,
        ):
            errors = check_release_sync.release_errors(
                REPO_ROOT,
                CURRENT_TAG,
                "HEAD",
                require_annotated_tag=True,
            )
        self.assertTrue(any("must be annotated" in error for error in errors))

    def test_unknown_main_ref_is_rejected(self) -> None:
        errors = check_release_sync.release_errors(
            REPO_ROOT,
            CURRENT_TAG,
            "refs/remotes/origin/not-a-real-branch",
        )
        self.assertTrue(any("cannot resolve main ref" in error for error in errors))

    def test_release_commit_must_equal_main(self) -> None:
        original = check_release_sync.git_output

        def mismatched_git_output(repo: Path, *args: str) -> str | None:
            if args == ("rev-parse", "HEAD^{commit}"):
                return "release-sha"
            if args == ("rev-parse", "main^{commit}"):
                return "main-sha"
            return original(repo, *args)

        with patch.object(check_release_sync, "git_output", side_effect=mismatched_git_output):
            errors = check_release_sync.release_errors(
                REPO_ROOT,
                CURRENT_TAG,
                "main",
            )

        self.assertTrue(any("differs from main" in error for error in errors))

    def test_release_workflow_fetches_history_and_runs_sync_check(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("fetch-depth: 0", workflow)
        self.assertIn("scripts/check_release_sync.py", workflow)
        self.assertIn("--require-annotated-tag", workflow)


if __name__ == "__main__":
    unittest.main()
