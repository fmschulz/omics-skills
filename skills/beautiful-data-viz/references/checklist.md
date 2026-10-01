# Beautiful Data Viz Checklist

Run this pass before calling a chart, figure, or dashboard view done.

## 1) Integrity (never tell a lie)

- Chart choice matches the data structure; a sentence or table is used when it communicates better than a plot.
- Encodings match semantics (ordered data → ordered axis; categories → discrete encodings).
- Axes scales are appropriate (avoid deceptive truncation unless explicitly justified and clearly labeled).
- Uncertainty is represented when it matters (CI bands, error bars, quantiles).
- Aggregations are explicit (mean vs median; rolling window; binning).
- Comparison context is present when the claim depends on it (baseline, target, prior period, cohort, reference line, or companion series).

## 2) Readability (works at the size it will be seen)

- Tick labels are readable at the target embed size (no overlaps, no micro-font).
- Labels include **units** and use consistent numeric formatting (%, $, thousands separators).
- Long category names are wrapped, abbreviated, or switched to a horizontal layout (barh / dot plot).

## 3) Visual hierarchy (the viewer sees what matters first)

- One primary element (data marks) gets the most contrast.
- Secondary elements (grid, spines, annotations) are quieter.
- Manuscript/paper figures do not use in-plot titles or subtitles. The caption carries a short title that names what is shown, then states what is plotted: axes and units, what colours and symbols encode, and n. The finding goes in the Results text, not the caption.
- For notebooks or slides, titles and annotations explain the “so what” without duplicating axis labels.
- Prefer direct labels over legends; keep a legend only when direct labels would collide with the data or each other.

## 4) Data-ink and chart form

- Remove top and right spines, chart borders, shadows, gradient fills, and other non-data decoration.
- Gridlines are absent by default; if precision reading matters, use faint horizontal gridlines only.
- Avoid pie charts, 3D effects, decorative gauges, and dual y-axes. Use horizontal bars, flat 2D marks, text plus sparklines, or small multiples.
- Replace overloaded multi-series plots with small multiples that share scales across panels.
- Use slopegraphs for before/after comparisons and sparklines for compact trend context.

## 5) Layout and whitespace (tight but not cramped)

- Use `constrained_layout=True` or `fig.tight_layout()`; avoid accidental huge margins.
- Legends don’t create a dead column/row of whitespace.
- If labels/legend must be outside the axes, resize the figure to compensate (don’t just shrink the data area).
- Export with `bbox_inches="tight"` and small `pad_inches`.

## 6) Color and accessibility

- Marks are grey by default. Each color present encodes a category the reader must tell apart, the one highlighted finding, or an ordered or signed quantity; remove any other color.
- One accent marks the finding. Past three or four categorical colors, group the rest as grey "Other", facet, or use a table.
- Palette type matches data (qualitative / sequential / diverging); see [palettes.md](palettes.md).
- Color is never the only encoding: position, shape, line style, or a direct label carries the same information.
- Colors are colorblind-safe, and a greyscale copy of the figure (`Image.open(path).convert("L")`) still shows every distinction.
- Text and important marks have enough contrast for the target background.
- Static exports have useful alt text in the surrounding manuscript, notebook, or web page.
- Interactive charts do not hide essential values behind hover-only behavior; provide tap/focus alternatives or a companion table.

## 7) Responsive and interactive use

- At small widths, reduce tick density, abbreviate labels, or switch vertical bars to horizontal bars.
- Animation explains state change only; no decorative entrance animations. Respect reduced-motion settings when producing web figures.
- Dark-mode figures use an intentional palette; do not simply invert light-mode colors.
- Figures in one paper, deck, or dashboard share palette, typography, and line widths.
