---
name: beautiful-data-viz
description: Shared design rules for every plot, figure, chart, dashboard or data visual (matplotlib, seaborn, ggplot2, Plotly, HTML/SVG). Greyscale first, color only to encode information, colorblind-safe, publication-ready export. Use when making, restyling or reviewing any chart or figure.
argument-hint: "[medium=notebook|paper|slides|web] [background=light|dark]"
---

# Beautiful Data Viz

The pack's shared rules for any data visual, whatever the library or medium. Show the data, remove decoration, label directly, and add only the context the reader needs. Other skills that draw figures (`/plotly-dashboard-skill`, `/notebooks`, the `bio-*` reporting skills) follow these rules and add only what their medium needs.

## Instructions

1. **Greyscale first.** Draw every mark in neutral greys by default. Add color only when it encodes information:
   - a category the reader must tell apart,
   - the one highlighted finding (one accent color; everything else stays grey),
   - an ordered or signed quantity (sequential or diverging scale).

   Use colorblind-safe colors, never make color the only encoding (add position, shape, line style, or a direct label), and keep the figure readable in greyscale print. When color is warranted, pick it from [references/palettes.md](references/palettes.md).
2. Clarify the message, comparison context, audience, and medium (notebook, paper, slides, web). One or two values read better as a sentence; a short lookup list reads better as a table.
3. Choose the simplest chart that answers the question: horizontal bars or dot plots for ranked categories, small multiples instead of more than four overlaid series or a dual axis, slopegraphs for before/after, sparklines for compact trends.
4. Remove chart junk: no 3D, no pie charts unless asked for, no decorative borders, no heavy grids, no gradient fills, no dual y-axes.
5. Label series directly. Keep a legend only when direct labels would collide with the data or each other.
6. Manuscript figures carry no in-plot title or subtitle; axis labels, direct labels, panel letters, and the caption do that work. The caption sits below the figure: in a notebook the figure cell comes first and the caption cell follows it.
7. Apply the style for the medium:
   - matplotlib or seaborn: `set_beautiful_style(...)` from [assets/beautiful_style.py](assets/beautiful_style.py). It sets a grey series cycle with distinct line styles and returns a config whose `accent` is a colorblind-safe highlight color for the current background.
   - R / ggplot2: `theme_classic()` or `theme_minimal()`, `scale_colour_grey()` for neutral series, and `scale_colour_manual()` to give only the finding the accent.
   - Plotly or Dash: a registered template with a grey `colorway` and the accent added per trace; see `/plotly-dashboard-skill` [references/style.md](../plotly-dashboard-skill/references/style.md).
   - HTML / SVG: define neutral greys and one accent as CSS custom properties and redefine them for dark mode.
8. Check the result at the target size: run the [references/checklist.md](references/checklist.md) pass, and view a greyscale copy to confirm every encoding survives (`Image.open(path).convert("L")` with Pillow).
9. Reproduce figures from a pinned environment: the project's `pixi.toml` (this skill ships one in [pixi.toml](pixi.toml)), or a PEP 723 script run with `uv run --script`, as in [scripts/export_fixture.py](scripts/export_fixture.py).

## Quick Reference

| Task | Action |
|------|--------|
| Apply matplotlib style | `cfg = set_beautiful_style(medium="paper")` from `assets/beautiful_style.py` |
| Highlight the finding | `ax.plot(x, y, color=cfg.accent)`; all other series keep the grey cycle |
| Direct label, range frame, sparkline | `direct_label`, `annotate_point`, `apply_range_frame`, `sparkline` |
| Choose colors when warranted | [references/palettes.md](references/palettes.md) |
| Final QA pass | [references/checklist.md](references/checklist.md) |
| Copyable plot patterns | [examples/recipes.md](examples/recipes.md) |
| Duplicate figures in an executed Jupyter notebook | See the `/notebooks` troubleshooting section |

## Input Requirements

- Data in tabular form (pandas or polars DataFrame, R data frame, or similar).
- The primary message the figure must carry.
- Target medium, size, and background.

## Output

- Figures exported as PNG, SVG, or PDF (or an HTML/SVG visual) with consistent styling and labeling.
- The plotting code that reproduces them from a pinned environment.

## Quality Gates

- [ ] The message is clear within a few seconds at the target size, and a sentence or table would not do better.
- [ ] Marks are grey unless color encodes a category, the one finding, or an ordered or signed quantity.
- [ ] Colors are colorblind-safe, color is never the only encoding, and the greyscale copy stays readable.
- [ ] Manuscript figures have no in-plot title; the caption sits below the figure.
- [ ] No top/right spines, decorative borders, 3D, or heavy grid; direct labels replace legends where they fit.
- [ ] Labels carry units, and comparison context is present when the claim depends on it.
- [ ] `uv run --script skills/beautiful-data-viz/scripts/export_fixture.py skills/beautiful-data-viz/fixtures/growth_curve.csv --out build/fixture` writes non-empty PNG, SVG, and PDF files with grey default series; with `--background dark`, labels inherit the dark-theme text color.

## Examples

### Example 1: Grey series with one highlighted finding

```python
from pathlib import Path
import sys

import matplotlib.pyplot as plt

SKILL_DIR = Path.home() / ".agents" / "skills" / "beautiful-data-viz"
sys.path.insert(0, str(SKILL_DIR))
from assets.beautiful_style import direct_label, finalize_axes, set_beautiful_style

cfg = set_beautiful_style(medium="paper", background="light")
fig, ax = plt.subplots(figsize=(4.2, 2.8))
for name, y in reference_series.items():  # context: default grey cycle
    ax.plot(x, y, linewidth=1)
    direct_label(ax, x, y, name)
ax.plot(x, treated, color=cfg.accent, linewidth=2)  # the finding
direct_label(ax, x, treated, "Treated", color=cfg.accent)
finalize_axes(ax, xlabel="Time (days)", ylabel="Biomass (g/L)")
fig.savefig("growth.pdf")
```

## Troubleshooting

**Issue**: Labels overlap or are unreadable.
**Solution**: Reduce tick count, wrap or abbreviate labels, switch to horizontal bars, or widen the figure.

**Issue**: Categories are hard to tell apart.
**Solution**: Reduce the number of colored categories (group the rest in grey as "Other"), add markers or line styles, or split into small multiples.

**Issue**: A chart needs a legend, many colors, and a second y-axis to fit.
**Solution**: Split it into small multiples with shared scales and direct labels.
