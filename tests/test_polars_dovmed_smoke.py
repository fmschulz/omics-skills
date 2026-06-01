"""Tests for the polars-dovmed smoke-test helper."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "skills" / "polars-dovmed" / "scripts" / "smoke_test.py"


def load_smoke_module():
    spec = importlib.util.spec_from_file_location("polars_dovmed_smoke_test", MODULE_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PolarsDovmedSmokeTests(unittest.TestCase):
    def test_defaults_keep_artifacts_outside_skill_source(self) -> None:
        module = load_smoke_module()
        args = module.parse_args([])

        self.assertEqual(
            Path(args.run_dir),
            REPO_ROOT / "tasks" / "polars-dovmed-runs" / "smoke-test",
        )
        self.assertNotIn("skills/polars-dovmed/runs", args.run_dir)
        self.assertEqual(args.corpus, "biorxiv")
        self.assertEqual(args.poll_timeout, 75)


if __name__ == "__main__":
    unittest.main()
