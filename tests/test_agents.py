"""The agent files, the installer's agent list and the skills they name agree."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROW = re.compile(r"^\|\s*`([a-z0-9-]+)`\s*\|")


def skills_table_names(agent_text: str) -> list[str]:
    """Return the skill names in the first column of an agent's ``## Skills`` table."""
    section = agent_text.partition("\n## Skills\n")[2].partition("\n## ")[0]
    return [
        match.group(1)
        for line in section.splitlines()
        if (match := SKILL_ROW.match(line))
    ]


def missing_skills(repo_root: Path) -> list[str]:
    """List ``agent: skill`` for every table row that names no shipped skill."""
    shipped = {path.parent.name for path in repo_root.glob("skills/*/SKILL.md")}
    return [
        f"{agent.stem}: {name}"
        for agent in sorted(repo_root.glob("agents/*.md"))
        for name in skills_table_names(agent.read_text(encoding="utf-8"))
        if name not in shipped
    ]


def test_every_agent_lists_only_shipped_skills() -> None:
    agents = sorted(REPO_ROOT.glob("agents/*.md"))
    assert agents, "the pack ships at least one agent"
    for agent in agents:
        assert skills_table_names(agent.read_text(encoding="utf-8")), agent.name
    assert missing_skills(REPO_ROOT) == []


def test_a_row_for_a_removed_skill_is_reported(tmp_path: Path) -> None:
    (tmp_path / "skills" / "kept").mkdir(parents=True)
    (tmp_path / "skills" / "kept" / "SKILL.md").write_text("---\nname: kept\n---\n")
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "helper.md").write_text(
        "---\nname: helper\n---\n\n## Skills\n\n"
        "| Skill | Use for |\n| --- | --- |\n| `kept` | a |\n| `removed` | b |\n\n"
        "## Communication\n\n| `not-a-skill-row` | outside the table |\n"
    )

    assert missing_skills(tmp_path) == ["helper: removed"]


def test_the_installer_lists_exactly_the_shipped_agents() -> None:
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    match = re.search(r"^AGENT_FILES := (.+)$", makefile, flags=re.MULTILINE)
    assert match, "the Makefile defines AGENT_FILES"
    shipped = sorted(path.name for path in REPO_ROOT.glob("agents/*.md"))

    assert sorted(match.group(1).split()) == shipped
