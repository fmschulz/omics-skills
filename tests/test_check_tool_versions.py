"""Tests for the tool-version maintenance report (no network)."""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_tool_versions", ROOT / "scripts" / "check_tool_versions.py"
)
assert SPEC is not None
assert SPEC.loader is not None
check_tool_versions = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_tool_versions  # dataclasses resolve the module by name
SPEC.loader.exec_module(check_tool_versions)

GUIDE = """# Tool

**Last verified:** 2026-10-01
**Tool version/release checked:** SPAdes v4.2.0 (GitHub release, 2025-05-06)
**Official docs/manual:** https://ablab.github.io/spades/
**Release/source:** https://github.com/ablab/spades/releases/tag/v4.2.0 and
"""


def test_parse_guide_reads_checked_version_and_repository() -> None:
    """Both provenance lines are read and the GitHub repository is extracted."""
    guide = check_tool_versions.parse_guide(Path("x.md"), GUIDE)
    assert guide is not None
    assert guide.checked.startswith("SPAdes v4.2.0")
    assert guide.repos == ("ablab/spades",)


def test_parse_guide_skips_pages_without_provenance() -> None:
    """A page without the provenance lines is not a tool guide."""
    assert check_tool_versions.parse_guide(Path("x.md"), "# Notes\n") is None


def test_is_current_compares_without_the_v_prefix() -> None:
    """A tag counts as current when the checked text already names it."""
    checked = "SPAdes v4.2.0 (GitHub release)"
    assert check_tool_versions.is_current(checked, "v4.2.0")
    assert not check_tool_versions.is_current(checked, "v4.3.0")
    assert not check_tool_versions.is_current(checked, "unknown")
    assert check_tool_versions.is_current("QUAST v5.3.0", "quast_5.3.0")
    assert not check_tool_versions.is_current("Tool v1.2.0-rc.1", "v1.2.0")
    assert check_tool_versions.is_current("Tool v1.2.0-rc.1", "v1.2.0-rc.1")
    assert check_tool_versions.is_current("MMseqs2 18-8cc5c", "18-8cc5c")
    assert not check_tool_versions.is_current("MMseqs2 18-8cc5c", "18-8ffff")
    assert check_tool_versions.is_current("InterProScan 5.78-109.0; v6", "5.78-109.0")
    assert not check_tool_versions.is_current("Tool v14.2.0", "v4.2.0")
    assert not check_tool_versions.is_current("Tool 1.2.0.rc1", "v1.2.0")
    assert not check_tool_versions.is_current("Tool 1.2.0.dev1", "1.2.0")
    assert not check_tool_versions.is_current("Tool 1.2.0+cu12", "1.2.0")
    assert check_tool_versions.is_current("Checked with v4.2.0.", "v4.2.0")


def test_report_rows_cover_every_guide_with_a_github_source() -> None:
    """The repository's own guides parse, and at least one names GitHub."""
    guides = check_tool_versions.guides_in(ROOT)
    assert guides
    assert all(guide.repos for guide in guides)
