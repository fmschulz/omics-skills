---
name: beautiful-data-viz
description: Shared design rules for every plot, figure, chart, dashboard or Dash app (matplotlib, seaborn, ggplot2, Plotly, HTML/SVG). Greyscale first, color only to encode information, colorblind-safe, publication-ready export. Use when making, restyling or reviewing any chart, figure or dashboard.
argument-hint: "[medium=notebook|paper|slides|web] [background=light|dark]"
---

# Beautiful Data Viz

The owner's standard for any data visual, whatever the library or medium. It overrides the palette of any built-in data-visualization skill of the harness: greyscale first, colour only to encode information. Show the data, remove decoration, label directly, and add only the context the reader needs. Other skills that draw figures (`/notebooks`, the `bio-*` reporting skills) follow these rules and add only what their medium needs.

## Instructions

1. **Greyscale first.** Draw every mark in neutral greys by default. Add colour only when it encodes information:
   - a category the reader must tell apart,
   - the one highlighted finding (one accent colour; everything else stays grey),
   - an ordered or signed quantity (sequential or diverging scale).

   Use colourblind-safe colours, never make colour the only encoding (add position, shape, line style or a direct label), and keep the figure readable in greyscale print. Pick colours from [references/palettes.md](references/palettes.md).
2. Clarify the message, comparison context, audience and medium (notebook, paper, slides, web). One or two values read better as a sentence; a short lookup list reads better as a table.
3. Choose the simplest chart that answers the question: horizontal bars or dot plots for ranked categories, small multiples instead of more than four overlaid series or a dual axis, slopegraphs for before/after, sparklines for compact trends.
4. Remove chart junk: no 3D, no pie charts unless asked for, no decorative borders, no heavy grids, no gradient fills, no dual y-axes, no top/right spines.
5. Label series directly. Keep a legend only when direct labels would collide.
6. Manuscript figures carry no in-plot title or subtitle; axis labels (with units), direct labels, panel letters and the caption do that work. The caption sits below the figure: in a notebook the figure cell comes first and the caption cell follows it.
7. Apply the style for the medium:
   - matplotlib or seaborn: `cfg = set_beautiful_style(medium="paper")` from [assets/beautiful_style.py](assets/beautiful_style.py), imported with the skill directory on `sys.path` (setup in [examples/recipes.md](examples/recipes.md)); the module is the single source of the palette, rcParams and dpi (150 on screen, 300 on export). It sets a grey series cycle with distinct line styles; `cfg.accent` is the highlight colour for the current background. Helpers: `direct_label`, `annotate_point`, `apply_range_frame`, `sparkline`, `finalize_axes`.
   - R / ggplot2: `theme_classic()` or `theme_minimal()`, `scale_colour_grey()` for neutral series, `scale_colour_manual()` to give only the finding the accent.
   - Plotly or Dash: a registered template with a grey `colorway` and the accent added per trace; structure, template and smoke test in [references/dash.md](references/dash.md).
   - HTML / SVG: define neutral greys and one accent as CSS custom properties and redefine them for dark mode.
8. Check the result at the target size with [references/checklist.md](references/checklist.md), and view a greyscale copy to confirm every encoding survives (`Image.open(path).convert("L")` with Pillow).
9. Reproduce figures from a pinned environment: the project's `pixi.toml` (this skill ships one) or a PEP 723 script run with `uv run --script`, as in [scripts/export_fixture.py](scripts/export_fixture.py). Duplicate figures in an executed Jupyter notebook: see the `/notebooks` troubleshooting section.

## Input Requirements

Tabular data, the message the figure must carry, and the target medium, size and background.

## Output

Figures as PNG, SVG or PDF (or an HTML/SVG visual) and the plotting code that reproduces them.

## Quality Gates

- The message is clear within a few seconds at the target size, and a sentence or table would not do better.
- The greyscale copy stays readable; colour is never the only encoding.
- From the skill directory, `uv run --script scripts/export_fixture.py fixtures/growth_curve.csv --out build/fixture` ([script](scripts/export_fixture.py), [fixture](fixtures/growth_curve.csv)) writes non-empty PNG, SVG and PDF files with grey default series; with `--background dark`, labels inherit the dark-theme text colour.
