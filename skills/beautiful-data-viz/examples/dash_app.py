#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["dash==4.4.0", "plotly==6.5.0"]
# ///
"""Runnable Dash fixture with a WSGI start and callback-latency smoke gate."""

import argparse
import json
import statistics
import time

from dash import Dash, Input, Output, callback, dcc, html
import plotly.graph_objects as go

# Greyscale-first template: series stay grey and differ by marker symbol.
# Color only the trace that carries the finding: marker_color=ACCENT for markers,
# line_color=ACCENT for lines.
ACCENT = "#D55E00"
TEMPLATE = go.layout.Template(
    layout=go.Layout(
        colorway=["#333333", "#a8a8a8"],
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis={"showgrid": False, "zeroline": False},
        yaxis={"showgrid": True, "gridcolor": "rgba(0,0,0,0.06)", "zeroline": False},
    )
)
SYMBOLS = {"A": "circle", "B": "square-open"}
ROWS = [{"group": group, "x": x, "y": x * factor} for group, factor in (("A", 1), ("B", 2)) for x in range(1, 101)]


def filter_points(group: str):
    selected = ROWS if group == "All" else [row for row in ROWS if row["group"] == group]
    figure = go.Figure()
    for label in sorted({row["group"] for row in selected}):
        rows = [row for row in selected if row["group"] == label]
        figure.add_scatter(
            x=[row["x"] for row in rows],
            y=[row["y"] for row in rows],
            mode="markers",
            marker_symbol=SYMBOLS[label],
            name=label,
        )
    figure.update_layout(template=TEMPLATE)
    return figure


def build_app() -> Dash:
    app = Dash(__name__)
    app.layout = html.Main([
        html.H1("Scientific dashboard fixture"),
        dcc.Dropdown(["All", "A", "B"], "All", id="group", clearable=False),
        dcc.Graph(id="figure", figure=filter_points("All")),
    ])

    @callback(Output("figure", "figure"), Input("group", "value"))
    def update_figure(group):
        return filter_points(group)

    return app


def smoke(latency_budget_ms: float) -> dict[str, object]:
    app = build_app()
    response = app.server.test_client().get("/")
    timings = []
    for _ in range(30):
        started = time.perf_counter()
        filter_points("A")
        timings.append((time.perf_counter() - started) * 1000)
    p95 = statistics.quantiles(timings, n=20)[18]
    return {"http_status": response.status_code, "callback_p95_ms": p95, "latency_budget_ms": latency_budget_ms, "passed": response.status_code == 200 and p95 <= latency_budget_ms}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--latency-budget-ms", type=float, default=300)
    parser.add_argument("--port", type=int, default=8050)
    args = parser.parse_args()
    if args.smoke:
        result = smoke(args.latency_budget_ms)
        print(json.dumps(result, indent=2))
        return 0 if result["passed"] else 2
    build_app().run(debug=False, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
