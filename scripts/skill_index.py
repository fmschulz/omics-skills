#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SKILL_REF_PATTERN = re.compile(r"(?<![\w:/])/([a-z0-9][a-z0-9-]+)")
QUOTED_PATTERN = re.compile(r'"([^"]+)"')
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

# How many hops of `depend_on` edges to follow out from each primary skill when
# building the "supporting skills" list. depend_on is the reverse of the
# workflow_next chain, so an unbounded walk drags an entire pipeline into every
# single-step query. 1 = direct prerequisites only.
DEPENDENCY_MAX_DEPTH = 1

# Routing score weights (see docs/SKILL_GRAPH.md). Lifted to named constants so
# the scoring model lives in one place and can be tuned against the benchmark.
SKILL_DESCRIPTION_WEIGHT = 2.0       # query overlap with a skill's name/description
TASK_PATTERN_DIRECT_BONUS = 4.0      # query contains a skill's task-pattern phrase verbatim
TASK_PATTERN_OVERLAP_WEIGHT = 3.0    # partial token overlap with a task-pattern phrase
PARTIAL_OVERLAP_MIN = 0.34           # min token overlap to count a partial match
PRIMARY_CUTOFF_FLOOR = 0.75          # a primary skill must score at least this
PRIMARY_CUTOFF_RATIO = 0.35          # ...and at least this fraction of the top score
AGENT_PATTERN_DIRECT_BONUS = 1.0     # owning agent's phrase matched the query verbatim
AGENT_PATTERN_OVERLAP_WEIGHT = 0.5   # ...partial overlap with the owning agent's phrase
WEAK_PATTERN_TOKENS = {
    "analysis",
    "data",
    "docs",
    "documentation",
    "document",
    "quality",
    "review",
    "this",
    "write",
    "writing",
}
SOFTWARE_REVIEW_ACTION_TOKENS = {"review", "documentation", "functionality", "structure", "usefulness"}
SCIENTIFIC_CONTEXT_TOKENS = {
    "abstract",
    "annotation",
    "assembly",
    "bioinformatics",
    "biology",
    "contig",
    "doi",
    "genome",
    "mag",
    "manuscript",
    "metagenome",
    "omics",
    "paper",
    "proposal",
    "protein",
    "scientific",
    "sequence",
}


@dataclass
class WorkflowEdge:
    source: str
    target: str
    evidence: str


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "build":
        repo_root = resolve_repo_root(args.repo)
        payload = build_outputs(repo_root)
        if args.include_agent is not None or args.include_skill is not None:
            payload = filter_catalog_payload(
                payload,
                include_agents=args.include_agent,
                include_skills=args.include_skill,
            )
        out_dir = Path(args.out).expanduser().resolve() if args.out else default_output_dir(repo_root)
        out_dir.mkdir(parents=True, exist_ok=True)
        write_outputs(payload, out_dir)
        print(json.dumps({"catalog": str(out_dir / "catalog.json")}, indent=2))
        return 0

    if args.command == "route":
        result = route_request(
            task=args.task,
            agent=args.agent,
            platform=args.platform,
            top_k=args.top_k,
            repo=args.repo,
            index_root=args.index_root,
        )
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(format_route_result(result))
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and query the omics skill catalog.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_cmd = subparsers.add_parser("build", help="Build catalog files from the repository.")
    build_cmd.add_argument("--repo", default=None, help="Repository root. Defaults to the parent of this script.")
    build_cmd.add_argument("--out", default=None, help="Output directory. Defaults to <repo>/catalog.")
    build_cmd.add_argument(
        "--include-agent",
        action="append",
        default=None,
        help="Agent name or file to include. Repeat for selected installs.",
    )
    build_cmd.add_argument(
        "--include-skill",
        action="append",
        default=None,
        help="Skill directory/name to include. Repeat for selected installs.",
    )

    route_cmd = subparsers.add_parser("route", help="Recommend an agent and ordered skills for a task.")
    route_cmd.add_argument("task", help="Task description.")
    route_cmd.add_argument("--repo", default=None, help="Repository root. If omitted, the script infers it when possible.")
    route_cmd.add_argument("--index-root", default=None, help="Directory containing catalog.json.")
    route_cmd.add_argument("--agent", default=None, help="Limit recommendations to a specific installed agent.")
    route_cmd.add_argument("--platform", choices=("generic", "claude", "codex"), default="generic")
    route_cmd.add_argument("--top-k", type=int, default=4, help="Maximum number of primary skills to return.")
    route_cmd.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser


def resolve_repo_root(repo: str | None) -> Path:
    if repo:
        return Path(repo).expanduser().resolve()
    script_path = Path(__file__).resolve()
    candidate = script_path.parent.parent
    if is_repo_root(candidate):
        return candidate
    raise SystemExit("Could not determine the repository root. Pass --repo explicitly.")


def default_output_dir(repo_root: Path) -> Path:
    return repo_root / "catalog"


def is_repo_root(path: Path) -> bool:
    return (path / "skills").is_dir() and (path / "agents").is_dir()


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    frontmatter_text = text[4:end]
    body = text[end + 5 :]
    return parse_frontmatter(frontmatter_text), body


def parse_frontmatter(block: str) -> dict[str, str]:
    data: dict[str, str] = {}
    lines = block.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if ":" not in line or not line.strip():
            index += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value in {">", ">-", "|", "|-"}:
            folded = value.startswith(">")
            index += 1
            payload: list[str] = []
            while index < len(lines):
                continuation = lines[index]
                if continuation.startswith(" ") or continuation.startswith("\t"):
                    payload.append(continuation.strip())
                    index += 1
                    continue
                break
            data[key] = " ".join(payload).strip() if folded else "\n".join(payload).strip()
            continue
        data[key] = value.strip('"').strip("'")
        index += 1
    return data


def extract_section(markdown: str, heading: str) -> str:
    marker = f"## {heading}"
    start = markdown.find(marker)
    if start == -1:
        return ""
    tail = markdown[start + len(marker) :]
    match = re.search(r"\n##\s+", tail)
    return tail if not match else tail[: match.start()]


def extract_first_heading(markdown: str) -> str | None:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return None


def extract_platforms(text: str) -> list[str]:
    lowered = text.lower()
    platforms: list[str] = []
    if "claude code" in lowered or "claude" in lowered:
        platforms.append("claude")
    if "codex" in lowered:
        platforms.append("codex")
    return sorted(set(platforms)) or ["claude", "codex"]


def extract_skill_references(markdown: str, exclude: str) -> tuple[list[str], dict[str, list[str]]]:
    references: list[str] = []
    contexts: dict[str, list[str]] = {}
    for line in markdown.splitlines():
        for match in SKILL_REF_PATTERN.findall(line):
            if match == exclude:
                continue
            references.append(match)
            contexts.setdefault(match, []).append(line.strip())
    return sorted(set(references)), contexts


def parse_skill_sections(markdown: str) -> dict[str, list[str]]:
    content = extract_section(markdown, "Mandatory Skill Usage")
    sections: dict[str, list[str]] = {}
    current_section = "General"
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if line.startswith("### "):
            current_section = line[4:].strip()
            continue
        matches = SKILL_REF_PATTERN.findall(line)
        if matches:
            sections.setdefault(current_section, []).extend(matches)
    return sections


def arrow_depth(line: str) -> int:
    positions = [index for index in (line.find("├"), line.find("└")) if index >= 0]
    return min(positions) if positions else -1


def dedupe_workflow_edges(edges: list[WorkflowEdge]) -> list[WorkflowEdge]:
    seen: set[tuple[str, str]] = set()
    deduped: list[WorkflowEdge] = []
    for edge in edges:
        key = (edge.source, edge.target)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(edge)
    return deduped


def parse_workflow_edges(markdown: str) -> list[WorkflowEdge]:
    content = extract_section(markdown, "Workflow Decision Tree")
    code_blocks = re.findall(r"```(.*?)```", content, flags=re.DOTALL)
    if not code_blocks:
        return []
    tree = code_blocks[0]
    edges: list[WorkflowEdge] = []
    stack: list[tuple[int, str]] = []
    for raw_line in tree.splitlines():
        branch_depth = arrow_depth(raw_line)
        names = SKILL_REF_PATTERN.findall(raw_line)
        if not names:
            if branch_depth >= 0:
                stack = [(level, skill) for level, skill in stack if level < branch_depth]
            continue
        depth = branch_depth if branch_depth >= 0 else raw_line.find("/")
        parent = next((skill for level, skill in reversed(stack) if level < depth), None)
        previous = parent
        for name in names:
            if previous and previous != name:
                edges.append(WorkflowEdge(source=previous, target=name, evidence=raw_line.strip()))
            previous = name
        stack = [(level, skill) for level, skill in stack if level < depth]
        stack.append((depth, names[-1]))
    return dedupe_workflow_edges(edges)


def parse_task_patterns(markdown: str) -> list[dict[str, Any]]:
    content = extract_section(markdown, "Task Recognition Patterns")
    patterns: list[dict[str, Any]] = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if "→" not in line:
            continue
        skills = SKILL_REF_PATTERN.findall(line)
        if not skills:
            continue
        phrases = QUOTED_PATTERN.findall(line.split("→", 1)[0])
        patterns.append({"skill_name": skills[0], "phrases": phrases})
    return patterns


def tokenize(text: str) -> set[str]:
    return {token for token in TOKEN_PATTERN.findall(text.lower()) if len(token) > 2}


def text_overlap(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    common = left & right
    if not common:
        return 0.0
    return len(common) / len(right)


def task_pattern_overlap(query_tokens: set[str], pattern_tokens: set[str]) -> float:
    """Token overlap for task-recognition phrases.

    Multi-token phrases may match on one distinctive token, but a lone generic
    word such as "review" must not activate "peer review" or "review council".
    """
    if not query_tokens or not pattern_tokens:
        return 0.0
    common = query_tokens & pattern_tokens
    if not common:
        return 0.0
    if len(pattern_tokens) > 1 and len(common) < 2 and common <= WEAK_PATTERN_TOKENS:
        return 0.0
    return len(common) / len(pattern_tokens)


def is_software_repo_review(query_tokens: set[str]) -> bool:
    """Detect off-domain software repository review requests.

    The omics-skills router has no code-review skill. Explicit code/repo review
    prompts should stay silent instead of matching scientific review patterns.
    """
    has_repo_subject = bool(query_tokens & {"repo", "repository"}) or (
        "code" in query_tokens and "review" in query_tokens
    )
    has_review_action = bool(query_tokens & SOFTWARE_REVIEW_ACTION_TOKENS)
    has_scientific_context = bool(query_tokens & SCIENTIFIC_CONTEXT_TOKENS)
    return has_repo_subject and has_review_action and not has_scientific_context


def parse_repo(repo_root: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    skills: dict[str, dict[str, Any]] = {}
    for skill_file in sorted((repo_root / "skills").glob("*/SKILL.md")):
        raw_text = skill_file.read_text(encoding="utf-8")
        frontmatter, body = split_frontmatter(raw_text)
        name = frontmatter.get("name", skill_file.parent.name).strip()
        references, contexts = extract_skill_references(body, exclude=name)
        skills[name] = {
            "name": name,
            "title": extract_first_heading(body) or name,
            "description": frontmatter.get("description", "").strip(),
            "path": str(skill_file.relative_to(repo_root)),
            "platforms": extract_platforms("\n".join((frontmatter.get("description", ""), body))),
            "agents": [],
            "sections": [],
            "task_patterns": [],
            "internal_references": references,
            "reference_contexts": contexts,
        }

    agents: dict[str, dict[str, Any]] = {}
    for agent_file in sorted((repo_root / "agents").glob("*.md")):
        raw_text = agent_file.read_text(encoding="utf-8")
        frontmatter, body = split_frontmatter(raw_text)
        name = frontmatter.get("name", agent_file.stem).strip()
        agent = {
            "name": name,
            "description": frontmatter.get("description", "").strip(),
            "path": str(agent_file.relative_to(repo_root)),
            "skill_sections": parse_skill_sections(body),
            "workflow_edges": parse_workflow_edges(body),
            "task_patterns": parse_task_patterns(body),
        }
        agents[name] = agent
        for section, section_skills in agent["skill_sections"].items():
            for skill_name in section_skills:
                if skill_name in skills:
                    skills[skill_name]["agents"].append(name)
                    skills[skill_name]["sections"].append(section)
        for pattern in agent["task_patterns"]:
            skill_name = pattern["skill_name"]
            if skill_name in skills:
                skills[skill_name]["agents"].append(name)
                skills[skill_name]["task_patterns"].extend(pattern["phrases"])

    for skill in skills.values():
        skill["agents"] = sorted(set(skill["agents"]))
        skill["sections"] = sorted(set(skill["sections"]))
        skill["task_patterns"] = sorted(set(skill["task_patterns"]))
    return skills, agents


def infer_reference_relationship(contexts: list[str]) -> tuple[str, float]:
    joined = " ".join(contexts).lower()
    if any(token in joined for token in ("requires", "must use", "depends on", "prerequisite")):
        return "depend_on", 0.9
    if any(token in joined for token in ("part of", "sub-task", "subtask", "component of")):
        return "belong_to", 0.85
    if any(token in joined for token in ("instead of", "alternative", "substitute", "same function")):
        return "similar_to", 0.8
    if any(token in joined for token in ("after", "before", "next", "use ", "invoke", "follow")):
        return "compose_with", 0.75
    return "compose_with", 0.6


def merge_edges(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for edge in edges:
        key = (edge["source"], edge["target"], edge["type"], edge["source_type"], edge["target_type"])
        current = merged.get(key)
        if current is None:
            merged[key] = edge
            continue
        current["confidence"] = max(current["confidence"], edge["confidence"])
        current["provenance"] = sorted(set(current["provenance"] + edge["provenance"]))
        current["evidence"] = sorted(set(current["evidence"] + edge["evidence"]))
    return sorted(merged.values(), key=lambda item: (item["source"], item["type"], item["target"]))


_BUILD_CACHE: dict[str, tuple[tuple[int, int], dict[str, Any]]] = {}


def _repo_signature(repo_root: Path) -> tuple[int, int]:
    """Cheap change-detector for the catalog cache: (file count, newest mtime)
    across all SKILL.md and agent files. Adding, removing, or editing any source
    file changes the signature and busts the cache."""
    sources = list((repo_root / "skills").glob("*/SKILL.md"))
    sources += list((repo_root / "agents").glob("*.md"))
    latest = 0
    for path in sources:
        try:
            latest = max(latest, path.stat().st_mtime_ns)
        except OSError:
            continue
    return (len(sources), latest)


def build_outputs(repo_root: Path, use_cache: bool = True) -> dict[str, Any]:
    """Build the catalog payload, memoized by (repo path, source signature).

    parse_repo re-reads and regex-parses ~40 markdown files; the router and the
    benchmark call this repeatedly for the same repo, so caching turns N rebuilds
    into one. Callers may freely mutate the result (e.g. _absolutize_paths
    rewrites paths in place): the cache always stores and returns independent
    deep copies, so a mutated result never corrupts a later build."""
    key = str(repo_root)
    signature = _repo_signature(repo_root)
    if use_cache:
        cached = _BUILD_CACHE.get(key)
        if cached is not None and cached[0] == signature:
            return copy.deepcopy(cached[1])
    payload = _build_catalog(repo_root)
    if use_cache:
        _BUILD_CACHE[key] = (signature, copy.deepcopy(payload))
    return payload


def _build_catalog(repo_root: Path) -> dict[str, Any]:
    skills, agents = parse_repo(repo_root)
    edges: list[dict[str, Any]] = []

    for agent in agents.values():
        for skill_names in agent["skill_sections"].values():
            for skill_name in skill_names:
                if skill_name not in skills:
                    continue
                edges.append(
                    {
                        "source": agent["name"],
                        "target": skill_name,
                        "type": "uses",
                        "source_type": "agent",
                        "target_type": "skill",
                        "confidence": 1.0,
                        "provenance": ["mandatory_skill_usage"],
                        "evidence": [agent["path"]],
                    }
                )
        for workflow_edge in agent["workflow_edges"]:
            if workflow_edge.source not in skills or workflow_edge.target not in skills:
                continue
            edges.append(
                {
                    "source": workflow_edge.source,
                    "target": workflow_edge.target,
                    "type": "workflow_next",
                    "source_type": "skill",
                    "target_type": "skill",
                    "confidence": 0.95,
                    "provenance": ["workflow_decision_tree"],
                    "evidence": [workflow_edge.evidence],
                }
            )
            edges.append(
                {
                    "source": workflow_edge.target,
                    "target": workflow_edge.source,
                    "type": "depend_on",
                    "source_type": "skill",
                    "target_type": "skill",
                    "confidence": 0.95,
                    "provenance": ["workflow_decision_tree"],
                    "evidence": [workflow_edge.evidence],
                }
            )

    for skill in skills.values():
        for reference in skill["internal_references"]:
            if reference not in skills:
                continue
            relation_type, confidence = infer_reference_relationship(skill["reference_contexts"].get(reference, []))
            edges.append(
                {
                    "source": skill["name"],
                    "target": reference,
                    "type": relation_type,
                    "source_type": "skill",
                    "target_type": "skill",
                    "confidence": confidence,
                    "provenance": ["skill_body_reference"],
                    "evidence": skill["reference_contexts"].get(reference, []),
                }
            )

    merged_edges = merge_edges(edges)
    # Metadata is intentionally deterministic (no build timestamp or absolute
    # source path) so the committed catalog/catalog.json is byte-stable across
    # machines and a `git diff` freshness check is meaningful.
    metadata = {
        "skill_count": len(skills),
        "agent_count": len(agents),
        "edge_count": len(merged_edges),
    }
    catalog = {
        "metadata": metadata,
        "skills": [skills[name] for name in sorted(skills)],
        "agents": [
            {
                "name": agent["name"],
                "description": agent["description"],
                "path": agent["path"],
                "skill_sections": {section: sorted(set(items)) for section, items in sorted(agent["skill_sections"].items())},
                "workflow_edges": [edge.__dict__ for edge in agent["workflow_edges"]],
                "task_patterns": agent["task_patterns"],
            }
            for agent in sorted(agents.values(), key=lambda item: item["name"])
        ],
        "edges": merged_edges,
    }
    # catalog.json is the single source of truth. The router consumes only
    # catalog["skills"], ["agents"], and ["edges"]; earlier builds also emitted
    # routing.json and relationships.json, but both were lossless projections of
    # this structure that nothing read, so they were removed.
    return {"catalog": catalog}


def _agent_filter_name(value: str) -> str:
    return Path(value).stem


def _skill_filter_name(value: str) -> str:
    return Path(value).name


def filter_catalog_payload(
    payload: dict[str, Any],
    include_agents: list[str] | None = None,
    include_skills: list[str] | None = None,
) -> dict[str, Any]:
    """Return a catalog limited to selected installed agents and skills.

    Selected installs must not recommend uninstalled components. The filter
    trims agent sections, task patterns, workflow edges, and graph edges, then
    recomputes each skill's owning agents and patterns from the remaining
    agents.
    """
    filtered = copy.deepcopy(payload)
    catalog = filtered["catalog"]
    agent_names = (
        {_agent_filter_name(value) for value in include_agents}
        if include_agents is not None
        else {agent["name"] for agent in catalog["agents"]}
    )
    skill_names = (
        {_skill_filter_name(value) for value in include_skills}
        if include_skills is not None
        else {skill["name"] for skill in catalog["skills"]}
    )

    skills = [skill for skill in catalog["skills"] if skill["name"] in skill_names]
    remaining_skill_names = {skill["name"] for skill in skills}

    agents: list[dict[str, Any]] = []
    for agent in catalog["agents"]:
        if agent["name"] not in agent_names:
            continue
        agent = copy.deepcopy(agent)
        agent["skill_sections"] = {
            section: [skill for skill in section_skills if skill in remaining_skill_names]
            for section, section_skills in agent.get("skill_sections", {}).items()
        }
        agent["skill_sections"] = {
            section: section_skills
            for section, section_skills in agent["skill_sections"].items()
            if section_skills
        }
        agent["task_patterns"] = [
            pattern
            for pattern in agent.get("task_patterns", [])
            if pattern.get("skill_name") in remaining_skill_names
        ]
        agent["workflow_edges"] = [
            edge
            for edge in agent.get("workflow_edges", [])
            if edge.get("source") in remaining_skill_names and edge.get("target") in remaining_skill_names
        ]
        agents.append(agent)

    for skill in skills:
        skill["agents"] = []
        skill["sections"] = []
        skill["task_patterns"] = []

    skills_by_name = {skill["name"]: skill for skill in skills}
    for agent in agents:
        for section, section_skills in agent.get("skill_sections", {}).items():
            for skill_name in section_skills:
                if skill_name in skills_by_name:
                    skills_by_name[skill_name]["agents"].append(agent["name"])
                    skills_by_name[skill_name]["sections"].append(section)
        for pattern in agent.get("task_patterns", []):
            skill_name = pattern.get("skill_name")
            if skill_name in skills_by_name:
                skills_by_name[skill_name]["task_patterns"].extend(pattern.get("phrases", []))

    for skill in skills:
        skill["agents"] = sorted(set(skill["agents"]))
        skill["sections"] = sorted(set(skill["sections"]))
        skill["task_patterns"] = sorted(set(skill["task_patterns"]))

    remaining_agent_names = {agent["name"] for agent in agents}
    edges: list[dict[str, Any]] = []
    for edge in catalog["edges"]:
        if edge.get("source_type") == "agent":
            if edge.get("source") in remaining_agent_names and edge.get("target") in remaining_skill_names:
                edges.append(edge)
            continue
        if edge.get("source_type") == "skill" and edge.get("target_type") == "skill":
            if edge.get("source") in remaining_skill_names and edge.get("target") in remaining_skill_names:
                edges.append(edge)

    catalog["skills"] = sorted(skills, key=lambda item: item["name"])
    catalog["agents"] = sorted(agents, key=lambda item: item["name"])
    catalog["edges"] = merge_edges(edges)
    catalog["metadata"] = {
        "skill_count": len(catalog["skills"]),
        "agent_count": len(catalog["agents"]),
        "edge_count": len(catalog["edges"]),
    }
    return filtered


def write_outputs(payload: dict[str, Any], out_dir: Path) -> None:
    (out_dir / "catalog.json").write_text(json.dumps(payload["catalog"], indent=2), encoding="utf-8")


def collect_unresolved_references(repo_root: Path) -> list[tuple[str, str, str]]:
    """Return (source_kind, source_name, unresolved_ref) triples for every /skill-like
    token in the repo that does not resolve to an actual skill directory. Used by tests
    to hard-error on skill graph inconsistencies.
    """
    skills, agents = parse_repo(repo_root)
    real = set(skills)
    unresolved: list[tuple[str, str, str]] = []
    for agent in agents.values():
        for section_skills in agent["skill_sections"].values():
            for skill_name in section_skills:
                if skill_name not in real:
                    unresolved.append(("agent", agent["name"], skill_name))
        for pattern in agent["task_patterns"]:
            if pattern["skill_name"] not in real:
                unresolved.append(("agent_task_pattern", agent["name"], pattern["skill_name"]))
        for edge in agent["workflow_edges"]:
            for name in (edge.source, edge.target):
                if name not in real:
                    unresolved.append(("workflow_edge", agent["name"], name))
    for skill in skills.values():
        for ref in skill["internal_references"]:
            if ref not in real:
                unresolved.append(("skill_body", skill["name"], ref))
    return sorted(set(unresolved))


def load_outputs(index_root: Path) -> dict[str, Any]:
    return {
        "catalog": json.loads((index_root / "catalog.json").read_text(encoding="utf-8")),
    }


def resolve_route_source(repo: str | None, index_root: str | None) -> tuple[dict[str, Any], str]:
    if index_root:
        resolved = Path(index_root).expanduser().resolve()
        source_mode = "installed" if (resolved / "skill_index.py").exists() else "index"
        payload = load_outputs(resolved)
        _absolutize_paths(payload, catalog_dir=resolved)
        return payload, source_mode
    if repo:
        repo_root = resolve_repo_root(repo)
        payload = build_outputs(repo_root)
        _absolutize_paths(payload, catalog_dir=repo_root / "catalog")
        return payload, "repo"

    invoked_root = invoked_index_root()
    if invoked_root is not None:
        payload = load_outputs(invoked_root)
        _absolutize_paths(payload, catalog_dir=invoked_root)
        return payload, "installed"

    script_path = Path(__file__).resolve()
    repo_candidate = script_path.parent.parent
    if is_repo_root(repo_candidate):
        catalog_dir = repo_candidate / "catalog"
        # Prefer the committed catalog.json over re-parsing every SKILL.md.
        # This keeps the per-prompt routing hook fast; CI guarantees the
        # committed catalog stays in sync with the markdown sources.
        if (catalog_dir / "catalog.json").exists():
            payload = load_outputs(catalog_dir)
        else:
            payload = build_outputs(repo_candidate)
        _absolutize_paths(payload, catalog_dir=catalog_dir)
        return payload, "repo"

    installed_root = script_path.parent
    if (installed_root / "catalog.json").exists():
        payload = load_outputs(installed_root)
        _absolutize_paths(payload, catalog_dir=installed_root)
        return payload, "installed"

    raise SystemExit("Could not find catalog files. Pass --repo or --index-root explicitly.")


def invoked_index_root() -> Path | None:
    """Return the invocation directory when it contains an installed catalog.

    Symlink installs make ``Path(__file__).resolve()`` point back to the repo
    script, while ``sys.argv[0]`` remains the installed symlink path. Prefer the
    installed catalog in that case so selected installs only route to installed
    components.
    """
    if not sys.argv or not sys.argv[0]:
        return None
    invocation = Path(sys.argv[0]).expanduser()
    if not invocation.is_absolute():
        invocation = Path.cwd() / invocation
    candidate = invocation.parent
    if (candidate / "catalog.json").exists():
        return candidate.resolve()
    return None


def _is_relative_skill_path(value: str) -> bool:
    """Relative paths we emit always start with skills/ or agents/. Anything
    else (POSIX absolute `/…`, Windows absolute `C:\\…`, `~/…`) should pass
    through untouched."""
    return value.startswith("skills/") or value.startswith("agents/")


def _absolutize_paths(payload: dict[str, Any], catalog_dir: Path | None = None) -> None:
    """Resolve repo-relative `path` fields in the catalog to absolute paths.
    Callers downstream (route_request, format_route_result) assume absolute
    paths so the router can print a usable location regardless of the cwd at
    invocation time.

    The base repo is discovered from ``catalog_dir``'s location: catalog.json
    sits at ``<repo>/catalog/catalog.json`` in every checkout, so the parent of
    its directory is the repo root. This makes a committed catalog.json resolve
    correctly in any clone without baking the committing machine's path into the
    file. When no repo context is found (e.g. catalog.json copied into a bare
    directory), paths are left repo-relative; installed layouts override them
    via installed_skill_path / installed_agent_path instead."""
    catalog = payload.get("catalog")
    if not catalog:
        return

    base: Path | None = None
    if catalog_dir is not None:
        # catalog.json is usually at <repo>/catalog/catalog.json or at
        # <install-root>/catalog.json. Walk up one level first, then check
        # the dir itself (installed layouts keep skills/ at the home level).
        for candidate in (catalog_dir.parent, catalog_dir):
            if is_repo_root(candidate):
                base = candidate
                break

    if base is None:
        return

    def resolve(value: str) -> str:
        if _is_relative_skill_path(value):
            return str(base / value)
        return value

    for item in catalog.get("skills", []):
        if "path" in item:
            item["path"] = resolve(item["path"])
    for item in catalog.get("agents", []):
        if "path" in item:
            item["path"] = resolve(item["path"])


def _allowed_skills_for_agent(
    agent: str | None, agents: dict[str, dict[str, Any]]
) -> set[str] | None:
    """The set of skills an agent is allowed to recommend (its Mandatory Skill
    Usage entries), or None when no agent constraint is given."""
    if not agent:
        return None
    agent_record = agents.get(agent)
    if not agent_record:
        raise SystemExit(f"Unknown agent: {agent}")
    allowed: set[str] = set()
    for section_skills in agent_record["skill_sections"].values():
        allowed.update(section_skills)
    return allowed


def _score_skills(
    skills: dict[str, dict[str, Any]],
    query: str,
    query_tokens: set[str],
    allowed_skills: set[str] | None,
    platform: str,
    reasons: dict[str, list[str]],
) -> dict[str, float]:
    """Score each candidate skill by query overlap with its name/description and
    its task-pattern phrases. Records match explanations in ``reasons`` (mutated
    in place). Skills that fail the agent/platform filter or score 0 are dropped."""
    scores: dict[str, float] = {}
    for skill in skills.values():
        if allowed_skills is not None and skill["name"] not in allowed_skills:
            continue
        if platform in ("claude", "codex") and platform not in skill["platforms"]:
            continue
        score = 0.0
        description_tokens = tokenize(" ".join((skill["name"].replace("-", " "), skill["description"])))
        overlap = text_overlap(query_tokens, description_tokens)
        if overlap:
            score += overlap * SKILL_DESCRIPTION_WEIGHT
            reasons[skill["name"]].append("name/description overlap")
        for pattern in skill["task_patterns"]:
            if pattern.lower() in query:
                score += TASK_PATTERN_DIRECT_BONUS
                reasons[skill["name"]].append(f'task pattern "{pattern}" matched directly')
                continue
            pattern_overlap = task_pattern_overlap(query_tokens, tokenize(pattern))
            if pattern_overlap >= PARTIAL_OVERLAP_MIN:
                score += pattern_overlap * TASK_PATTERN_OVERLAP_WEIGHT
                reasons[skill["name"]].append(f'task pattern "{pattern}" overlapped')
        if score > 0:
            scores[skill["name"]] = score
    return scores


def _rank_primary_skills(skill_scores: dict[str, float], top_k: int) -> list[tuple[str, float]]:
    """Sort skills by score (desc, then name) and drop anything below the
    confidence cutoff. Returns all surviving (name, score) pairs; the caller
    takes the first ``top_k`` as primary skills."""
    ranked = sorted(skill_scores.items(), key=lambda item: (-item[1], item[0]))
    if ranked:
        cutoff = max(PRIMARY_CUTOFF_FLOOR, ranked[0][1] * PRIMARY_CUTOFF_RATIO)
        ranked = [item for item in ranked if item[1] >= cutoff]
    return ranked


def _score_agents(
    primary_skills: list[str],
    skills: dict[str, dict[str, Any]],
    agents: dict[str, dict[str, Any]],
    agent: str | None,
    query: str,
    query_tokens: set[str],
    skill_scores: dict[str, float],
    reasons: dict[str, list[str]],
) -> dict[str, float]:
    """Attribute each primary skill's score to its owning agent(s), then add two
    tiebreaks for shared skills — section-heading overlap and per-agent
    task-pattern matches — plus a small agent-description overlap term. E.g.
    bio-logic is co-owned by omics-scientist ("...Hypothesis Formation") and
    science-writer ("...Evaluation"); a "hypothesis" query thus prefers
    omics-scientist. Mutates ``reasons`` with tiebreak explanations."""
    agent_scores: dict[str, float] = defaultdict(float)
    for skill_name in primary_skills:
        for owner in skills[skill_name]["agents"]:
            agent_scores[owner] += skill_scores[skill_name]
            owner_record = agents.get(owner) or {}
            for section, section_skills in owner_record.get("skill_sections", {}).items():
                if skill_name not in section_skills:
                    continue
                section_overlap = text_overlap(query_tokens, tokenize(section))
                if section_overlap:
                    agent_scores[owner] += section_overlap * skill_scores[skill_name]
                    reasons[skill_name].append(
                        f"section-heading '{section}' overlap for agent {owner}"
                    )
            for pattern_entry in owner_record.get("task_patterns", []):
                if pattern_entry.get("skill_name") != skill_name:
                    continue
                for phrase in pattern_entry.get("phrases", []):
                    phrase_tokens = tokenize(phrase)
                    if phrase.lower() in query:
                        agent_scores[owner] += AGENT_PATTERN_DIRECT_BONUS
                        reasons[skill_name].append(f'agent {owner} pattern "{phrase}" direct match')
                        break
                    phrase_overlap = task_pattern_overlap(query_tokens, phrase_tokens)
                    if phrase_overlap >= PARTIAL_OVERLAP_MIN:
                        agent_scores[owner] += phrase_overlap * AGENT_PATTERN_OVERLAP_WEIGHT
                        reasons[skill_name].append(f'agent {owner} pattern "{phrase}" overlap')
    for agent_name, agent_record in agents.items():
        if agent and agent_name != agent:
            continue
        agent_scores[agent_name] += text_overlap(query_tokens, tokenize(agent_record["description"]))
    return agent_scores


def _compose_extras(
    primary_set: set[str],
    dep_skills: list[str],
    edges: list[dict[str, Any]],
    allowed_skills: set[str] | None,
    platform: str,
    skills: dict[str, dict[str, Any]],
) -> list[str]:
    """Skills a primary skill directly recommends via a `compose_with` edge,
    excluding anything already primary or a dependency, and respecting the
    agent/platform filters."""
    extras: list[str] = []
    seen: set[str] = set()
    dep_set = set(dep_skills)
    for neighbor in compose_neighbors(primary_set, edges):
        if neighbor in primary_set or neighbor in dep_set or neighbor in seen:
            continue
        if allowed_skills is not None and neighbor not in allowed_skills:
            continue
        if platform in ("claude", "codex") and neighbor in skills:
            if platform not in skills[neighbor]["platforms"]:
                continue
        extras.append(neighbor)
        seen.add(neighbor)
    return extras


def _result_paths(
    selected_agent: str | None,
    ordered_skills: list[str],
    skills: dict[str, dict[str, Any]],
    agents: dict[str, dict[str, Any]],
    source_mode: str,
    platform: str,
) -> tuple[str | None, dict[str, str]]:
    """Resolve the agent file path and per-skill file paths for the result. When
    consuming an installed catalog, rewrite paths to the installed locations."""
    agent_path = agents[selected_agent]["path"] if selected_agent in agents else None
    skill_paths = {name: skills[name]["path"] for name in ordered_skills if name in skills}
    if source_mode == "installed":
        if selected_agent:
            agent_path = installed_agent_path(selected_agent, platform, fallback=agent_path)
        skill_paths = {
            name: installed_skill_path(name, fallback=skills[name]["path"])
            for name in ordered_skills
            if name in skills
        }
    return agent_path, skill_paths


def route_request(
    task: str,
    agent: str | None,
    platform: str,
    top_k: int,
    repo: str | None,
    index_root: str | None,
) -> dict[str, Any]:
    payload, source_mode = resolve_route_source(repo=repo, index_root=index_root)
    catalog = payload["catalog"]
    skills = {item["name"]: item for item in catalog["skills"]}
    agents = {item["name"]: item for item in catalog["agents"]}
    edges = catalog["edges"]

    query = task.lower()
    query_tokens = tokenize(task)
    allowed_skills = _allowed_skills_for_agent(agent, agents)

    if agent is None and is_software_repo_review(query_tokens):
        return {
            "task": task,
            "platform": platform,
            "agent": None,
            "primary_skills": [],
            "supporting_skills": [],
            "ordered_skills": [],
            "skill_scores": {},
            "reasons": {},
            "agent_path": None,
            "skill_paths": {},
        }

    reasons: dict[str, list[str]] = defaultdict(list)
    skill_scores = _score_skills(skills, query, query_tokens, allowed_skills, platform, reasons)
    ranked_pairs = _rank_primary_skills(skill_scores, top_k)
    primary_skills = [name for name, _ in ranked_pairs[:top_k]]

    agent_scores = _score_agents(
        primary_skills, skills, agents, agent, query, query_tokens, skill_scores, reasons
    )
    selected_agent = agent or (
        max(agent_scores.items(), key=lambda item: (item[1], item[0]))[0] if agent_scores else None
    )

    dep_skills = ordered_dependencies(primary_skills, edges)
    primary_set = set(primary_skills)
    # Order only the primary + strict-dependency set through the workflow
    # topological sort — pulling compose_with neighbours through it produces
    # huge "also consider" tails of unrelated skills.
    ordered_skills = ordered_workflow(dep_skills, edges)
    compose_extras = _compose_extras(primary_set, dep_skills, edges, allowed_skills, platform, skills)
    supporting_only = [name for name in dep_skills if name not in primary_set] + compose_extras

    agent_path, skill_paths = _result_paths(
        selected_agent, ordered_skills, skills, agents, source_mode, platform
    )
    ranked_names = {name for name, _ in ranked_pairs}
    return {
        "task": task,
        "platform": platform,
        "agent": selected_agent,
        "primary_skills": primary_skills,
        "supporting_skills": supporting_only,
        "ordered_skills": ordered_skills,
        "skill_scores": {name: round(score, 3) for name, score in ranked_pairs},
        "reasons": {name: sorted(set(values)) for name, values in reasons.items() if name in ranked_names},
        "agent_path": agent_path,
        "skill_paths": skill_paths,
    }


def compose_neighbors(primary_set: set[str], edges: list[dict[str, Any]]) -> list[str]:
    """Return skills that any primary skill explicitly cites via a
    `compose_with` edge (outgoing direction only). Treated as a tight
    supporting list — not reverse-direction, not `similar_to`, not
    transitive — so a primary-skill hit surfaces only the partners that
    skill's body directly recommends. Keeps the router from snowballing
    unrelated sibling skills into every query."""
    neighbors: list[str] = []
    seen: set[str] = set()
    for edge in edges:
        if edge.get("source_type") != "skill" or edge.get("target_type") != "skill":
            continue
        if edge.get("type") != "compose_with":
            continue
        source = edge.get("source")
        target = edge.get("target")
        if source in primary_set and target not in primary_set and target not in seen:
            neighbors.append(target)
            seen.add(target)
    return neighbors


def ordered_dependencies(
    primary_skills: list[str],
    edges: list[dict[str, Any]],
    max_depth: int = DEPENDENCY_MAX_DEPTH,
) -> list[str]:
    """Return the primary skills plus their prerequisites, dependency-first.

    Dependencies are followed at most ``max_depth`` hops out from each primary
    skill. Because depend_on is the reverse of the workflow_next chain, an
    unbounded walk pulls a whole pipeline (reads -> assembly -> binning -> ...)
    into the supporting list for any single-step query; the depth cap keeps it to
    genuine immediate prerequisites."""
    dependencies: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        if edge["type"] == "depend_on" and edge["source_type"] == "skill" and edge["target_type"] == "skill":
            dependencies[edge["source"]].append(edge["target"])

    ordered: list[str] = []
    seen: set[str] = set()
    on_path: set[str] = set()

    def visit(skill_name: str, depth: int) -> None:
        if skill_name in seen or skill_name in on_path:
            return
        on_path.add(skill_name)
        if depth < max_depth:
            for dependency in dependencies.get(skill_name, []):
                visit(dependency, depth + 1)
        on_path.discard(skill_name)
        seen.add(skill_name)
        ordered.append(skill_name)

    for skill_name in primary_skills:
        visit(skill_name, 0)
    return ordered


def ordered_workflow(skill_names: list[str], edges: list[dict[str, Any]]) -> list[str]:
    allowed = set(skill_names)
    outgoing: dict[str, list[str]] = defaultdict(list)
    incoming: dict[str, int] = defaultdict(int)
    for edge in edges:
        if edge["type"] != "workflow_next":
            continue
        if edge["source"] not in allowed or edge["target"] not in allowed:
            continue
        outgoing[edge["source"]].append(edge["target"])
        incoming[edge["target"]] += 1
        incoming.setdefault(edge["source"], 0)

    queue = sorted(name for name in allowed if incoming.get(name, 0) == 0)
    ordered: list[str] = []
    while queue:
        current = queue.pop(0)
        ordered.append(current)
        for target in sorted(outgoing.get(current, [])):
            incoming[target] -= 1
            if incoming[target] == 0:
                queue.append(target)
                queue.sort()
    for name in skill_names:
        if name not in ordered:
            ordered.append(name)
    return ordered


def format_route_result(result: dict[str, Any]) -> str:
    lines = [
        f"Agent: {result['agent'] or 'none'}",
        f"Primary skills: {', '.join(result['primary_skills']) or 'none'}",
        f"Supporting skills: {', '.join(result['supporting_skills']) or 'none'}",
        f"Suggested order: {' -> '.join(result['ordered_skills']) or 'none'}",
    ]
    if result["agent_path"]:
        lines.append(f"Agent file: {result['agent_path']}")
    for name, path in result["skill_paths"].items():
        lines.append(f"Skill file [{name}]: {path}")
    return "\n".join(lines)


def installed_skill_path(skill_name: str, fallback: str) -> str:
    candidate = Path.home() / ".agents" / "skills" / skill_name / "SKILL.md"
    return str(candidate) if candidate.exists() else fallback


def installed_agent_path(agent_name: str, platform: str, fallback: str | None) -> str | None:
    candidates: list[Path] = []
    if platform == "claude":
        candidates.append(Path.home() / ".claude" / "agents" / f"{agent_name}.md")
    elif platform == "codex":
        candidates.append(Path.home() / ".codex" / "agents" / f"{agent_name}.md")
    else:
        candidates.append(Path.home() / ".claude" / "agents" / f"{agent_name}.md")
        candidates.append(Path.home() / ".codex" / "agents" / f"{agent_name}.md")
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return fallback


if __name__ == "__main__":
    sys.exit(main())
