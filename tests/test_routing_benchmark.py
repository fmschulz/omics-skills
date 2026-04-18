"""Thin sanity tests for the routing benchmark plumbing. Does not gate on
pass-rate — the benchmark itself is the regression signal via
`docs/routing_baseline.json` and `python3 scripts/routing_benchmark.py
--compare ...`."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import routing_benchmark  # noqa: E402


class RoutingBenchmarkTests(unittest.TestCase):
    def test_yaml_loads_nonempty(self) -> None:
        rows = routing_benchmark.load_yaml(routing_benchmark.BENCHMARK_PATH)
        self.assertGreater(len(rows), 20)
        self.assertIn("task", rows[0])
        self.assertIn("expected_primary_skills", rows[0])

    def test_evaluate_row_returns_row_result(self) -> None:
        sample = {
            "task": "quality-control Illumina short reads with fastp and trim adapters",
            "platform": "codex",
            "expected_agent": "omics-scientist",
            "expected_primary_skills": ["bio-reads-qc-mapping"],
        }
        result = routing_benchmark.evaluate_row(sample)
        self.assertTrue(result.passed, f"unexpected failures: {result.failures}")
        self.assertEqual(result.actual["agent"], "omics-scientist")
        self.assertIn("bio-reads-qc-mapping", result.actual["primary_skills"])

    def test_baseline_snapshot_exists_and_is_wellformed(self) -> None:
        baseline_path = REPO_ROOT / "docs" / "routing_baseline.json"
        self.assertTrue(
            baseline_path.exists(),
            "Missing docs/routing_baseline.json — run "
            "`python3 scripts/routing_benchmark.py --baseline` to create it.",
        )
        import json

        payload = json.loads(baseline_path.read_text(encoding="utf-8"))
        self.assertIn("summary", payload)
        self.assertIn("pass_rate", payload["summary"])

    def test_fallback_yaml_parser_matches_pyyaml_shape(self) -> None:
        """The fallback parser must handle the exact subset we actually use:
        list of mappings with string scalars and flow-style lists."""
        text = (
            '- task: "assemble reads"\n'
            "  platform: codex\n"
            "  expected_agent: omics-scientist\n"
            "  expected_primary_skills: [bio-assembly-qc, bio-binning-qc]\n"
            "  forbidden_skills: []\n"
            "- task: \"null agent allowed\"\n"
            "  expected_agent: null\n"
            "  expected_primary_skills: [agent-browser]\n"
        )
        parsed = routing_benchmark._parse_minimal_yaml(text)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]["task"], "assemble reads")
        self.assertEqual(
            parsed[0]["expected_primary_skills"],
            ["bio-assembly-qc", "bio-binning-qc"],
        )
        self.assertEqual(parsed[0]["forbidden_skills"], [])
        self.assertIsNone(parsed[1]["expected_agent"])

    def test_aggregate_counts_summary_fields(self) -> None:
        from routing_benchmark import RowResult, aggregate

        results = [
            RowResult(task="a", passed=True, failures=[], actual={}),
            RowResult(
                task="b",
                passed=False,
                failures=["agent: expected 'x', got 'y'"],
                actual={},
            ),
            RowResult(
                task="c",
                passed=False,
                failures=["missing primary skills: ['z']"],
                actual={},
            ),
        ]
        summary = aggregate(results)
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["passed"], 1)
        self.assertEqual(summary["agent_failures"], 1)
        self.assertEqual(summary["primary_skill_failures"], 1)


if __name__ == "__main__":
    unittest.main()
