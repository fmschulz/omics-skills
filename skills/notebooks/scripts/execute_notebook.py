#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "nbclient>=0.10,<1",
#     "nbformat>=5.10,<6",
# ]
# ///

"""Execute a Jupyter notebook top to bottom on a fresh kernel and save a copy.

Why this exists:
- Human "it ran on my machine" is not enough.
- This creates a deterministic validation gate in CI or local checks.

Without --kernel the notebook's own kernelspec runs, else python3. A given --kernel is
written into the executed notebook's kernelspec.

Usage:
  uv run --script ~/.agents/skills/notebooks/scripts/execute_notebook.py \
    notebooks/01_analysis.ipynb --out notebooks/01_analysis.executed.ipynb
"""
from __future__ import annotations

import argparse
from pathlib import Path

import nbformat
from nbclient import NotebookClient


DEFAULT_KERNEL = "python3"


def resolve_kernel_name(
    notebook_kernel_name: str | None, kernel_flag: str | None
) -> str:
    """Pick the kernel: the --kernel flag, else the notebook's own, else python3."""
    return kernel_flag or notebook_kernel_name or DEFAULT_KERNEL


def execute_notebook(
    notebook_path: Path,
    out_path: Path,
    *,
    kernel_name: str | None = None,
    timeout_s: int = 600,
) -> None:
    nb = nbformat.read(str(notebook_path), as_version=4)

    # A given kernel replaces the notebook's own, so the executed file records it.
    kernelspec = nb.metadata.setdefault("kernelspec", {})
    kernel_name = resolve_kernel_name(kernelspec.get("name"), kernel_name)
    kernelspec["name"] = kernel_name
    kernelspec.setdefault("display_name", kernel_name)

    # Execute in the notebook's directory so relative paths behave as expected.
    resources = {"metadata": {"path": str(notebook_path.parent)}}

    client = NotebookClient(
        nb,
        timeout=timeout_s,
        kernel_name=kernel_name,
        resources=resources,
    )

    # Execute all cells; exceptions raise CellExecutionError by default.
    client.execute()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, str(out_path))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("notebook", type=Path, help="Path to .ipynb notebook")
    ap.add_argument("--out", type=Path, default=None, help="Output executed notebook path")
    ap.add_argument(
        "--kernel",
        type=str,
        default=None,
        help=(
            "Kernel name, written into the executed notebook "
            "(default: the notebook's own kernelspec, else python3)"
        ),
    )
    ap.add_argument("--timeout", type=int, default=600, help="Cell timeout in seconds (default: 600)")
    args = ap.parse_args()

    nb_path: Path = args.notebook
    if not nb_path.exists():
        raise SystemExit(f"Notebook not found: {nb_path}")

    out_path = args.out or nb_path.with_suffix(".executed.ipynb")

    execute_notebook(
        nb_path,
        out_path,
        kernel_name=args.kernel,
        timeout_s=args.timeout,
    )
    print(f"Executed notebook written to: {out_path}")


if __name__ == "__main__":
    main()
