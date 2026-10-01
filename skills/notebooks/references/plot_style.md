# Plot style in notebooks

Figures in notebooks follow `/beautiful-data-viz` ([../../beautiful-data-viz/SKILL.md](../../beautiful-data-viz/SKILL.md)): greyscale first, color only to encode a category the reader must tell apart, the one highlighted finding, or an ordered or signed quantity; colorblind-safe; never color as the only encoding; direct labels over legends; no in-plot titles on manuscript figures. This file covers only what is specific to notebooks.

## Style cell

Put one styling cell near the top and reuse its result in every plot cell. With the skill installed, use its helper:

```python
from pathlib import Path
import sys

sys.path.insert(0, str(Path.home() / ".agents" / "skills" / "beautiful-data-viz"))
from assets.beautiful_style import set_beautiful_style

cfg = set_beautiful_style(medium="notebook", background="light")
# cfg.accent is the one highlight color; all other series use the grey cycle.
```

A marimo `--sandbox` notebook or a teammate's clean clone may not have the skill installed. Then inline the same defaults instead of importing them:

```python
import matplotlib as mpl
from cycler import cycler

ACCENT = "#D55E00"  # Okabe-Ito vermillion: the one highlighted finding
mpl.rcParams.update({
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "Liberation Sans"],
    "figure.facecolor": "#ffffff",
    "axes.facecolor": "#ffffff",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": False,
    "axes.prop_cycle": cycler(color=["#333333", "#7a7a7a", "#a8a8a8", "#555555"])
    + cycler(linestyle=["-", "--", ":", "-."]),
    "legend.frameon": False,
    "figure.constrained_layout.use": True,
})
```

## Notebook-specific rules

- Build a fresh figure with `plt.subplots(...)` in each plot cell and make the figure the cell's final expression, so marimo and the executed `.ipynb` both embed it.
- In marimo, name the figure and axes `_fig, _ax` (or give each cell unique names). Marimo rejects a global such as `fig` defined in two cells, and the underscore makes the names private to the cell.
- Caption order: the figure cell comes first and its caption markdown cell follows directly below.
- Exploratory or slide figures may carry a short title; manuscript figures do not.
- Save exported figures from the same cell that draws them: `_fig.savefig(OUT_DIR / "figure.pdf")`.
- Duplicate figures in executed Jupyter notebooks: see the troubleshooting section of [../SKILL.md](../SKILL.md).
