# Dash dashboards

Colour rules come from [../SKILL.md](../SKILL.md) and [palettes.md](palettes.md). This file adds Dash structure, the figure template and the smoke test. The runnable app is [../examples/dash_app.py](../examples/dash_app.py); copy its structure.

## Structure

- Small app: `app.py`, `assets/styles.css`, `utils/{data.py,figures.py}`, `README.md`.
- Larger app: add `pages/` (Dash Pages: `Dash(__name__, use_pages=True)`), `components/`, `callbacks/`, `utils/transforms.py` and `data_dictionary.md`.
- Layout modules define components; callback modules define interactivity. One callback does one thing. Pull transforms into `utils/transforms.py`.
- Fan-out for shared work: one data callback filters and aggregates into a `dcc.Store`; separate render callbacks build each chart from it. Chain callbacks only for a real dependency.
- Useful tools: `PreventUpdate`, `dash.no_update`, `prevent_initial_call=True`, `ctx.triggered_id`, `running=[(Output(...), True, False)]` to disable controls, `cancel=[Input(...)]`.

## Performance

1. Move expensive work out of the request loop: cache at the data layer (load and filter once per filter signature), pre-aggregate, and use background callbacks for work that can pass about 30 s or that several users may trigger (DiskCache locally, Celery with Redis in production).
2. Show loading states and disable the triggering controls while a callback runs.
3. Render less: fewer traces, downsampled time series, WebGL traces for very large point clouds. Put large tables in `dash-ag-grid` (it fills its parent, so a wrong look is usually CSS sizing).

## Figure template

Register one template before building any chart, so no figure is styled by hand. Series stay grey; set `marker_color=ACCENT` (or `line_color=ACCENT`) only on the trace that carries the finding. `ACCENT` is the Okabe-Ito vermillion on light backgrounds (orange `#E69F00` on dark).

```python
import plotly.graph_objects as go
import plotly.io as pio

DASH_COLORWAY = ["#333333", "#7a7a7a", "#a8a8a8", "#555555"]
ACCENT = "#D55E00"

pio.templates["dash_ui"] = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Inter, system-ui, Segoe UI, Roboto, Helvetica, Arial, sans-serif", size=13),
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
pio.templates.default = "dash_ui"
```

Label traces directly (`mode="lines+text"` or an annotation at the last point) and hide the legend where that fits. Use Plotly scales for magnitude (`px.colors.sequential.Viridis`) and signed values (`RdBu` with `zmid=0`).

## Smoke test

```bash
uv run --script ~/.agents/skills/beautiful-data-viz/examples/dash_app.py --smoke --latency-budget-ms 300
```

It must print `passed: true`: HTTP 200 and a measured pure-callback p95 inside the budget (exit 2 otherwise). Also check: filters have defaults and visible state, tooltips carry units, empty states are handled, no horizontal scroll on a phone width, requirements are pinned, and the README gives purpose, run command and data sources.
