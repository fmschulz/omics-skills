#!/usr/bin/env python3
"""Validate grouped splits, predictions, calibration, imbalance, and confounding."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path


REQUIRED_COLUMNS = {
    "sample_id",
    "group_id",
    "split",
    "y_true",
    "y_pred",
    "y_score",
}


def binary(value: str, field: str) -> int:
    if value not in {"0", "1"}:
        raise ValueError(f"{field} must contain only 0 or 1, found {value!r}")
    return int(value)


def load_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        columns = reader.fieldnames or []
        missing = sorted(REQUIRED_COLUMNS - set(columns))
        if missing:
            raise ValueError(f"prediction table is missing columns: {missing}")
        rows = list(reader)
    if not rows:
        raise ValueError("prediction table has no rows")
    return rows, columns


def evaluate(
    rows: list[dict[str, str]],
    batch_column: str,
    max_brier: float,
    max_batch_prevalence_range: float,
    require_beats_null: bool,
) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    sample_splits: dict[str, set[str]] = defaultdict(set)
    group_splits: dict[str, set[str]] = defaultdict(set)
    batches: dict[str, list[int]] = defaultdict(list)
    test_truth: list[int] = []
    test_pred: list[int] = []
    test_score: list[float] = []

    for row_number, row in enumerate(rows, 2):
        split = row["split"].strip().lower()
        if split not in {"train", "validation", "test"}:
            errors.append(f"row {row_number}: invalid split {split!r}")
            continue
        truth = binary(row["y_true"].strip(), "y_true")
        pred = binary(row["y_pred"].strip(), "y_pred")
        try:
            score = float(row["y_score"])
        except ValueError as error:
            raise ValueError(f"row {row_number}: invalid y_score") from error
        if not math.isfinite(score) or not 0 <= score <= 1:
            errors.append(f"row {row_number}: y_score must be finite and between 0 and 1")
        sample_splits[row["sample_id"]].add(split)
        group_splits[row["group_id"]].add(split)
        batch = row.get(batch_column, "").strip()
        if not batch:
            errors.append(f"row {row_number}: missing confounder column value {batch_column!r}")
        else:
            batches[batch].append(truth)
        if split == "test":
            test_truth.append(truth)
            test_pred.append(pred)
            test_score.append(score)

    leaked_samples = sorted(sample for sample, splits in sample_splits.items() if len(splits) > 1)
    leaked_groups = sorted(group for group, splits in group_splits.items() if len(splits) > 1)
    if leaked_samples:
        errors.append(f"sample leakage across splits: {leaked_samples}")
    if leaked_groups:
        errors.append(f"group leakage across splits: {leaked_groups}")
    if not test_truth:
        errors.append("no test rows are present")

    test_counts = Counter(test_truth)
    if len(test_counts) < 2:
        errors.append("test split contains only one class")
    imbalance_ratio = (
        min(test_counts.values()) / max(test_counts.values()) if len(test_counts) == 2 else 0.0
    )
    if imbalance_ratio < 0.2:
        warnings.append(f"test class imbalance ratio is {imbalance_ratio:.3f}")

    accuracy = (
        sum(actual == predicted for actual, predicted in zip(test_truth, test_pred, strict=True))
        / len(test_truth)
        if test_truth
        else 0.0
    )
    majority_accuracy = max(test_counts.values()) / len(test_truth) if test_truth else 0.0
    brier = (
        sum((score - actual) ** 2 for score, actual in zip(test_score, test_truth, strict=True))
        / len(test_truth)
        if test_truth
        else 1.0
    )
    if brier > max_brier:
        errors.append(f"Brier score {brier:.4f} exceeds threshold {max_brier:.4f}")
    if require_beats_null and accuracy <= majority_accuracy:
        errors.append(
            f"test accuracy {accuracy:.4f} does not beat majority baseline {majority_accuracy:.4f}"
        )

    prevalence = {
        batch: sum(values) / len(values) for batch, values in batches.items() if values
    }
    prevalence_range = max(prevalence.values()) - min(prevalence.values()) if prevalence else 0.0
    if prevalence_range > max_batch_prevalence_range:
        errors.append(
            f"outcome prevalence range across {batch_column} is {prevalence_range:.4f}, "
            f"above {max_batch_prevalence_range:.4f}"
        )

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "rows": len(rows),
            "test_rows": len(test_truth),
            "test_class_0": test_counts.get(0, 0),
            "test_class_1": test_counts.get(1, 0),
        },
        "metrics": {
            "accuracy": round(accuracy, 6),
            "majority_null_accuracy": round(majority_accuracy, 6),
            "brier_score": round(brier, 6),
            "minority_to_majority_ratio": round(imbalance_ratio, 6),
            f"{batch_column}_outcome_prevalence_range": round(prevalence_range, 6),
        },
        "batch_prevalence": {key: round(value, 6) for key, value in sorted(prevalence.items())},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--batch-column", default="batch")
    parser.add_argument("--max-brier", type=float, default=0.25)
    parser.add_argument("--max-batch-prevalence-range", type=float, default=0.5)
    parser.add_argument("--require-beats-null", action="store_true")
    args = parser.parse_args(argv)
    if args.report.exists():
        print(f"ERROR: refusing to overwrite {args.report}", file=sys.stderr)
        return 1
    try:
        rows, columns = load_rows(args.predictions)
        if args.batch_column not in columns:
            raise ValueError(f"prediction table is missing confounder column {args.batch_column!r}")
        report = evaluate(
            rows,
            args.batch_column,
            args.max_brier,
            args.max_batch_prevalence_range,
            args.require_beats_null,
        )
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for error in report["errors"]:
        print(f"ERROR: {error}", file=sys.stderr)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
