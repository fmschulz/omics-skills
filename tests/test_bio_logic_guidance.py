from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "skills" / "bio-logic" / "SKILL.md"


class BioLogicGuidanceTests(unittest.TestCase):
    def test_study_profiles_separate_computational_and_intervention_evidence(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("### Study-Type Profiles", text)
        self.assertIn("Computational or machine learning", text)
        self.assertIn("Evolutionary or comparative genomics", text)
        self.assertNotIn("Causal claims only from experimental designs", text)

    def test_grade_language_is_bounded(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("Do not assign a GRADE level to a single phylogeny", text)


if __name__ == "__main__":
    unittest.main()
