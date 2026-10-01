# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "matplotlib",
#     "numpy",
#     "pandas",
# ]
# ///

import marimo

__generated_with = "0.23.1"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    return Path, mo, np, pd, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Notebook Title

    **Purpose:** State the question this notebook answers.

    **Outputs:** List the tables, figures, or files this notebook produces.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Configuration

    Resolve project-relative paths and create the output directory.
    """)
    return


@app.cell
def _(Path):
    PROJECT_ROOT = Path.cwd()
    DATA_DIR = PROJECT_ROOT / "data"
    OUTPUT_DIR = PROJECT_ROOT / "outputs"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR, OUTPUT_DIR, PROJECT_ROOT


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Results

    Replace this placeholder with the analysis and figures requested by the user.
    """)
    return


@app.cell
def _(np, pd):
    example = pd.DataFrame(
        {
            "x": np.arange(5),
            "y": np.array([1, 3, 2, 5, 4]),
        }
    )
    example
    return (example,)


@app.cell
def _(OUTPUT_DIR, example, plt):
    _fig, _ax = plt.subplots(figsize=(5.5, 3.2))
    _ax.plot(example["x"], example["y"], marker="o", color="#333333")
    _ax.set_xlabel("x")
    _ax.set_ylabel("y")
    _ax.set_title("Example Figure")
    _fig.tight_layout()
    _fig.savefig(OUTPUT_DIR / "example_figure.png", dpi=200)
    _fig  # noqa: B018 - marimo renders the final expression
    return  # noqa: PLR1711 - marimo cells end with an explicit return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Figure revision log

    - Initial rendered figure inspected after a fresh-kernel export.
    """)
    return


if __name__ == "__main__":
    app.run()
