# Dash Architecture and Performance

Last verified: 2026-09-05
Tool version/release checked: Dash 4.4.0
Official docs/manual: https://dash.plotly.com/urls and https://dash.plotly.com/background-callbacks
Release/source: https://github.com/plotly/dash/releases

## Project structure

Single page, small app:

```
my_app/
  app.py
  assets/styles.css
  utils/{data.py,figures.py}
  README.md
```

Multi-page, once the app grows:

```
my_app/
  app.py
  pages/{overview.py,drilldown.py}
  components/{header.py,filters.py,cards.py}
  callbacks/{overview_callbacks.py,drilldown_callbacks.py}
  utils/{data.py,transforms.py,figures.py}
  assets/styles.css
  README.md
  data_dictionary.md
```

Use Dash Pages for routing: `app = Dash(__name__, use_pages=True)`, then register each module under `pages/`.

## Callback rules

Keep layout modules defining components and callback modules defining interactivity. A callback should be about one thing: pull transforms into `utils/transforms.py` rather than letting one callback both reshape data and build several outputs.

Use the fan-out pattern for shared work: one data callback filters and aggregates into a `dcc.Store`, and separate render callbacks build each chart from the stored result. This is what keeps a dashboard out of callback spaghetti; do not chain callbacks unless the dependency is real.

Tools worth reaching for:

- `PreventUpdate` to stop updating outputs until inputs are valid
- `dash.no_update` to update only some outputs
- `prevent_initial_call=True` to skip unnecessary initial work
- `ctx.triggered_id` to handle multi-input callbacks cleanly
- `running=[(Output(...), True, False)]` to disable controls while a callback runs
- `cancel=[Input(...)]` for cancellation

## Performance

Three principles, in order of payoff:

1. Move expensive work out of the request loop. Cache results, pre-aggregate, push long tasks to background callbacks.
2. Make the UI feel fast. Show loading states, disable the triggering controls while running, report progress on long jobs.
3. Render less. Reduce trace count, downsample time series, use WebGL traces for very large point clouds.

Reach for background callbacks when a callback can exceed the typical web server timeout (about 30 s) or when several users may trigger the same expensive work. DiskCache is the easiest local backend; Celery with Redis is the production choice.

Cache at the data layer first (load and filter once per filter signature) and only cache figure building when building the figure is itself expensive. `flask_caching` covers memoization; DiskCache or Celery covers background work.

Large tables belong in `dash-ag-grid`. A grid that looks wrong is usually a CSS sizing problem: the grid fills its parent.

## References

- Dash Pages: https://dash.plotly.com/urls
- Dash advanced callbacks: https://dash.plotly.com/advanced-callbacks
- Callback organization: https://dash-resources.com/dash-callbacks-best-practices-with-examples/ (updated 2025)
- App architecture patterns: https://deepwiki.com/plotly/dash-sample-apps/9-best-practices-and-common-patterns
- Background callbacks and job queues: https://dash.plotly.com/background-callbacks
- Interactive graphing and WebGL: https://dash.plotly.com/interactive-graphing
- AG Grid sizing: https://dash.plotly.com/dash-ag-grid/grid-size
