#!/usr/bin/env python3
"""Validate a proposal rubric and compute its weighted recommendation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


DEFAULT_WEIGHTS = {
    "strategic_fit_and_novelty": 15,
    "technical_rigor": 25,
    "feasibility_and_resources": 20,
    "team_and_execution": 15,
    "risk_ethics_and_compliance": 15,
    "budget_and_schedule": 10,
}
DEFAULT_RECOMMENDATIONS = [
    {"minimum": 4.5, "label": "Strong Accept"},
    {"minimum": 3.7, "label": "Accept"},
    {"minimum": 2.8, "label": "Borderline"},
    {"minimum": 1.0, "label": "Reject"},
]


def validate_weights(weights: dict[str, object]) -> dict[str, float]:
    parsed = {str(category): float(weight) for category, weight in weights.items()}
    if not parsed:
        raise ValueError("rubric has no weighted categories")
    if any(weight <= 0 for weight in parsed.values()):
        raise ValueError("rubric weights must be positive")
    if abs(sum(parsed.values()) - 100.0) > 1e-9:
        raise ValueError(f"rubric weights total {sum(parsed.values()):g}, expected 100")
    return parsed


def recommendation(score: float, bands: list[dict[str, object]]) -> str:
    parsed = sorted(
        ((float(item["minimum"]), str(item["label"])) for item in bands),
        reverse=True,
    )
    for minimum, label in parsed:
        if score >= minimum:
            return label
    raise ValueError("recommendation bands do not cover the computed score")


def lowest_label(bands: list[dict[str, object]]) -> str:
    """Return the label of the band with the lowest minimum score."""
    return str(min(bands, key=lambda item: float(item["minimum"]))["label"])


def score_payload(payload: dict[str, object]) -> dict[str, object]:
    rubric = payload.get("rubric")
    if rubric is None:
        weights = validate_weights(DEFAULT_WEIGHTS)
        bands = DEFAULT_RECOMMENDATIONS
        rubric_source = "default"
    elif isinstance(rubric, dict):
        if not isinstance(rubric.get("weights"), dict):
            raise ValueError("sponsor rubric must define a weights mapping")
        if not isinstance(rubric.get("recommendations"), list):
            raise ValueError("sponsor rubric must define recommendation bands")
        weights = validate_weights(rubric["weights"])
        bands = rubric["recommendations"]
        rubric_source = "sponsor"
    else:
        raise ValueError("rubric must be an object")

    raw_scores = payload.get("scores")
    if not isinstance(raw_scores, dict):
        raise ValueError("scores must be a category-to-score mapping")
    missing = sorted(set(weights) - set(raw_scores))
    extra = sorted(set(raw_scores) - set(weights))
    if missing or extra:
        raise ValueError(f"score categories differ from rubric: missing={missing}, extra={extra}")
    scores = {category: float(raw_scores[category]) for category in weights}
    if any(score < 1 or score > 5 for score in scores.values()):
        raise ValueError("every category score must be between 1 and 5")
    weighted_mean = sum(scores[category] * weights[category] for category in weights) / 100.0
    label = recommendation(weighted_mean, bands)
    if payload.get("fatal_flaw"):
        label = str(payload.get("fatal_flaw_recommendation", lowest_label(bands)))
    return {
        "rubric_source": rubric_source,
        "weights_total": sum(weights.values()),
        "weighted_mean_1_to_5": round(weighted_mean, 4),
        "recommendation": label,
        "category_contributions": {
            category: round(scores[category] * weights[category] / 100.0, 4)
            for category in weights
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scorecard", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.scorecard.read_text(encoding="utf-8"))
        result = score_payload(payload)
    except (OSError, json.JSONDecodeError, TypeError, KeyError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        if args.output.exists():
            print(f"ERROR: refusing to overwrite {args.output}", file=sys.stderr)
            return 1
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
