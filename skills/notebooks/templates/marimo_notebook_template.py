# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo>=0.23",
#     "matplotlib>=3.9",
#     "numpy>=2.1",
#     "pandas>=2.2",
# ]
# ///

import marimo

__generated_with = "0.23.1"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Notebook Title

    **Purpose:** State the question this notebook answers.

    **Outputs:** List the tables, figures, or files this notebook produces.

    **Setup:** Copy `assets/beautiful_style.py` from the beautiful-data-viz skill
    next to this notebook. It is the single source of the plot palette, rcParams
    and dpi (150 on screen, 300 on export).
    """)
    return


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from beautiful_style import set_beautiful_style

    return Path, mo, np, pd, plt, set_beautiful_style


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Configuration

    Resolve project-relative paths, create the output directory and apply the
    shared plot style.
    """)
    return


@app.cell
def _(Path, set_beautiful_style):
    PROJECT_ROOT = Path.cwd()
    DATA_DIR = PROJECT_ROOT / "data"
    OUTPUT_DIR = PROJECT_ROOT / "outputs"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    set_beautiful_style(medium="notebook")
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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Plot `y` against `x`. Expect one grey line with markers; the axis labels carry
    the units.
    """)
    return


@app.cell
def _(OUTPUT_DIR, example, plt):
    _fig, _ax = plt.subplots(figsize=(5.5, 3.2))
    _ax.plot(example["x"], example["y"], marker="o")
    _ax.set_xlabel("x (arbitrary units)")
    _ax.set_ylabel("y (arbitrary units)")
    _fig.savefig(OUTPUT_DIR / "example_figure.png")
    _fig  # noqa: B018 - marimo renders the final expression
    return  # noqa: PLR1711 - marimo cells end with an explicit return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Figure 1.** Example values of `y` against `x`. Replace this caption with what
    the figure shows.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Figure revision log

    - Initial rendered figure inspected after a fresh-kernel export.
    """)
    return


if __name__ == "__main__":
    app.run()
