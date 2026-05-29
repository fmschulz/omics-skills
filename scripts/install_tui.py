#!/usr/bin/env python3
"""Interactive component selector for `make install` / `make uninstall`.

The Makefile only invokes this script for real terminal sessions. Non-
interactive runs continue to use the all-components paths directly. Press `t`
to switch between install and uninstall; rows are annotated `(installed)` so you
can see what is currently set up before choosing what to remove.
"""

from __future__ import annotations

import argparse
import curses
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# Reuse the single source of truth for skill-reference parsing instead of
# maintaining a second copy of the regex and section extractor.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import skill_index  # noqa: E402


DEFAULT_AGENT_FILES = [
    "omics-scientist.md",
    "literature-expert.md",
    "science-writer.md",
    "dataviz-artist.md",
]

AGENT_LABELS = {
    "omics-scientist.md": "Omics scientist agent",
    "literature-expert.md": "Literature expert agent",
    "science-writer.md": "Science writer agent",
    "dataviz-artist.md": "Dataviz artist agent",
}

# Where installed components live (standard paths; no private meta-repo).
HOME = Path.home()
CLAUDE_AGENTS_DIR = HOME / ".claude" / "agents"
CODEX_AGENTS_DIR = HOME / ".codex" / "agents"
AGENTS_SKILLS_DIR = HOME / ".agents" / "skills"


def agent_installed(agent: str) -> bool:
    for directory in (CLAUDE_AGENTS_DIR, CODEX_AGENTS_DIR):
        target = directory / agent
        if target.exists() or target.is_symlink():
            return True
    return False


def skill_installed(skill: str) -> bool:
    target = AGENTS_SKILLS_DIR / skill
    return target.exists() or target.is_symlink()


@dataclass
class InstallSelection:
    agents: dict[str, bool]
    skills: dict[str, bool]

    @property
    def all_selected(self) -> bool:
        return all(self.agents.values()) and all(self.skills.values())

    @property
    def has_any(self) -> bool:
        return any(self.agents.values()) or any(self.skills.values())

    def selected_agents(self) -> list[str]:
        return [agent for agent, selected in self.agents.items() if selected]

    def selected_skills(self) -> list[str]:
        return [skill for skill, selected in self.skills.items() if selected]


@dataclass(frozen=True)
class OptionRow:
    key: str
    label: str
    kind: str = "option"


def make_rows(agent_files: list[str], skill_dirs: list[str]) -> list[OptionRow]:
    rows = [
        OptionRow("all", "All agents and skills"),
        OptionRow("agents-header", "Agents", "header"),
    ]
    rows.extend(
        OptionRow(agent, f"{AGENT_LABELS.get(agent, agent)} ({agent})")
        for agent in agent_files
    )
    rows.append(OptionRow("skills-header", "Skills", "header"))
    rows.extend(OptionRow(f"skill:{skill}", skill) for skill in skill_dirs)
    return rows


def make_initial_selection(
    agent_files: list[str], skill_dirs: list[str], mode: str = "install"
) -> InstallSelection:
    # Install: everything pre-selected. Uninstall: only what is installed.
    pick_agent = (lambda a: True) if mode == "install" else agent_installed
    pick_skill = (lambda s: True) if mode == "install" else skill_installed
    return InstallSelection(
        agents={agent: pick_agent(agent) for agent in agent_files},
        skills={skill: pick_skill(skill) for skill in skill_dirs},
    )


def row_installed(key: str) -> bool:
    if key == "all" or key.endswith("-header"):
        return False
    if key.startswith("skill:"):
        return skill_installed(key.removeprefix("skill:"))
    return agent_installed(key)


def selectable_indexes(rows: list[OptionRow]) -> list[int]:
    return [index for index, row in enumerate(rows) if row.kind == "option"]


def load_agent_skill_map(
    repo: Path,
    agent_files: list[str],
    skill_dirs: list[str],
) -> dict[str, set[str]]:
    skill_set = set(skill_dirs)
    mapping = {agent: set() for agent in agent_files}

    catalog_path = repo / "catalog" / "catalog.json"
    if catalog_path.exists():
        try:
            with catalog_path.open(encoding="utf-8") as handle:
                catalog = json.load(handle)
            for agent in catalog.get("agents", []):
                agent_file = Path(agent.get("path", "")).name
                if agent_file not in mapping:
                    continue
                for section_skills in agent.get("skill_sections", {}).values():
                    mapping[agent_file].update(skill for skill in section_skills if skill in skill_set)
        except (OSError, json.JSONDecodeError):
            pass

    for agent_file, skills in mapping.items():
        if skills:
            continue
        agent_path = repo / "agents" / agent_file
        if not agent_path.exists():
            continue
        try:
            text = agent_path.read_text(encoding="utf-8")
        except OSError:
            continue
        body = skill_index.extract_section(text, "Mandatory Skill Usage")
        skills.update(skill for skill in skill_index.SKILL_REF_PATTERN.findall(body) if skill in skill_set)

    return mapping


def toggle_selection(
    selection: InstallSelection,
    key: str,
    agent_skill_map: dict[str, set[str]] | None = None,
) -> None:
    if key == "all":
        new_state = not selection.all_selected
        for agent in selection.agents:
            selection.agents[agent] = new_state
        for skill in selection.skills:
            selection.skills[skill] = new_state
        return

    if key.startswith("skill:"):
        skill = key.removeprefix("skill:")
        if skill in selection.skills:
            selection.skills[skill] = not selection.skills[skill]
        return

    if key in selection.agents:
        new_state = not selection.agents[key]
        selection.agents[key] = new_state
        if not agent_skill_map:
            return
        agent_skills = agent_skill_map.get(key, set())
        if new_state:
            for skill in agent_skills:
                if skill in selection.skills:
                    selection.skills[skill] = True
            return
        still_selected_skills: set[str] = set()
        for agent, selected in selection.agents.items():
            if selected:
                still_selected_skills.update(agent_skill_map.get(agent, set()))
        for skill in agent_skills - still_selected_skills:
            if skill in selection.skills:
                selection.skills[skill] = False


def make_command(
    make_program: str,
    mode: str,
    install_method: str,
    verbose: str,
    selection: InstallSelection,
) -> list[str]:
    target = "install-selected" if mode == "install" else "uninstall-selected"
    command = [
        make_program,
        "--no-print-directory",
        target,
        f"SELECTED_AGENT_FILES={' '.join(selection.selected_agents())}",
        f"SELECTED_SKILL_DIRS={' '.join(selection.selected_skills())}",
        f"VERBOSE={verbose}",
    ]
    if mode == "install":
        command.append(f"INSTALL_METHOD={install_method}")
    return command


def _row_checked(selection: InstallSelection, key: str) -> bool:
    if key == "all":
        return selection.all_selected
    if key.startswith("skill:"):
        return selection.skills.get(key.removeprefix("skill:"), False)
    return selection.agents.get(key, False)


def _draw(
    screen: curses.window,
    rows: list[OptionRow],
    selection: InstallSelection,
    cursor_index: int,
    message: str,
    mode: str,
) -> None:
    screen.erase()
    height, width = screen.getmaxyx()
    line = 0

    def add(text: str, attr: int = 0) -> None:
        nonlocal line
        if line < height:
            screen.addnstr(line, 0, text, max(0, width - 1), attr)
        line += 1

    verb = "install" if mode == "install" else "uninstall"
    add(f"Omics Skills Installer — {mode.upper()}", curses.A_BOLD)
    add("")
    add(f"Up/Down or j/k move · Space toggle · t switch install/uninstall "
        f"· Enter {verb} · q cancel")
    add("Rows marked (installed) are currently present.")
    add("")

    max_rows = max(1, height - line - 3)
    if len(rows) <= max_rows:
        start = 0
    else:
        start = min(max(0, cursor_index - max_rows + 1), len(rows) - max_rows)
    end = min(len(rows), start + max_rows)

    if start > 0:
        add(f"  ... {start} more above")

    for index, row in enumerate(rows[start:end], start=start):
        if row.kind == "header":
            add(f"  {row.label}", curses.A_BOLD)
            continue
        marker = "[x]" if _row_checked(selection, row.key) else "[ ]"
        prefix = ">" if index == cursor_index else " "
        suffix = "  (installed)" if row_installed(row.key) else ""
        attr = curses.A_REVERSE if index == cursor_index else 0
        add(f"{prefix} {marker} {row.label}{suffix}", attr)

    if end < len(rows):
        add(f"  ... {len(rows) - end} more below")
    if message:
        add(message, curses.A_BOLD)

    screen.refresh()


def choose_components(
    screen: curses.window,
    agent_files: list[str],
    skill_dirs: list[str],
    agent_skill_map: dict[str, set[str]] | None = None,
    mode: str = "install",
) -> tuple[str, InstallSelection]:
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    screen.keypad(True)

    rows = make_rows(agent_files, skill_dirs)
    selection = make_initial_selection(agent_files, skill_dirs, mode)
    indexes = selectable_indexes(rows)
    cursor_pos = 0
    message = ""

    while True:
        cursor_index = indexes[cursor_pos]
        _draw(screen, rows, selection, cursor_index, message, mode)
        message = ""
        key = screen.getch()

        if key in (ord("q"), ord("Q"), 27):
            raise KeyboardInterrupt
        if key in (curses.KEY_UP, ord("k"), ord("K")):
            cursor_pos = (cursor_pos - 1) % len(indexes)
            continue
        if key in (curses.KEY_DOWN, ord("j"), ord("J")):
            cursor_pos = (cursor_pos + 1) % len(indexes)
            continue
        if key in (ord("t"), ord("T")):
            mode = "uninstall" if mode == "install" else "install"
            selection = make_initial_selection(agent_files, skill_dirs, mode)
            continue
        if key == ord(" "):
            # Skill cascade only makes sense when installing.
            cascade = agent_skill_map if mode == "install" else None
            toggle_selection(selection, rows[cursor_index].key, cascade)
            continue
        if key in (curses.KEY_ENTER, 10, 13):
            if selection.has_any:
                return mode, selection
            message = f"Select at least one component to {mode}."


def run_selected(args: argparse.Namespace, mode: str, selection: InstallSelection) -> int:
    command = make_command(
        args.make_program,
        mode,
        args.install_method,
        args.verbose,
        selection,
    )
    selected = selection.selected_agents()
    selected.extend(f"skills/{skill}" for skill in selection.selected_skills())
    verb = "Installing" if mode == "install" else "Uninstalling"
    print(f"{verb} selected components: " + ", ".join(selected))
    completed = subprocess.run(command, cwd=args.repo)
    return completed.returncode


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--make-program", default=os.environ.get("MAKE", "make"))
    parser.add_argument("--install-method", default="symlink")
    parser.add_argument("--verbose", default="0")
    parser.add_argument("--mode", choices=["install", "uninstall"], default="install")
    parser.add_argument("--agents", nargs="+", default=DEFAULT_AGENT_FILES)
    parser.add_argument("--skills", nargs="+")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("Interactive installer requires a terminal.", file=sys.stderr)
        return 2

    try:
        skill_dirs = args.skills
        if skill_dirs is None:
            skills_root = args.repo / "skills"
            skill_dirs = sorted(path.name for path in skills_root.iterdir() if path.is_dir())
        agent_skill_map = load_agent_skill_map(args.repo, args.agents, skill_dirs)
        mode, selection = curses.wrapper(
            choose_components, args.agents, skill_dirs, agent_skill_map, args.mode
        )
    except KeyboardInterrupt:
        print("Cancelled.")
        return 130

    return run_selected(args, mode, selection)


if __name__ == "__main__":
    raise SystemExit(main())
