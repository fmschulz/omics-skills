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
        f"---\nname: {fm_name}\ndescription: Test behavior. Use when testing a skill.\n---\n# {name}\n\n{body}",
        encoding="utf-8",
    )
    return skill_dir


class ValidateSkillTests(unittest.TestCase):
    def test_valid_skill_has_no_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _write_skill(Path(tmp), "good-skill")
            self.assertEqual(validate_skills.validate_skill(skill_dir), [])

    def test_empty_required_section_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _write_skill(Path(tmp), "hollow-skill")
            md = skill_dir / "SKILL.md"
            md.write_text(
                md.read_text(encoding="utf-8").replace("## Output\n\ncontent\n", "## Output\n"),
                encoding="utf-8",
            )
            errors = validate_skills.validate_skill(skill_dir)
            self.assertTrue(any("empty section ## Output" in error for error in errors))

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

    def test_description_requires_use_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _write_skill(Path(tmp), "vague-skill")
            md = skill_dir / "SKILL.md"
            md.write_text(
                md.read_text().replace(
                    "Test behavior. Use when testing a skill.",
                    "Test behavior.",
                ),
                encoding="utf-8",
            )
            errors = validate_skills.validate_skill(skill_dir)
            self.assertTrue(any("must say when" in error for error in errors))

    def test_broken_local_markdown_link_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _write_skill(Path(tmp), "linked-skill")
            md = skill_dir / "SKILL.md"
            md.write_text(
                md.read_text() + "\n[Missing guide](docs/missing.md)\n",
                encoding="utf-8",
            )
            errors = validate_skills.validate_skill(skill_dir)
            self.assertTrue(any("broken local Markdown link" in error for error in errors))

    def test_broken_link_in_supplementary_markdown_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _write_skill(Path(tmp), "linked-skill")
            docs = skill_dir / "docs"
            docs.mkdir()
            (docs / "guide.md").write_text(
                "[Missing](missing-reference.md)\n",
                encoding="utf-8",
            )
            errors = validate_skills.validate_skill(skill_dir)
            self.assertTrue(any("docs/guide.md" in error for error in errors))

    def test_folded_yaml_description_cannot_bypass_length_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _write_skill(Path(tmp), "folded-skill")
            skill_md = skill_dir / "SKILL.md"
            text = skill_md.read_text(encoding="utf-8")
            long_description = "Use when testing. " + ("long description " * 30)
            text = text.replace(
                "description: Test behavior. Use when testing a skill.",
                "description: >-\n  " + long_description,
            )
            skill_md.write_text(text, encoding="utf-8")
            errors = validate_skills.validate_skill(skill_dir)
            self.assertTrue(any("description over" in error for error in errors))

    def test_documented_command_requires_existing_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _write_skill(Path(tmp), "command-skill")
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                skill_md.read_text(encoding="utf-8")
                + "\n```bash\nuv run --script scripts/missing.py\n```\n",
                encoding="utf-8",
            )
            errors = validate_skills.validate_skill(skill_dir)
            self.assertTrue(any("command script is missing" in error for error in errors))

    def test_documented_command_must_load_pep723_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _write_skill(Path(tmp), "command-skill")
            scripts = skill_dir / "scripts"
            scripts.mkdir()
            (scripts / "driver.py").write_text(
                "# /// script\n"
                "# dependencies = [\n"
                '#   "jsonschema==4.26.0",\n'
                "# ]\n"
                "# ///\n",
                encoding="utf-8",
            )
            skill_md = skill_dir / "SKILL.md"
            skill_md.write_text(
                skill_md.read_text(encoding="utf-8")
                + "\n```bash\nuv run --no-project python scripts/driver.py\n```\n",
                encoding="utf-8",
            )
            errors = validate_skills.validate_skill(skill_dir)
            self.assertTrue(any("bypasses PEP 723" in error for error in errors))

    def test_output_contract_requires_script_literal_or_annotation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = _write_skill(Path(tmp), "output-skill")
            (skill_dir / "scripts").mkdir()
            (skill_dir / "scripts" / "driver.py").write_text(
                'OUTPUT = "real.tsv"\n',
                encoding="utf-8",
            )
            skill_md = skill_dir / "SKILL.md"
            text = skill_md.read_text(encoding="utf-8").replace(
                "## Output\n\ncontent",
                "## Output\n\n- `real.tsv`\n- `phantom.json`",
            )
            skill_md.write_text(text, encoding="utf-8")
            errors = validate_skills.validate_skill(skill_dir)
            self.assertTrue(any("phantom.json" in error for error in errors))
            self.assertFalse(any("real.tsv" in error for error in errors))

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

    def test_required_taxonomy_documents_cannot_disappear_silently(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "skills" / "tracking-taxonomy-updates").mkdir(parents=True)
            errors = validate_supplementary_docs.validate_all(root)
            self.assertTrue(any("reference/sources.md" in error for error in errors))
            self.assertTrue(any("reference/tools.md" in error for error in errors))

    def test_banned_conda_command_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "skills" / "demo-skill" / "docs"
            docs.mkdir(parents=True)
            (docs / "install.md").write_text(
                "conda install -c bioconda demo\n",
                encoding="utf-8",
            )
            errors = validate_supplementary_docs.validate_all(root)
            self.assertTrue(any("banned conda/mamba" in error for error in errors))

    def test_pinned_pixi_gate_requires_manifest_and_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "skills" / "demo-skill"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "# Demo\n\n## Quality Gates\n\n- [ ] The existing `pixi.lock` is current.\n",
                encoding="utf-8",
            )
            errors = validate_supplementary_docs.validate_all(root)
            self.assertTrue(any("pixi.toml and pixi.lock" in error for error in errors))
            (skill / "pixi.toml").write_text("[workspace]\nname='demo'\n", encoding="utf-8")
            (skill / "pixi.lock").write_text("version: 6\n", encoding="utf-8")
            self.assertEqual(validate_supplementary_docs.validate_all(root), [])

    def test_real_repo_supplementary_docs_pass(self) -> None:
        errors = validate_supplementary_docs.validate_all(REPO_ROOT)
        self.assertEqual(errors, [], f"shipped supplementary docs failed validation: {errors}")


if __name__ == "__main__":
    unittest.main()
