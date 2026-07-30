from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "ai-scientist-evaluator"
SCRIPT = SKILL_ROOT / "scripts" / "aggregate_reviews.py"
PROFILES = SKILL_ROOT / "assets" / "default_weight_profiles.yaml"


def scientific_review() -> dict:
    categories = (
        "task_completion",
        "data_provenance",
        "methodological_rigor",
        "computational_correctness",
        "biological_interpretation",
        "validation_robustness",
        "reproducibility",
        "novelty_insight",
        "communication",
    )
    weights = (15, 10, 15, 10, 15, 10, 15, 5, 5)
    return {
        "task": {
            "name": "Notebook audit",
            "summary": "Audit one generated analysis notebook.",
            "primary_question": "Does the notebook support its conclusion?",
            "deliverables": ["notebook"],
        },
        "submission_id": "submission-a",
        "profile": "scientific-analysis",
        "gate_checks": [],
        "scores": [
            {
                "category": category,
                "weight": weight + 1,
                "score_0_to_5": 3,
                "weighted_points": 999,
                "justification": "Fixture score.",
            }
            for category, weight in zip(categories, weights, strict=True)
        ],
        "overall": {
            "total_score_100": 99,
            "recommendation": "Major revision",
            "confidence": "medium",
            "summary": "Fixture review.",
            "major_strengths": [],
            "major_weaknesses": [],
            "required_revisions": [],
        },
    }


class AIScientistEvaluatorTests(unittest.TestCase):
    def run_aggregator(self, *reviews: dict) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for index, review in enumerate(reviews):
                path = Path(tmp) / f"review-{index}.json"
                path.write_text(json.dumps(review), encoding="utf-8")
                paths.append(path)
            return subprocess.run(
                ["uv", "run", "--script", str(SCRIPT), *map(str, paths)],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

    def test_aggregator_recomputes_profile_weights_and_total(self) -> None:
        result = self.run_aggregator(scientific_review())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("| 60.0 |", result.stdout)

    def test_aggregator_rejects_schema_invalid_review(self) -> None:
        review = scientific_review()
        del review["task"]
        result = self.run_aggregator(review)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("failed evaluation_schema.json", result.stderr)

    def test_aggregator_preserves_downward_penalty_adjustment(self) -> None:
        review = scientific_review()
        review["overall"]["total_score_100"] = 50
        result = self.run_aggregator(review)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("| 50.0 |", result.stdout)

    def test_integrity_flags_win_before_task_completion_tiebreak(self) -> None:
        clean = scientific_review()
        clean["submission_id"] = "clean"
        dirty = scientific_review()
        dirty["submission_id"] = "fabricated"
        for item in dirty["scores"]:
            if item["category"] == "task_completion":
                item["score_0_to_5"] = 4
            elif item["category"] == "data_provenance":
                item["score_0_to_5"] = 1.5
        dirty["red_flags"] = [
            {
                "flag": "fabricated accession",
                "severity": "critical",
                "notes": "The accession does not exist.",
            }
        ]

        result = self.run_aggregator(dirty, clean)
        self.assertEqual(result.returncode, 0, result.stderr)
        first_data_row = next(
            line
            for line in result.stdout.splitlines()
            if line.startswith("| 1 |")
        )
        self.assertIn("| clean |", first_data_row)

    def test_weight_profiles_are_present_for_regression_context(self) -> None:
        self.assertTrue(PROFILES.is_file())


if __name__ == "__main__":
    unittest.main()
