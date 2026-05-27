#!/usr/bin/env python3
"""Interactive component selector for `make install`.

The Makefile only invokes this script for real terminal sessions. Non-
interactive installs continue to use the all-components path directly.
"""

from __future__ import annotations

import argparse
import curses
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


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


def make_initial_selection(agent_files: list[str], skill_dirs: list[str]) -> InstallSelection:
    return InstallSelection(
        agents={agent: True for agent in agent_files},
        skills={skill: True for skill in skill_dirs},
    )


def selectable_indexes(rows: list[OptionRow]) -> list[int]:
    return [index for index, row in enumerate(rows) if row.kind == "option"]


def toggle_selection(selection: InstallSelection, key: str) -> None:
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
        selection.agents[key] = not selection.agents[key]


def make_install_command(
    make_program: str,
    install_method: str,
    verbose: str,
    selection: InstallSelection,
) -> list[str]:
    return [
        make_program,
        "--no-print-directory",
        "install-selected",
        f"SELECTED_AGENT_FILES={' '.join(selection.selected_agents())}",
        f"SELECTED_SKILL_DIRS={' '.join(selection.selected_skills())}",
        f"INSTALL_METHOD={install_method}",
        f"VERBOSE={verbose}",
    ]


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
) -> None:
    screen.erase()
    height, width = screen.getmaxyx()
    line = 0

    def add(text: str, attr: int = 0) -> None:
        nonlocal line
        if line < height:
            screen.addnstr(line, 0, text, max(0, width - 1), attr)
        line += 1

    add("Omics Skills Installer", curses.A_BOLD)
    add("")
    add("Use Up/Down or j/k to move, Space to toggle, Enter to install, q to cancel.")
    add("The all option starts selected; turn it off to choose components separately.")
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
        attr = curses.A_REVERSE if index == cursor_index else 0
        add(f"{prefix} {marker} {row.label}", attr)

    if end < len(rows):
        add(f"  ... {len(rows) - end} more below")
    if message:
        add(message, curses.A_BOLD)

    screen.refresh()


def choose_components(
    screen: curses.window,
    agent_files: list[str],
    skill_dirs: list[str],
) -> InstallSelection:
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    screen.keypad(True)

    rows = make_rows(agent_files, skill_dirs)
    selection = make_initial_selection(agent_files, skill_dirs)
    indexes = selectable_indexes(rows)
    cursor_pos = 0
    message = ""

    while True:
        cursor_index = indexes[cursor_pos]
        _draw(screen, rows, selection, cursor_index, message)
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
        if key == ord(" "):
            toggle_selection(selection, rows[cursor_index].key)
            continue
        if key in (curses.KEY_ENTER, 10, 13):
            if selection.has_any:
                return selection
            message = "Select at least one component before installing."


def run_selected_install(args: argparse.Namespace, selection: InstallSelection) -> int:
    command = make_install_command(
        args.make_program,
        args.install_method,
        args.verbose,
        selection,
    )
    selected = selection.selected_agents()
    selected.extend(f"skills/{skill}" for skill in selection.selected_skills())
    print("Installing selected components: " + ", ".join(selected))
    completed = subprocess.run(command, cwd=args.repo)
    return completed.returncode


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--make-program", default=os.environ.get("MAKE", "make"))
    parser.add_argument("--install-method", default="symlink")
    parser.add_argument("--verbose", default="0")
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
        selection = curses.wrapper(choose_components, args.agents, skill_dirs)
    except KeyboardInterrupt:
        print("Installation cancelled.")
        return 130

    return run_selected_install(args, selection)


if __name__ == "__main__":
    raise SystemExit(main())
