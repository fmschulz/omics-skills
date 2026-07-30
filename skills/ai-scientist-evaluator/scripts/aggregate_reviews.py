#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "jsonschema==4.26.0",
#   "PyYAML==6.0.3",
# ]
# ///
"""Aggregate and rank AI scientist evaluation JSON files.

Usage:
    python scripts/aggregate_reviews.py review1.json review2.json --out_md leaderboard.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml
from jsonschema import Draft202012Validator


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = SKILL_ROOT / "assets" / "evaluation_schema.json"
WEIGHTS_PATH = SKILL_ROOT / "assets" / "default_weight_profiles.yaml"


def load_weight_profiles() -> dict[str, dict[str, float]]:
    profiles = yaml.safe_load(WEIGHTS_PATH.read_text(encoding="utf-8"))
    if not isinstance(profiles, dict):
        raise ValueError(f"{WEIGHTS_PATH} does not contain a profile mapping")
    normalized: dict[str, dict[str, float]] = {}
    for name, weights in profiles.items():
        if not isinstance(name, str) or not isinstance(weights, dict):
            raise ValueError(f"invalid weight profile: {name!r}")
        parsed = {str(category): float(weight) for category, weight in weights.items()}
        if abs(sum(parsed.values()) - 100.0) > 1e-9:
            raise ValueError(f"weight profile {name!r} does not total 100")
        normalized[name] = parsed
    return normalized


def load_review(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validation_errors = sorted(
        Draft202012Validator(schema).iter_errors(data),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if validation_errors:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
            for error in validation_errors
        )
        raise ValueError(f"{path} failed evaluation_schema.json: {details}")

    profiles = load_weight_profiles()
    profile_name = data["profile"]
    if profile_name not in profiles:
        raise ValueError(f"{path} uses unknown weight profile {profile_name!r}")
    expected_weights = profiles[profile_name]
    score_items = data["scores"]
    categories = [item["category"] for item in score_items]
    duplicate_categories = sorted(
        category for category in set(categories) if categories.count(category) > 1
    )
    missing_categories = sorted(set(expected_weights) - set(categories))
    extra_categories = sorted(set(categories) - set(expected_weights))
    if duplicate_categories or missing_categories or extra_categories:
        raise ValueError(
            f"{path} score categories do not match profile {profile_name!r}: "
            f"duplicates={duplicate_categories}, missing={missing_categories}, extra={extra_categories}"
        )

    submitted_total = float(data["overall"]["total_score_100"])
    total = 0.0
    for item in score_items:
        weight = expected_weights[item["category"]]
        points = float(item["score_0_to_5"]) / 5.0 * weight
        item["weight"] = weight
        item["weighted_points"] = round(points, 10)
        total += points
    raw_total = round(total, 10)
    data["overall"]["raw_weighted_score_100"] = raw_total
    data["overall"]["penalty_points"] = round(max(0.0, raw_total - submitted_total), 10)
    data["overall"]["total_score_100"] = min(raw_total, submitted_total)
    return data


def category_score(data: Dict[str, Any], names: Tuple[str, ...]) -> float:
    for item in data.get("scores", []):
        if item.get("category") in names:
            try:
                return float(item.get("weighted_points", 0))
            except (TypeError, ValueError):
                return 0.0
    return 0.0


def gate_fail_count(data: Dict[str, Any]) -> int:
    return sum(1 for item in data.get("gate_checks", []) if item.get("status") == "fail")


def red_flag_count(data: Dict[str, Any]) -> int:
    return len(data.get("red_flags", []))


def sort_key(data: Dict[str, Any]) -> Tuple[float, float, float, float, float, float, float]:
    total = float(data["overall"].get("total_score_100", 0))
    task = category_score(data, ("task_completion",))
    repro = category_score(data, ("reproducibility",))
    validation = category_score(data, ("validation_robustness", "benchmarking"))
    limitations = category_score(data, ("limitations_and_uncertainty",))
    writing = category_score(data, ("communication", "prose_quality"))
    penalties = gate_fail_count(data) + red_flag_count(data)
    return (total, -penalties, repro, task, validation, limitations, writing)


def format_markdown(reviews: List[Tuple[Path, Dict[str, Any]]]) -> str:
    lines = []
    lines.append("# AI Scientist Leaderboard")
    lines.append("")
    lines.append("| Rank | Submission | Scientist | Score | Recommendation | Gate fails | Red flags |")
    lines.append("|---:|---|---|---:|---|---:|---:|")
    for idx, (path, data) in enumerate(reviews, start=1):
        submission = data.get("submission_id", path.stem)
        scientist = data.get("scientist_name", "")
        score = float(data["overall"].get("total_score_100", 0))
        recommendation = data["overall"].get("recommendation", "")
        lines.append(
            f"| {idx} | {submission} | {scientist} | {score:.1f} | {recommendation} | {gate_fail_count(data)} | {red_flag_count(data)} |"
        )
    lines.append("")
    if reviews:
        winner = reviews[0][1]
        lines.append("## Winner")
        lines.append("")
        lines.append(
            f"{winner.get('submission_id', reviews[0][0].stem)} "
            f"({winner.get('scientist_name', '').strip()}) ranks first with "
            f"{float(winner['overall'].get('total_score_100', 0)):.1f}/100."
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate and rank AI scientist evaluation JSON files")
    parser.add_argument("reviews", nargs="+", help="Paths to evaluation JSON files")
    parser.add_argument("--out_md", help="Optional markdown output path")
    args = parser.parse_args()

    loaded: List[Tuple[Path, Dict[str, Any]]] = []
    for review_path in args.reviews:
        path = Path(review_path)
        try:
            loaded.append((path, load_review(path)))
        except (OSError, json.JSONDecodeError, ValueError) as error:
            parser.error(str(error))

    loaded.sort(key=lambda item: sort_key(item[1]), reverse=True)
    markdown = format_markdown(loaded)
    print(markdown)

    if args.out_md:
        Path(args.out_md).write_text(markdown, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
