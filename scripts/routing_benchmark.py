#!/usr/bin/env python3
"""Run the routing benchmark at tests/routing_benchmark.yaml against the live
router and emit a pass/fail report with aggregate metrics.

Usage:
  python3 scripts/routing_benchmark.py               # human report
  python3 scripts/routing_benchmark.py --json        # machine output
  python3 scripts/routing_benchmark.py --baseline    # write docs/routing_baseline.json
  python3 scripts/routing_benchmark.py --compare PATH  # diff current run vs a saved baseline

Exit code is 0 when every row passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import skill_index  # noqa: E402

BENCHMARK_PATH = REPO_ROOT / "tests" / "routing_benchmark.yaml"


def load_yaml(path: Path) -> list[dict[str, Any]]:
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:
        return _parse_minimal_yaml(path.read_text(encoding="utf-8"))
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _parse_minimal_yaml(text: str) -> list[dict[str, Any]]:
    """Tiny YAML subset sufficient for the benchmark file. Supports:
      - list of mappings with `- key: value` style
      - string values (plain, quoted)
      - list values in flow form [a, b, c]
    Kept dependency-free so the benchmark can run in minimal environments.
    """
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        stripped = line.lstrip()
        if stripped.startswith("- "):
            if current is not None:
                records.append(current)
            current = {}
            stripped = stripped[2:]
        if current is None:
            raise ValueError(f"YAML parse error: stray line {raw_line!r}")
        if ":" not in stripped:
            raise ValueError(f"YAML parse error: no colon in {raw_line!r}")
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            current[key] = [
                item.strip().strip('"').strip("'")
                for item in value[1:-1].split(",")
                if item.strip()
            ]
        elif value in {"null", "~", ""}:
            current[key] = None
        else:
            current[key] = value.strip('"').strip("'")
    if current is not None:
        records.append(current)
    return records


@dataclass
class RowResult:
    task: str
    passed: bool
    failures: list[str]
    actual: dict[str, Any]


def evaluate_row(row: dict[str, Any]) -> RowResult:
    task = row["task"]
    platform = row.get("platform") or "codex"
    result = skill_index.route_request(
        task=task,
        agent=None,
        platform=platform,
        top_k=4,
        repo=str(REPO_ROOT),
        index_root=None,
    )
    failures: list[str] = []

    expected_agent = row.get("expected_agent")
    if expected_agent and result["agent"] != expected_agent:
        failures.append(
            f"agent: expected {expected_agent!r}, got {result['agent']!r}"
        )

    expected_primary = row.get("expected_primary_skills") or []
    missing_primary = [s for s in expected_primary if s not in result["primary_skills"]]
    if missing_primary:
        failures.append(f"missing primary skills: {missing_primary}")

    expected_ordered = row.get("expected_ordered_includes") or []
    missing_ordered = [s for s in expected_ordered if s not in result["ordered_skills"]]
    if missing_ordered:
        failures.append(f"missing ordered skills: {missing_ordered}")

    forbidden = row.get("forbidden_skills") or []
    leaked = [
        s
        for s in forbidden
        if s in result["primary_skills"] or s in result["ordered_skills"]
    ]
    if leaked:
        failures.append(f"forbidden skills surfaced: {leaked}")

    return RowResult(
        task=task,
        passed=not failures,
        failures=failures,
        actual={
            "agent": result["agent"],
            "primary_skills": result["primary_skills"],
            "ordered_skills": result["ordered_skills"],
        },
    )


def aggregate(results: list[RowResult]) -> dict[str, Any]:
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    agent_failures = sum(1 for r in results if any(f.startswith("agent:") for f in r.failures))
    primary_failures = sum(1 for r in results if any("primary skills" in f for f in r.failures))
    ordered_failures = sum(1 for r in results if any("ordered skills" in f for f in r.failures))
    forbidden_failures = sum(1 for r in results if any("forbidden" in f for f in r.failures))
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total, 3) if total else 0.0,
        "agent_failures": agent_failures,
        "primary_skill_failures": primary_failures,
        "ordered_skill_failures": ordered_failures,
        "forbidden_skill_leaks": forbidden_failures,
    }


def format_human(results: list[RowResult], summary: dict[str, Any]) -> str:
    lines = [f"Routing benchmark: {summary['passed']}/{summary['total']} passing "
             f"({summary['pass_rate']:.1%})"]
    lines.append("")
    for r in results:
        marker = "PASS" if r.passed else "FAIL"
        lines.append(f"[{marker}] {r.task}")
        if not r.passed:
            for failure in r.failures:
                lines.append(f"    - {failure}")
            lines.append(f"    actual agent          = {r.actual['agent']}")
            lines.append(f"    actual primary_skills = {r.actual['primary_skills']}")
            lines.append(f"    actual ordered_skills = {r.actual['ordered_skills']}")
    lines.append("")
    lines.append(f"Summary: {summary}")
    return "\n".join(lines)


def run(emit_json: bool) -> int:
    rows = load_yaml(BENCHMARK_PATH)
    results = [evaluate_row(row) for row in rows]
    summary = aggregate(results)
    if emit_json:
        print(json.dumps(
            {
                "summary": summary,
                "rows": [
                    {
                        "task": r.task,
                        "passed": r.passed,
                        "failures": r.failures,
                        "actual": r.actual,
                    }
                    for r in results
                ],
            },
            indent=2,
        ))
    else:
        print(format_human(results, summary))
    return 0 if summary["failed"] == 0 else 1


def write_baseline(path: Path) -> int:
    rows = load_yaml(BENCHMARK_PATH)
    results = [evaluate_row(row) for row in rows]
    summary = aggregate(results)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "summary": summary,
                "rows": [
                    {"task": r.task, "passed": r.passed, "actual": r.actual}
                    for r in results
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Baseline written to {path} — pass_rate={summary['pass_rate']:.1%}")
    return 0


def compare(baseline_path: Path) -> int:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    rows = load_yaml(BENCHMARK_PATH)
    results = [evaluate_row(row) for row in rows]
    summary = aggregate(results)
    baseline_pass = baseline["summary"]["passed"]
    delta = summary["passed"] - baseline_pass
    sign = "+" if delta >= 0 else ""
    print(
        f"Current: {summary['passed']}/{summary['total']}  "
        f"baseline: {baseline_pass}/{baseline['summary']['total']}  "
        f"delta: {sign}{delta}"
    )
    baseline_by_task = {row["task"]: row for row in baseline["rows"]}
    regressions: list[str] = []
    fixes: list[str] = []
    silent_drift: list[tuple[str, dict, dict]] = []
    for r in results:
        previous = baseline_by_task.get(r.task)
        if previous is None:
            continue
        if previous["passed"] and not r.passed:
            regressions.append(r.task)
        elif not previous["passed"] and r.passed:
            fixes.append(r.task)
        elif not previous["passed"] and not r.passed:
            # Still failing but may have drifted to a different wrong answer.
            # Surface agent/primary-skill deltas so wrong-A → wrong-B changes
            # are visible even when the pass/fail flag is stable.
            prev_actual = previous.get("actual", {})
            if (
                prev_actual.get("agent") != r.actual["agent"]
                or prev_actual.get("primary_skills") != r.actual["primary_skills"]
            ):
                silent_drift.append((r.task, prev_actual, r.actual))
    if fixes:
        print("Fixed since baseline:")
        for task in fixes:
            print(f"  + {task}")
    if silent_drift:
        print("Drifted (still failing, different answer):")
        for task, prev_actual, now_actual in silent_drift:
            print(f"  ~ {task}")
            print(f"      was: agent={prev_actual.get('agent')!r} primary={prev_actual.get('primary_skills')}")
            print(f"      now: agent={now_actual['agent']!r} primary={now_actual['primary_skills']}")
    if regressions:
        print("Regressions since baseline:")
        for task in regressions:
            print(f"  - {task}")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--baseline", action="store_true", help="Write baseline JSON.")
    parser.add_argument(
        "--baseline-path",
        default=str(REPO_ROOT / "docs" / "routing_baseline.json"),
    )
    parser.add_argument("--compare", metavar="PATH", help="Compare vs saved baseline.")
    args = parser.parse_args(argv)

    if args.baseline:
        return write_baseline(Path(args.baseline_path))
    if args.compare:
        return compare(Path(args.compare))
    return run(emit_json=args.json)


if __name__ == "__main__":
    sys.exit(main())
