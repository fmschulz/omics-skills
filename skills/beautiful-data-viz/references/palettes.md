# Choosing colors when color is warranted

Read this only after the greyscale-first rule in [../SKILL.md](../SKILL.md) says a figure needs color. Default marks stay grey. Color is warranted for three jobs:

| Job | Palette type | Example |
|-----|--------------|---------|
| A category the reader must tell apart | Qualitative (hue changes) | Three treatment arms in one panel |
| The one highlighted finding | One accent on grey context | The single significant gene among many |
| An ordered or signed quantity | Sequential (lightness changes) or diverging (two hues around a neutral midpoint) | Abundance heatmap; log2 fold change |

In every case the colors must be colorblind-safe, color must not be the only encoding, and the figure must stay readable in greyscale.

## 1) One accent

Most figures need only this. Keep all context in the grey cycle and give the finding one accent:

- Light background: Okabe-Ito vermillion `#D55E00`.
- Dark background: Okabe-Ito orange `#E69F00`.

`set_beautiful_style()` returns the matching value as `cfg.accent`. Pair the accent with a heavier line, a larger marker, or a direct label so the highlight survives greyscale print.

## 2) Categorical colors

- Color at most three or four categories in one panel. Past that, show the rest in grey as "Other", facet into small multiples, or use a table.
- Use a palette designed for color-vision deficiency:

```python
# Okabe-Ito (Okabe and Ito, "Color Universal Design"): https://jfly.uni-koeln.de/color/
OKABE_ITO = [
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#009E73",  # bluish green
    "#F0E442",  # yellow (weak on white; avoid for thin lines or text)
    "#0072B2",  # blue
    "#D55E00",  # vermillion
    "#CC79A7",  # reddish purple
    "#000000",  # black
]
```

- Library equivalents: seaborn `sns.color_palette("colorblind")`, Plotly `px.colors.qualitative.Safe`, ggplot2 `scale_colour_manual(values = okabe_ito)` or `scale_colour_viridis_d()`.
- Hue alone separates categories poorly in greyscale. Add markers, line styles, or direct labels.
- Keep one meaning per color across all figures in a paper or dashboard.

## 3) Sequential scales

For magnitude, use a perceptually uniform map whose lightness rises monotonically, so it also reads in greyscale: `viridis`, `cividis`, `mako`, `rocket`, or seaborn's `crest`. A single-hue grey ramp (`Greys`) is a valid default.

- matplotlib / seaborn: `cmap="viridis"` or `sns.color_palette("crest", as_cmap=True)`.
- Plotly: `px.colors.sequential.Viridis`. ggplot2: `scale_fill_viridis_c()`.
- For lines or points colored by value, avoid the end of the map that fades into the background.

## 4) Diverging scales

For data around a meaningful midpoint (0, baseline, target), use two hues with a neutral center and center the scale on the midpoint (`TwoSlopeNorm` in matplotlib, `zmid` in Plotly, `midpoint` in `scale_fill_gradient2`).

- Colorblind-safe choices: ColorBrewer `RdBu` or `PuOr`, seaborn `vlag`.
- Diverging maps lose their sign in greyscale (both ends turn dark), and a colorbar cannot restore it, because opposite values can print as the same grey. When the sign matters, attach a second encoding to the marks themselves: signed value labels (`+0.4`, `-0.4`), labeled contours, a marker shape per sign, or hatching on one side of the midpoint.

## References

- Seaborn palette tutorial: https://seaborn.pydata.org/tutorial/color_palettes.html
- Okabe-Ito colorblind-safe set: https://jfly.uni-koeln.de/color/
- Matplotlib colormap guidance: https://matplotlib.org/stable/users/explain/colors/colormaps.html
