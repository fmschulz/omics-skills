# Dashboard and Figure Style

Last verified: 2026-09-05
Tool version/release checked: Dash 4.4.0, Plotly 6.5.0
Official docs/manual: https://dash.plotly.com/ and https://plotly.com/python/templates/
Release/source: https://github.com/plotly/dash/releases

Readability, hierarchy, and consistency: the things that make a dashboard feel designed. One template and one palette definition drive every chart, so nothing is styled twice.

## Layout

Pick one structure and keep it across pages:

- Header, filters, content grid, footer
- Left rail filters, content grid
- Overview page with drilldown pages

Use an 8px spacing scale (4, 8, 12, 16, 24, 32, 48). Typical values: page padding 24, card padding 16, card gap 16, section spacing 24-32.

Group content into cards. Each card carries a short title, an optional subtitle ("last 30 days", "vs previous period"), one primary chart or KPI, and an optional footnote for a data caveat or source.

## Typography

One font family for UI, headings, and charts. Safe default:

```
Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif
```

Web sizes: page title 24-28, section title 16-18 bold, body 13-14, small labels 12. Sentence case everywhere except tiny labels.

## Color

Neutrals carry structure (background, borders, text). Color appears only when it encodes meaning or directs attention. Reserve green for good or increase, red for bad or decrease, gray for neutral or no data, and keep that meaning constant across the dashboard.

Categorical palettes must be visually equidistant: avoid four near-identical blues. Aim for 6-8 distinct categorical colors in one view. Past 8 categories, switch to top-N plus "Other", small multiples, or a table.

Never encode meaning by color alone. Add labels, shapes, or ordering, keep text contrast sufficient, and avoid red/green as the only distinguishing pair.

### Palettes

```python
# Vibrant, high contrast. Source: ColorsWall "Flat UI Colors Codes".
FLAT_UI_CLASSIC = [
    "#1abc9c",  # Turquoise
    "#2ecc71",  # Emerald
    "#3498db",  # Peter River
    "#9b59b6",  # Amethyst
    "#34495e",  # Wet Asphalt
    "#16a085",  # Green Sea
    "#27ae60",  # Nephritis
    "#2980b9",  # Belize Hole
    "#8e44ad",  # Wisteria
    "#2c3e50",  # Midnight Blue
    "#f1c40f",  # Sunflower
    "#e67e22",  # Carrot
    "#e74c3c",  # Alizarin
    "#95a5a6",  # Concrete
    "#7f8c8d",  # Asbestos
]

# Muted and modern. Source: Color-Hex palette "Learnui Design".
LEARNUI_DESIGN = ["#003f5c", "#7a5195", "#ef5675", "#ffa600", "#aaaaaa"]

# Template default: six hues from FLAT_UI_CLASSIC picked for maximum separation.
DASH_COLORWAY = ["#3498db", "#2ecc71", "#e67e22", "#9b59b6", "#e74c3c", "#1abc9c"]
```

Plotly Express also ships qualitative palettes under `px.colors.qualitative`. Prefer a built-in over shipping custom hex codes when either would do.

Pick the palette type from the data: categorical for categories, sequential single-hue for magnitude, diverging two-hue for negative to positive.

## Figure template

Register one template so every chart inherits the same look, rather than styling figures one at a time.

```python
import plotly.io as pio
import plotly.graph_objects as go

dash_template = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif", size=13),
        title=dict(font=dict(size=16)),
        colorway=DASH_COLORWAY,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=48, r=20, t=56, b=44),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title_text=""),
        xaxis=dict(showgrid=False, zeroline=False, ticks="outside", ticklen=4),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)", zeroline=False, ticks="outside", ticklen=4),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
)

pio.templates["dash_ui"] = dash_template
pio.templates.default = "dash_ui"
```

This is `plotly_white` plus overrides: white plot background, light y-grid only, no heavy borders, horizontal legend at the top.

## Chart readability

Strip chart junk: unnecessary gridlines, thick axis lines, redundant legends.

Tooltips always carry the metric name, the value with units, and the time period or category label. A tooltip showing only `1234` is not acceptable.

Label the axis or embed the unit in the title, not both inconsistently. Format large numbers as K/M/B and use readable date ticks ("Jan 2026").

## Helpers

```python
def format_currency(fig, axis="y"):
    fig.update_layout({f"{axis}axis": dict(tickprefix="$", separatethousands=True)})
    return fig


def add_subtitle(fig, subtitle: str):
    """Plotly has no portable native subtitle; place an annotation above the plot."""
    fig.add_annotation(
        text=subtitle, xref="paper", yref="paper", x=0, y=1.08,
        showarrow=False, align="left", font=dict(size=12, color="rgba(0,0,0,0.6)"),
    )
    return fig
```

Number formats: percent `.1%`, thousands `,.0f`, simple currency `$,.0f`.

When a graph redraws on every filter change, set `fig.update_layout(uirevision="keep")` so zoom and pan survive the update.

## Graph component defaults

```python
dcc.Graph(
    id="sales-trend",
    figure=fig,
    config={"displayModeBar": False, "scrollZoom": False, "responsive": True},
)
```

## Interaction

Group filters by type (time, geography, product), give them sensible defaults, and hide advanced filters behind a collapsible panel.

Add cross-filtering only when it stays predictable: selection highlighting, a clear-selection action, and a microcopy hint such as "Click bars to filter".

## References

- Dash dashboard design principles: https://dash-resources.com/a-guide-to-beautiful-dashboards-basic-design-principles/ (2025)
- Learn UI Design data color picker: https://www.learnui.design/tools/data-color-picker.html
- Learn UI Design on palette types: https://www.learnui.design/blog/picking-colors-for-your-data-visualizations.html
- Flat UI hex codes: https://colorswall.com/colors/flat-ui/
- "Learnui Design" palette values: https://www.color-hex.com/color-palette/103612
- Plotly templates and theming: https://plotly.com/python/templates/
- Dash Graph component: https://dash.plotly.com/dash-core-components/graph
