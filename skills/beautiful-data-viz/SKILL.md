---
name: beautiful-data-viz
description: Create publication-quality matplotlib/seaborn charts with readable axes, tight layout, curated palettes, and Tufte-style high-data-ink design.
argument-hint: "[medium=notebook|paper|slides] [background=light|dark]"
---

# Beautiful Data Viz

Create polished, publication-ready visualizations in Python/Jupyter with strong typography, clean layout, accessible color choices, and high data-ink. The default style is restrained: show the data, remove non-data decoration, label directly when possible, and add only the context needed to interpret the finding.

## Instructions

1. Clarify the message, comparison context, audience, and medium (notebook/paper/slides). If the data is one or two values, prefer a sentence; if it is a short lookup list, prefer a table.
2. Choose the simplest chart type that answers the question. Prefer horizontal bars for ranked categories, small multiples for >4 series or dual-axis temptations, slopegraphs for before/after changes, and sparklines for compact trend context.
3. Start gray-first: neutral series by default, one accent for the finding, and no rainbow palettes. Select an appropriate palette type only when color is carrying real information.
4. Remove chart junk before styling: no 3D, pie charts only if explicitly requested, no decorative borders, no heavy grids, no gradient fills, no dual y-axes.
5. Use direct labels instead of legends when series count and space allow. Keep legends only when direct labels would collide or obscure data.
6. For manuscript/paper figures, do not add in-plot titles or subtitles; use axis labels, legends/direct labels, panel letters, and the manuscript caption instead.
7. Place the figure caption/legend text BELOW the figure, directly under it — never above. In a notebook this means the figure (code) cell comes first and the caption (markdown) cell immediately follows it; in a document the caption goes beneath the image. A reader sees the figure, then its legend. (Journal convention: legends sit below the figure.)
8. Apply the shared style helpers, then build the plot.
9. Validate readability, accessibility, and export quality at the target size.

## Quick Reference

| Task | Action |
|------|--------|
| Apply style | Use `assets/beautiful_style.py` helpers |
| Pick palette | See `references/palettes.md` |
| QA checklist | See `references/checklist.md` |
| Plot recipes | See `examples/recipes.md` |
| Tufte finish | Use `direct_label`, `annotate_point`, `apply_range_frame`, or `sparkline` from `assets/beautiful_style.py` |

## Input Requirements

- Data in a tabular form (pandas DataFrame or similar)
- Clear statement of the primary message
- Target medium and background preference

## Output

- Publication-ready figure(s) (PNG/SVG/PDF)
- Consistent styling and labeling

## Quality Gates

- [ ] Message is clear in 3 seconds at target size
- [ ] Chart earns its space; a sentence or table would not communicate the pattern better
- [ ] Manuscript/paper figures have no plot title; the caption carries the title/interpretation
- [ ] The caption/legend is placed BELOW the figure (in a notebook: figure cell first, caption markdown cell directly after), never above it
- [ ] Non-data ink is minimized: no top/right spines, no decorative borders, no 3D, no heavy grid
- [ ] Direct labels replace legends when feasible
- [ ] Comparison context is present when interpretation depends on it
- [ ] Labels and units are readable and accurate
- [ ] Color choice is colorblind-safe and grayscale-tolerant
- [ ] Color is not the only encoding for important categories
- [ ] Layout is tight with minimal whitespace

## Examples

### Example 1: Apply the shared style helper

```python
from assets.beautiful_style import set_beautiful_style, finalize_axes
set_beautiful_style(medium="paper", background="light")
# build plot here
finalize_axes(ax, xlabel="Time (days)", ylabel="Value", tight=True)
```

### Example 2: Direct labels and range-frame axes

```python
from assets.beautiful_style import apply_range_frame, direct_label

ax.plot(x, y, color="#666666", linewidth=1.5)
apply_range_frame(ax, x, y)
direct_label(ax, x, y, "Observed", color="#666666")
```

## Troubleshooting

**Issue**: Labels overlap or are unreadable
**Solution**: Reduce tick count, rotate labels, or increase figure width.

**Issue**: Colors are hard to distinguish
**Solution**: Use a colorblind-safe categorical palette and limit categories.

**Issue**: A chart needs a legend, many colors, and a second y-axis to fit
**Solution**: Split it into small multiples with shared scales and direct labels.

**Issue**: Every figure appears twice in the executed Jupyter notebook
**Solution**: The matplotlib inline backend's `flush_figures` post-execute hook auto-displays every open figure as `display_data`, and the cell's `fig` return value produces a second copy as `execute_result`. Fix by unregistering the hook in the preamble cell:
```python
plt.ioff()
try:
    from matplotlib_inline.backend_inline import flush_figures
    get_ipython().events.unregister("post_execute", flush_figures)
except Exception:
    pass
```
With this fix, only the cell's final `fig` expression produces output. For figures created inside `if/else` blocks (where `fig` is not a top-level expression), use `display(fig)` explicitly instead of bare `fig`.
