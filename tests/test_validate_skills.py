"""Tests for scripts/validate-skills.py. The script name has a hyphen, so it is
loaded by file path rather than imported by module name."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
MODULE_PATH = REPO_ROOT / "scripts" / "validate-skills.py"
SPEC = importlib.util.spec_from_file_location("validate_skills", MODULE_PATH)
validate_skills = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = validate_skills
SPEC.loader.exec_module(validate_skills)

SUPP_MODULE_PATH = REPO_ROOT / "scripts" / "validate-supplementary-docs.py"
SUPP_SPEC = importlib.util.spec_from_file_location("validate_supplementary_docs", SUPP_MODULE_PATH)
validate_supplementary_docs = importlib.util.module_from_spec(SUPP_SPEC)
assert SUPP_SPEC.loader is not None
sys.modules[SUPP_SPEC.name] = validate_supplementary_docs
SUPP_SPEC.loader.exec_module(validate_supplementary_docs)


def _write_skill(root: Path, name: str, *, frontmatter_name: str | None = None, sections: bool = True) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True)
    fm_name = name if frontmatter_name is None else frontmatter_name
    body = "\n".join(f"{s}\n\ncontent\n" for s in validate_skills.REQUIRED_SECTIONS) if sections else "# Title\n"
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {fm_name}\ndescription: test skill\n---\n# {name}\n\n{body}",
        encoding="utf-8",
    )
    return skill_dir


class ValidateSkillTests(unittest.TestCase):
    def test_valid_skill_has_no_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _write_skill(Path(tmp), "good-skill")
            self.assertEqual(validate_skills.validate_skill(skill_dir), [])

    def test_missing_skill_md_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "no-skill-md"
            empty.mkdir()
            errors = validate_skills.validate_skill(empty)
            self.assertEqual(len(errors), 1)
            self.assertIn("missing SKILL.md", errors[0])

    def test_name_mismatch_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _write_skill(Path(tmp), "dir-name", frontmatter_name="other-name")
            errors = validate_skills.validate_skill(skill_dir)
            self.assertTrue(any("name mismatch" in e for e in errors))

    def test_missing_sections_are_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _write_skill(Path(tmp), "thin-skill", sections=False)
            errors = validate_skills.validate_skill(skill_dir)
            self.assertTrue(any("missing sections" in e for e in errors))

    def test_oversized_skill_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _write_skill(Path(tmp), "big-skill")
            md = skill_dir / "SKILL.md"
            md.write_text(md.read_text() + "\n".join(["filler"] * (validate_skills.MAX_LINES + 5)), encoding="utf-8")
            errors = validate_skills.validate_skill(skill_dir)
            self.assertTrue(any("over" in e and "lines" in e for e in errors))

    def test_validate_all_aggregates_across_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_skill(root, "good-skill")
            _write_skill(root, "bad-skill", frontmatter_name="WRONG")
            errors = validate_skills.validate_all(root)
            self.assertTrue(any("bad-skill" in e for e in errors))
            self.assertFalse(any("good-skill" in e for e in errors))

    def test_real_repo_skills_pass(self) -> None:
        """The shipped skills/ tree must validate cleanly."""
        errors = validate_skills.validate_all(REPO_ROOT / "skills")
        self.assertEqual(errors, [], f"shipped skills failed validation: {errors}")


class ValidateSupplementaryDocsTests(unittest.TestCase):
    def test_tool_doc_requires_evidence_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc_dir = root / "skills" / "demo-skill" / "docs"
            doc_dir.mkdir(parents=True)
            doc = doc_dir / "tool.md"
            doc.write_text("# Tool\n\nOfficial Documentation: https://example.org\n", encoding="utf-8")

            errors = validate_supplementary_docs.validate_all(root)
            self.assertTrue(any("Last verified" in e for e in errors))
            self.assertTrue(any("Tool version/release checked" in e for e in errors))

    def test_valid_tool_doc_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc_dir = root / "skills" / "demo-skill" / "docs"
            doc_dir.mkdir(parents=True)
            doc = doc_dir / "tool.md"
            doc.write_text(
                textwrap.dedent(
                    """\
                    # Tool

                    **Last verified:** 2026-05-30
                    **Tool version/release checked:** v1.2.3
                    **Official docs/manual:** https://example.org/docs
                    **Release/source:** https://example.org/releases/v1.2.3

                    ## Installation
                    ```bash
                    tool --version
                    ```
                    """
                ),
                encoding="utf-8",
            )

            self.assertEqual(validate_supplementary_docs.validate_all(root), [])

    def test_fasta_curator_root_tools_doc_is_in_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skills" / "bio-fasta-database-curator"
            skill_dir.mkdir(parents=True)
            (skill_dir / "tools.md").write_text(
                "# Tools\n\nOfficial docs: https://example.org\nVersion: v1\n",
                encoding="utf-8",
            )

            errors = validate_supplementary_docs.validate_all(root)
            self.assertTrue(any("bio-fasta-database-curator/tools.md" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
