# Dashboard and Figure Style

Last verified: 2026-09-05
Tool version/release checked: Dash 4.4.0, Plotly 6.5.0
Official docs/manual: https://dash.plotly.com/ and https://plotly.com/python/templates/
Release/source: https://github.com/plotly/dash/releases

Dash-specific layout, typography, and template rules. The shared visual rules (greyscale first, chart choice, direct labels, accessibility) live in `/beautiful-data-viz`; this file applies them to Plotly. One template drives every chart, so nothing is styled twice.

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

Follow the greyscale-first rule from `/beautiful-data-viz` ([../../beautiful-data-viz/SKILL.md](../../beautiful-data-viz/SKILL.md)): neutrals carry structure (background, borders, text) and every chart starts grey. Add color only when it encodes a category the reader must tell apart, the one highlighted finding, or an ordered or signed quantity. Keep each color's meaning constant across the dashboard.

- One accent marks the finding or the current selection: Okabe-Ito vermillion `#D55E00` on light backgrounds, orange `#E69F00` on dark.
- Categories that need color: at most three or four per view, from a colorblind-safe set (`px.colors.qualitative.Safe` or the Okabe-Ito list in [../../beautiful-data-viz/references/palettes.md](../../beautiful-data-viz/references/palettes.md)). Past that, show top-N plus a grey "Other", small multiples, or a table.
- Good/bad or increase/decrease: use a colorblind-safe pair (blue `#0072B2` and vermillion `#D55E00`), never red/green, and also show the sign with an arrow, `+`/`-`, or the value.
- Magnitude: a sequential scale such as `px.colors.sequential.Viridis`. Signed values: a diverging scale such as `RdBu` with `zmid=0`.
- Never encode meaning by color alone. Add labels, marker symbols, line dashes, or ordering, and keep text contrast sufficient.

```python
# Neutral colorway: series stay grey. On the trace that carries the finding, set
# marker_color=ACCENT (markers, bars) or line_color=ACCENT (lines).
DASH_COLORWAY = ["#333333", "#7a7a7a", "#a8a8a8", "#555555"]
ACCENT = "#D55E00"
```

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

This is `plotly_white` plus overrides: grey colorway, white plot background, light y-grid only, no heavy borders, horizontal legend at the top. Where traces fit, label them directly (`mode="lines+text"` or an annotation at the last point) and hide the legend.

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
    """Use Plotly's native subtitle (layout.title.subtitle, Plotly 5.23 and later)."""
    fig.update_layout(title_subtitle_text=subtitle, title_subtitle_font_color="rgba(0,0,0,0.6)")
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
- Okabe-Ito colorblind-safe colors: https://jfly.uni-koeln.de/color/
- Plotly built-in color scales: https://plotly.com/python/builtin-colorscales/
- Plotly figure titles and subtitles: https://plotly.com/python/figure-labels/
- Plotly templates and theming: https://plotly.com/python/templates/
- Dash Graph component: https://dash.plotly.com/dash-core-components/graph
