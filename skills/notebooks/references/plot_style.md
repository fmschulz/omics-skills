# Plot style in notebooks

Figures in notebooks follow `/beautiful-data-viz` ([../../beautiful-data-viz/SKILL.md](../../beautiful-data-viz/SKILL.md)): greyscale first, color only to encode a category the reader must tell apart, the one highlighted finding, or an ordered or signed quantity; colorblind-safe; never color as the only encoding; direct labels over legends; no in-plot titles on manuscript figures. This file covers only what is specific to notebooks.

## Style cell

[../../beautiful-data-viz/assets/beautiful_style.py](../../beautiful-data-viz/assets/beautiful_style.py) is the single source of the palette, rcParams and dpi: 150 dpi on screen, 300 dpi on export. Do not copy its values into a notebook. Copy the file next to the notebook (it needs only matplotlib and cycler; seaborn is optional), then put one styling cell near the top and reuse its result in every plot cell:

```python
from beautiful_style import set_beautiful_style

cfg = set_beautiful_style(medium="notebook", background="light")
# cfg.accent is the one highlight color; all other series use the grey cycle.
```

Both notebook templates start from this cell. The base font sizes are 9, 11 and 14 pt for `medium="paper"`, `"notebook"` and `"slides"`.

## Notebook-specific rules

- Build a fresh figure with `plt.subplots(...)` in each plot cell and make the figure the cell's final expression, so marimo and the executed `.ipynb` both embed it.
- In marimo, name the figure and axes `_fig, _ax` (or give each cell unique names). Marimo rejects a global such as `fig` defined in two cells, and the underscore makes the names private to the cell.
- Caption order: the figure cell comes first and its caption markdown cell follows directly below.
- Exploratory or slide figures may carry a short title; manuscript figures do not.
- Save exported figures from the same cell that draws them: `_fig.savefig(OUT_DIR / "figure.pdf")`.
- Duplicate figures in executed Jupyter notebooks: see the troubleshooting section of [../SKILL.md](../SKILL.md).
