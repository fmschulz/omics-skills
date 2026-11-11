#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["marimo==0.23.13", "nbformat==5.10.4"]
# ///
"""Convert between marimo Python notebooks and Jupyter ipynb files."""

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--to", choices=("jupyter", "marimo"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not args.input.is_file() or args.input.stat().st_size == 0:
        parser.error(f"input is missing or empty: {args.input}")
    expected = ".ipynb" if args.to == "jupyter" else ".py"
    if args.out.suffix != expected:
        parser.error(f"--to {args.to} requires an {expected} output")
    if args.to == "marimo":
        command = [sys.executable, "-m", "marimo", "convert", str(args.input), "-o", str(args.out)]
    else:
        command = [sys.executable, "-m", "marimo", "export", "ipynb", str(args.input), "-o", str(args.out), "-f"]
    result = subprocess.run(command, check=False)
    if result.returncode or not args.out.is_file() or args.out.stat().st_size == 0:
        return result.returncode or 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
