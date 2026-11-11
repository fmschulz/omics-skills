#!/usr/bin/env python3
"""Verify release metadata and the release commit before publication."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def git_output(repo: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def release_errors(
    repo: Path,
    tag: str,
    main_ref: str,
    require_annotated_tag: bool = False,
) -> list[str]:
    errors: list[str] = []
    codex = json.loads((repo / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    claude = json.loads((repo / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    codex_version = str(codex.get("version", ""))
    claude_version = str(claude.get("version", ""))
    expected_tag = f"v{codex_version}"

    if codex_version != claude_version:
        errors.append(
            f"plugin versions differ: Codex {codex_version!r}, Claude {claude_version!r}"
        )
    if tag != expected_tag:
        errors.append(f"release tag {tag!r} does not match manifest version {expected_tag!r}")

    notes = repo / ".github" / "releases" / f"{tag}.md"
    if not notes.is_file():
        errors.append(f"release notes are missing: {notes.relative_to(repo)}")
    elif not notes.read_text(encoding="utf-8").startswith(
        f"# omics-skills {codex_version}\n"
    ):
        errors.append(f"release notes heading does not match version {codex_version}")

    main_sha = git_output(repo, "rev-parse", f"{main_ref}^{{commit}}")
    if main_sha is None:
        errors.append(f"cannot resolve main ref: {main_ref}")

    tag_type = git_output(repo, "cat-file", "-t", tag)
    if require_annotated_tag and tag_type != "tag":
        errors.append(f"release tag must be annotated and present locally: {tag}")
    tag_sha = git_output(repo, "rev-parse", f"{tag}^{{commit}}")
    release_sha = tag_sha or git_output(repo, "rev-parse", "HEAD^{commit}")
    if release_sha is None:
        errors.append("cannot resolve the release commit")
    elif main_sha is not None and release_sha != main_sha:
        errors.append(
            f"release commit {release_sha} differs from {main_ref} commit {main_sha}"
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--tag", required=True)
    parser.add_argument("--main-ref", default="origin/main")
    parser.add_argument("--require-annotated-tag", action="store_true")
    args = parser.parse_args(argv)

    repo = args.repo.expanduser().resolve()
    errors = release_errors(
        repo,
        args.tag,
        args.main_ref,
        require_annotated_tag=args.require_annotated_tag,
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Release synchronized: {args.tag} -> {args.main_ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
