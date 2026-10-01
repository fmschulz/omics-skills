# Plot recipes

Patterns to adapt to the dataset. Each one keeps context grey and spends color only where the rules in [../SKILL.md](../SKILL.md) allow it. All recipes start with the same setup:

```python
from pathlib import Path
import sys

import matplotlib.pyplot as plt

SKILL_DIR = Path.home() / ".agents" / "skills" / "beautiful-data-viz"
sys.path.insert(0, str(SKILL_DIR))
from assets.beautiful_style import direct_label, finalize_axes, set_beautiful_style

cfg = set_beautiful_style(medium="notebook", background="light")
```

## Time series: grey context, one highlighted series

```python
import matplotlib.dates as mdates

# df has columns: date, value, series; `focus` names the series that carries the finding
fig, ax = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
for name, g in df.sort_values("date").groupby("series"):
    is_focus = name == focus
    color = cfg.accent if is_focus else "#a8a8a8"
    ax.plot(g["date"], g["value"], color=color, linewidth=2 if is_focus else 1, linestyle="-")
    direct_label(ax, g["date"], g["value"], name, color=color if is_focus else None)

locator = mdates.AutoDateLocator()
ax.xaxis.set_major_locator(locator)
ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
finalize_axes(ax, xlabel=None, ylabel="Value (units)", tight=False)
```

The accent appears twice (line and label), and the focus line is also thicker, so the highlight survives greyscale print.

## Ranked dot plot

```python
# df has columns: category, value
df_sorted = df.sort_values("value")

fig, ax = plt.subplots(figsize=(7, 5), constrained_layout=True)
ax.hlines(y=df_sorted["category"], xmin=0, xmax=df_sorted["value"], color="#cccccc", linewidth=1)
ax.plot(df_sorted["value"], df_sorted["category"], "o", color="#333333")

finalize_axes(ax, xlabel="Value (units)", ylabel=None, tight=False)
```

To highlight one category, re-plot its marker with `color=cfg.accent` and a larger `markersize`.

## Heatmap of an ordered quantity

```python
import seaborn as sns

fig, ax = plt.subplots(figsize=(7, 5), constrained_layout=True)
sns.heatmap(matrix, cmap="viridis", ax=ax, cbar_kws={"shrink": 0.8, "label": "Abundance (log10 CPM)"})
finalize_axes(ax, tight=False)
```

Here color encodes magnitude, so a sequential map with monotonic lightness is the right choice. For signed values (fold change), use a diverging map centered on zero; see [../references/palettes.md](../references/palettes.md).
