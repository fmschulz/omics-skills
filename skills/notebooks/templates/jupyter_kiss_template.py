# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#   kernelspec:
#     display_name: Pixi - <PROJECT_NAME>
#     language: python
#     name: <PIXI_PROJECT_KERNEL>
# ---

# %% [markdown]
# # <NOTEBOOK TITLE>
#
# **Purpose (3 lines max):**
# - What question does this notebook answer?
# - What decision or artifact does it support?
# - What is “done” for this notebook?
#
# **Outputs produced:**
# - Table(s): <describe>
# - Figure(s): <describe>
# - File(s): <describe path(s) if exported>

# %% [markdown]
# ## Reproducibility
# - Kernel/environment is defined by `pixi.toml` in this directory (Pixi + pixi-kernel).
# - To re-run: **Restart Kernel & Run All**.
# - Any randomness is seeded below.

# %%
from __future__ import annotations

from pathlib import Path
import random

import numpy as np
import pandas as pd
from IPython.display import display

# Optional: DuckDB for SQL analytics
import duckdb

# Plotting
import matplotlib.pyplot as plt

# %% [markdown]
# ## Configuration
# - Resolve `PROJECT_ROOT` from the nearest `pixi.toml` / `pyproject.toml` / `.git`.
# - Define `DATA_DIR` and `OUT_DIR`.
# - Set random seeds.

# %%
def find_project_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()
    markers = {"pixi.toml", "pyproject.toml", ".git"}
    for p in [start, *start.parents]:
        if any((p / m).exists() for m in markers):
            return p
    return start

PROJECT_ROOT = find_project_root()
DATA_DIR = PROJECT_ROOT / "data"
OUT_DIR = PROJECT_ROOT / "outputs"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 7
random.seed(SEED)
np.random.seed(SEED)

print("PROJECT_ROOT:", PROJECT_ROOT)
print("DATA_DIR:", DATA_DIR)
print("OUT_DIR:", OUT_DIR)

# %% [markdown]
# ## Plot styling
# - `beautiful_style.py` is the single source of the palette, rcParams and dpi
#   (150 on screen, 300 on export). Copy `assets/beautiful_style.py` from the
#   beautiful-data-viz skill next to this notebook.
# - Series are grey; use `cfg.accent` only for the one highlighted finding.

# %%
from beautiful_style import set_beautiful_style

cfg = set_beautiful_style(medium="notebook")

# %% [markdown]
# ## Data
# Describe your data sources:
# - Files: `data/raw/...` (TSV/CSV/Parquet)
# - Database: `data/analytics.duckdb` (or in-memory)
#
# Document:
# - refresh cadence
# - key columns
# - expected row counts / ranges

# %% [markdown]
# ## Load data
# - Load raw files using paths anchored to `DATA_DIR`.
# - Fail fast: a missing file raises `FileNotFoundError`.
# - Show a compact preview and shape.

# %%
# Example TSV (replace with your actual file); read_csv raises if it is missing.
raw_path = DATA_DIR / "raw" / "events.tsv"
events = pd.read_csv(raw_path, sep="\t")
display(events.head())
print("events shape:", events.shape)

# %% [markdown]
# ## DuckDB bootstrap (optional)
# - Connect to a file-backed DuckDB (recommended for repeatability) or use `:memory:`.
# - Use absolute paths when passing file paths into DuckDB.

# %%
db_path = DATA_DIR / "analytics.duckdb"
con = duckdb.connect(str(db_path))
con.execute("SELECT 1 AS ok").df()

# %% [markdown]
# ## Validate data
# - Check missingness and key uniqueness.
# - Confirm assumptions before analysis.

# %%
def null_rate(df: pd.DataFrame) -> pd.Series:
    return df.isna().mean().sort_values(ascending=False)

display(null_rate(events).head(10))

# %% [markdown]
# ## Analysis
# - Keep steps small and linear.
# - Each code cell should do one thing.

# %%
# TODO: analysis code here

# %% [markdown]
# ## Results
# - Present final tables/figures.
# - Export any artifacts to `OUT_DIR`.

# %%
# Example placeholder plot
fig, ax = plt.subplots(figsize=(7.5, 4.0))
events.iloc[:, 0].value_counts().head(20).plot(kind="bar", ax=ax)
ax.set_xlabel(events.columns[0])
ax.set_ylabel("count (rows)")
fig.savefig(OUT_DIR / "top_values.png")

# %% [markdown]
# ## Conclusions & next steps
# - Summarize what you found (3–6 bullets).
# - List concrete next actions.
