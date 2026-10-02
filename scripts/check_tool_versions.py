#!/usr/bin/env python3
"""Report tool guides whose checked version may be behind the newest GitHub release.

Each tool guide records a ``Tool version/release checked:`` line and a
``Release/source:`` line. For every GitHub repository named on the source line,
the report asks the GitHub API for the newest release, or the newest tag when
the repository publishes no releases, and prints it beside the checked text.
A row reads ``check`` when the newest version string does not appear in the
checked text. This is a maintenance report: it always exits 0 after printing.

Usage:
    python3 scripts/check_tool_versions.py [--repo PATH]
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKED_RE = re.compile(
    r"^(?:\*\*)?Tool version/release checked(?:\*\*)?:(?:\*\*)?\s*(.+)$", re.MULTILINE
)
SOURCE_RE = re.compile(
    r"^(?:\*\*)?Release/source(?:\*\*)?:(?:\*\*)?\s*(.+)$", re.MULTILINE
)
GITHUB_RE = re.compile(r"github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?(?=[/)\s#?>]|$)")
API_ROOT = "https://api.github.com/"
# The version inside a tag: everything from the first digit, so v4.2.0 gives 4.2.0.
TAG_VERSION_RE = re.compile(r"\d.*$")

log = logging.getLogger("check_tool_versions")


@dataclass(frozen=True)
class Guide:
    """The version provenance recorded at the top of one tool guide."""

    path: Path
    checked: str
    repos: tuple[str, ...]


def parse_guide(path: Path, text: str) -> Guide | None:
    """Read the checked version and GitHub repositories from a guide.

    Args:
        path: Location of the guide, kept for the report.
        text: Full Markdown text of the guide.

    Returns:
        The parsed guide, or None when either provenance line is missing.
    """
    checked = CHECKED_RE.search(text)
    source = SOURCE_RE.search(text)
    if not checked or not source:
        return None
    repos = dict.fromkeys(
        f"{owner}/{name}" for owner, name in GITHUB_RE.findall(source.group(1))
    )
    return Guide(path, checked.group(1).strip(), tuple(repos))


def github_get(endpoint: str) -> object | None:
    """Return the decoded JSON for a GitHub API endpoint, or None on any failure.

    Uses the authenticated ``gh`` CLI when it is installed, and an anonymous
    request otherwise. No contact address is sent.
    """
    if shutil.which("gh"):
        result = subprocess.run(
            ["gh", "api", endpoint], capture_output=True, text=True, check=False
        )
        return json.loads(result.stdout) if result.returncode == 0 else None
    request = urllib.request.Request(
        API_ROOT + endpoint,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "omics-skills"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as error:
        log.warning("GitHub request for %s failed: %s", endpoint, error)
        return None


def newest_version(repo: str) -> str:
    """Return the newest release tag of a repository, else its newest tag."""
    release = github_get(f"repos/{repo}/releases/latest")
    if isinstance(release, dict) and release.get("tag_name"):
        return str(release["tag_name"])
    tags = github_get(f"repos/{repo}/tags?per_page=1")
    if isinstance(tags, list) and tags:
        log.warning("%s has no releases; GitHub does not sort tags by version", repo)
        return str(tags[0]["name"])
    return "unknown"


def is_current(checked: str, tag: str) -> bool:
    """Tell whether the checked text already names the newest version.

    The whole version in the tag must appear in the checked text as one token,
    so ``v4.2.0`` and ``quast_5.3.0`` match text that says ``4.2.0`` or
    ``5.3.0``. A checked release candidate ``1.2.0-rc.1`` is not the stable
    ``1.2.0`` (also ``1.2.0.rc1`` or ``1.2.0+local``), and build hashes such as
    ``18-8cc5c`` must match in full.
    """
    version = TAG_VERSION_RE.search(tag)
    if not version:
        return False
    token = re.escape(version.group(0))
    return bool(re.search(rf"(?<![\w.-])v?{token}(?![\w+-]|\.\w)", checked))


def guides_in(repo_root: Path) -> list[Guide]:
    """Parse every Markdown file under ``skills/`` that carries both lines."""
    paths = sorted((repo_root / "skills").rglob("*.md"))
    parsed = (parse_guide(path, path.read_text(encoding="utf-8")) for path in paths)
    return [guide for guide in parsed if guide and guide.repos]


def main(argv: list[str] | None = None) -> int:
    """Print one tab-separated row per guide and GitHub repository."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, default=ROOT, help="Repository root.")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    print("status\tguide\tchecked\trepository\tnewest")
    for guide in guides_in(args.repo):
        for repo in guide.repos:
            tag = newest_version(repo)
            status = "ok" if is_current(guide.checked, tag) else "check"
            path = guide.path.relative_to(args.repo)
            print(f"{status}\t{path}\t{guide.checked}\t{repo}\t{tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
