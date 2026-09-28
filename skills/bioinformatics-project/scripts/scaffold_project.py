#!/usr/bin/env python3
"""Create or verify a minimal reproducible bioinformatics project scaffold."""

from __future__ import annotations

import argparse
import re
import stat
from datetime import date
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
GITIGNORE_TEMPLATE = SKILL_ROOT / "examples" / "gitignore.example"

MIT_LICENSE = """MIT License

Copyright (c) {year} {author}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def pixi_name(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")
    if not normalized:
        raise ValueError("project name must contain at least one letter or number")
    return normalized


def canonical_scaffold_files(project_name: str, objective: str) -> dict[Path, tuple[str, bool]]:
    pixi_project_name = pixi_name(project_name)
    return {
        Path("README.md"): (
            f"# {project_name}\n\n"
            f"## Objective\n\n{objective}\n\n"
            "## Reproduce\n\n"
            "1. Put immutable inputs under `data/raw/` and record their provenance in `data/README.md`.\n"
            "2. Resolve the environment with `pixi install` and commit `pixi.lock`.\n"
            "3. Fill `tasks/hypotheses.md` before exploratory analysis.\n"
            "4. Add one dated `results/YYYY-MM-DD_topic/runall` driver per experiment.\n",
            False,
        ),
        Path("SUMMARY.md"): (
            "# Project status\n\n"
            "No analysis has run. Record current counts, passed QC gates, and deliverables here.\n",
            False,
        ),
        Path("pixi.toml"): (
            "[workspace]\n"
            'channels = ["conda-forge", "bioconda"]\n'
            f'name = "{pixi_project_name}"\n'
            'platforms = ["linux-64"]\n'
            'version = "0.1.0"\n\n'
            "[tasks]\n\n"
            "[dependencies]\n",
            False,
        ),
        Path(".gitignore"): (GITIGNORE_TEMPLATE.read_text(encoding="utf-8"), False),
        Path("tasks/todo.md"): (
            "# Tasks\n\n- [ ] Define the first verifiable analysis outcome and its proof.\n",
            False,
        ),
        Path("tasks/METHODS.md"): (
            "# Methods\n\nRecord exact commands, versions, parameters, seeds, databases, checksums, and job IDs.\n",
            False,
        ),
        Path("tasks/lessons.md"): ("# Lessons\n\n", False),
        Path("tasks/hypotheses.md"): (
            "# Hypothesis register\n\n"
            "Replace each placeholder before exploratory analysis and keep ruled-out entries visible.\n\n"
            "| ID | Type | Working explanation | Status | Discriminating check |\n"
            "|---|---|---|---|---|\n"
            "| H1 | biological | Define a biological mechanism. | unresolved | Define a test. |\n"
            "| H2 | technical | Define a pipeline or measurement artifact. | unresolved | Define a control. |\n"
            "| H3 | null | Define the no-effect explanation. | unresolved | Define a null comparison. |\n"
            "| H4 | sampling | Define a sampling or batch explanation. | unresolved | Define a stratified check. |\n"
            "| H5 | database | Define a reference/database explanation. | unresolved | Define a database comparison. |\n",
            False,
        ),
        Path("data/README.md"): (
            "# Data provenance\n\n"
            "For each input, record its source, version, retrieval command, checksum, and license.\n",
            False,
        ),
        Path("data/samples.tsv"): ("sample_id\tinput_path\n", False),
        Path("results/lab_notebook.md"): (
            "# Lab notebook\n\n"
            "Add dated entries with the goal, command or driver, QC result, interpretation, and next check.\n",
            False,
        ),
        Path("results/runall.example"): (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n\n"
            'printf "Replace results/runall.example with a dated experiment driver.\\n" >&2\n'
            "exit 1\n",
            True,
        ),
        Path("src/.gitkeep"): ("", False),
        Path("bin/.gitkeep"): ("", False),
        Path("doc/.gitkeep"): ("", False),
    }


def numbered_gitignore() -> str:
    return (
        "# Immutable inputs and generated work\n"
        "00_data/00_raw/*\n"
        "!00_data/00_raw/.gitkeep\n"
        "02_analyses/*/*/*\n"
        "!02_analyses/*/*/README.md\n"
        "!02_analyses/*/*/runall\n"
        "90_logs/*\n"
        "!90_logs/.gitkeep\n"
        "99_scratch/*\n"
        "!99_scratch/.gitkeep\n"
        "*.fastq\n"
        "*.fastq.gz\n"
        "*.fq.gz\n"
        "*.bam\n"
        "*.bai\n"
        "*.cram\n\n"
        "# Environments and caches\n"
        ".pixi/\n"
        ".venv/\n"
        "__pycache__/\n"
        "*.pyc\n"
    )


def numbered_scaffold_files(project_name: str, objective: str) -> dict[Path, tuple[str, bool]]:
    pixi_project_name = pixi_name(project_name)
    return {
        Path("README.md"): (
            f"# {project_name}\n\n"
            f"## Objective\n\n{objective}\n\n"
            "## Reproduce\n\n"
            "1. Put immutable inputs under `00_data/00_raw/` and metadata under `00_data/01_metadata/`.\n"
            "2. Resolve the environment with `pixi install` and commit `pixi.lock`.\n"
            "3. Fill `tasks/hypotheses.md` before exploratory analysis.\n"
            "4. Put shared preprocessing under `01_shared_preprocessing/` and analysis tracks under `02_analyses/`.\n",
            False,
        ),
        Path("SUMMARY.md"): (
            "# Project status\n\n"
            "No analysis has run. Record current counts, passed QC gates, and deliverables here.\n",
            False,
        ),
        Path("pixi.toml"): (
            "[workspace]\n"
            'channels = ["conda-forge", "bioconda"]\n'
            f'name = "{pixi_project_name}"\n'
            'platforms = ["linux-64"]\n'
            'version = "0.1.0"\n\n'
            "[tasks]\n\n"
            "[dependencies]\n",
            False,
        ),
        Path(".gitignore"): (numbered_gitignore(), False),
        Path("tasks/todo.md"): (
            "# Tasks\n\n- [ ] Define the first verifiable analysis outcome and its proof.\n",
            False,
        ),
        Path("tasks/METHODS.md"): (
            "# Methods\n\nRecord exact commands, versions, parameters, seeds, databases, checksums, and job IDs.\n",
            False,
        ),
        Path("tasks/lessons.md"): ("# Lessons\n\n", False),
        Path("tasks/hypotheses.md"): (
            "# Hypothesis register\n\n"
            "Replace each placeholder before exploratory analysis and keep ruled-out entries visible.\n\n"
            "| ID | Type | Working explanation | Status | Discriminating check |\n"
            "|---|---|---|---|---|\n"
            "| H1 | biological | Define a biological mechanism. | unresolved | Define a test. |\n"
            "| H2 | technical | Define a pipeline or measurement artifact. | unresolved | Define a control. |\n"
            "| H3 | null | Define the no-effect explanation. | unresolved | Define a null comparison. |\n"
            "| H4 | sampling | Define a sampling or batch explanation. | unresolved | Define a stratified check. |\n"
            "| H5 | database | Define a reference/database explanation. | unresolved | Define a database comparison. |\n",
            False,
        ),
        Path("00_data/README.md"): (
            "# Data provenance\n\n"
            "For each input, record its source, version, retrieval command, checksum, and license.\n",
            False,
        ),
        Path("00_data/00_raw/.gitkeep"): ("", False),
        Path("00_data/01_metadata/samples.tsv"): ("sample_id\tinput_path\n", False),
        Path("01_shared_preprocessing/README.md"): (
            "# Shared preprocessing\n\nRecord shared manifests, QC, mappings, and catalogs here.\n",
            False,
        ),
        Path("02_analyses/README.md"): (
            "# Analysis tracks\n\nUse numbered, named tracks and restartable drivers.\n",
            False,
        ),
        Path("03_publication_outputs/README.md"): (
            "# Publication outputs\n\nKeep manuscript-ready figures, tables, and reports here.\n",
            False,
        ),
        Path("04_code/00_shared/.gitkeep"): ("", False),
        Path("05_tests/.gitkeep"): ("", False),
        Path("90_logs/.gitkeep"): ("", False),
        Path("99_scratch/.gitkeep"): ("", False),
    }


def parse_experiment(value: str) -> tuple[str, str]:
    match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})_([a-z0-9][a-z0-9-]*)", value)
    if match is None:
        raise ValueError("first experiment must use YYYY-MM-DD_topic with a lowercase topic")
    try:
        date.fromisoformat(match.group(1))
    except ValueError as exc:
        raise ValueError("first experiment contains an invalid calendar date") from exc
    return match.group(1), match.group(2)


def experiment_files(layout: str, value: str) -> dict[Path, tuple[str, bool]]:
    experiment_date, topic = parse_experiment(value)
    if layout == "canonical":
        experiment_root = Path("results") / value
    else:
        experiment_root = Path("02_analyses") / f"00_{topic}" / f"00_{value}"
    return {
        experiment_root / "README.md": (
            f"# {topic.replace('-', ' ').title()}\n\n"
            f"Date: {experiment_date}.\n\n"
            "## Goal\n\nDefine the question and expected output before adapting `runall`.\n\n"
            "## Validation\n\nRecord the QC gate, expected files, and failure criteria.\n",
            False,
        ),
        experiment_root / "runall": (
            (
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n\n"
                "# Under Slurm, submit with --chdir=<experiment dir> or export\n"
                "# EXPERIMENT_DIR: the spooled batch script's own path is not the\n"
                "# experiment directory.\n"
                'if [[ -n "${EXPERIMENT_DIR:-}" ]]; then\n'
                '  cd "$EXPERIMENT_DIR"\n'
                'elif [[ -z "${SLURM_JOB_ID:-}" ]]; then\n'
                '  cd "$(dirname "${BASH_SOURCE[0]}")"\n'
                "fi\n\n"
                'printf "Adapt this experiment driver before running it.\\n" >&2\n'
                "exit 1\n"
            ),
            True,
        ),
    }


def scaffold_files(
    project_name: str,
    objective: str,
    layout: str = "canonical",
    first_experiment: str | None = None,
) -> dict[Path, tuple[str, bool]]:
    if layout == "canonical":
        files = canonical_scaffold_files(project_name, objective)
    elif layout == "numbered":
        files = numbered_scaffold_files(project_name, objective)
    else:
        raise ValueError(f"unsupported layout: {layout}")
    if first_experiment is not None:
        files.update(experiment_files(layout, first_experiment))
    return files


def publication_files(project_name: str, author: str, license_id: str, year: int) -> dict[Path, tuple[str, bool]]:
    if license_id != "MIT":
        raise ValueError("the bundled scaffold currently supports --license MIT only")
    if not author.strip():
        raise ValueError("--author must be non-empty")
    if year < 1900 or year > 9999:
        raise ValueError("--copyright-year must be a four-digit year")
    title = project_name.replace('"', "'")
    citation_author = author.replace('"', "'")
    citation = (
        "cff-version: 1.2.0\n"
        f'title: "{title}"\n'
        'message: "If you use this project, please cite it using this metadata."\n'
        "type: software\n"
        "authors:\n"
        f'  - name: "{citation_author}"\n'
        "license: MIT\n"
    )
    return {
        Path("LICENSE"): (MIT_LICENSE.format(year=year, author=author), False),
        Path("CITATION.cff"): (citation, False),
    }


def conflicts(project_root: Path, files: dict[Path, tuple[str, bool]]) -> list[Path]:
    mismatches: list[Path] = []
    for relative, (content, _) in files.items():
        target = project_root / relative
        if not target.exists():
            continue
        if not target.is_file() or target.read_text(encoding="utf-8") != content:
            mismatches.append(relative)
    return mismatches


def apply_scaffold(project_root: Path, files: dict[Path, tuple[str, bool]]) -> tuple[int, int]:
    created = 0
    unchanged = 0
    for relative, (content, executable) in files.items():
        target = project_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            unchanged += 1
            continue
        target.write_text(content, encoding="utf-8")
        if executable:
            target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        created += 1
    return created, unchanged


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--name", help="Project display name; defaults to the directory name")
    parser.add_argument("--objective", required=True, help="One-sentence project objective")
    parser.add_argument(
        "--layout",
        choices=("canonical", "numbered"),
        default="canonical",
        help="Root directory layout",
    )
    parser.add_argument(
        "--first-experiment",
        metavar="YYYY-MM-DD_TOPIC",
        help="Add one dated experiment README and refusing runall template",
    )
    parser.add_argument("--license", dest="license_id", choices=("MIT",), help="Opt in to LICENSE and CITATION.cff generation")
    parser.add_argument("--author", help="Explicit author or entity name for publication files")
    parser.add_argument("--copyright-year", type=int, help="Explicit copyright year for LICENSE")
    parser.add_argument("--check", action="store_true", help="Verify the scaffold without writing")
    args = parser.parse_args(argv)

    project_root = args.project_dir.expanduser().resolve()
    project_name = args.name or project_root.name
    try:
        files = scaffold_files(
            project_name,
            args.objective.strip(),
            layout=args.layout,
            first_experiment=args.first_experiment,
        )
        publication_values = (args.license_id, args.author, args.copyright_year)
        if any(value is not None for value in publication_values):
            if any(value is None for value in publication_values):
                raise ValueError("--license, --author, and --copyright-year must be supplied together")
            files.update(publication_files(project_name, args.author, args.license_id, args.copyright_year))
    except ValueError as exc:
        parser.error(str(exc))

    mismatches = conflicts(project_root, files) if project_root.exists() else []
    if mismatches:
        print("Scaffold conflicts; no files changed:")
        for path in mismatches:
            print(f"  {path}")
        return 2

    if args.check:
        missing = [relative for relative in files if not (project_root / relative).exists()]
        if missing:
            print("Scaffold is incomplete:")
            for path in missing:
                print(f"  {path}")
            return 1
        print(f"Scaffold valid: {project_root}")
        return 0

    project_root.mkdir(parents=True, exist_ok=True)
    created, unchanged = apply_scaffold(project_root, files)
    print(f"Scaffold ready: {project_root} ({created} created, {unchanged} unchanged)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
