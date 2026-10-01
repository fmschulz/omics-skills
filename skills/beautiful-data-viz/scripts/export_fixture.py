#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib==3.11.0"]
# ///
"""Export the bundled growth-curve fixture to PNG, SVG, and PDF."""

import argparse
import csv
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL))
from assets.beautiful_style import direct_label, finalize_axes, set_beautiful_style  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path)
    parser.add_argument("--out", type=Path, required=True, help="Output path without suffix")
    parser.add_argument("--background", choices=("light", "dark"), default="light")
    args = parser.parse_args()
    with args.data.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        parser.error("fixture has no rows")
    columns = list(rows[0])
    x = [float(row[columns[0]]) for row in rows]
    set_beautiful_style(medium="paper", background=args.background)
    fig, ax = plt.subplots(figsize=(4.2, 2.8))
    for column in columns[1:]:
        y = [float(row[column]) for row in rows]
        ax.plot(x, y)
        direct_label(ax, x, y, column)
    finalize_axes(ax, xlabel=columns[0], ylabel="growth")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "svg", "pdf"):
        fig.savefig(args.out.with_suffix(f".{suffix}"), facecolor=fig.get_facecolor())
    metadata = {
        "text_color": plt.rcParams["text.color"],
        "annotation_colors": [text.get_color() for text in ax.texts],
        "line_colors": [line.get_color() for line in ax.lines],
    }
    args.out.with_suffix(".json").write_text(json.dumps(metadata, indent=2) + "\n")
    plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
