---
name: plotly-dashboard-skill
description: Build production-ready Plotly Dash dashboards. Use when scientific data needs an interactive, consistently themed layout with clear and performant callbacks.
---

# Plotly Dashboard Skill

Create interactive dashboards with a single source of truth for UI and figure styling.

## Instructions

1. Capture audience, questions, and data constraints.
2. Pick a layout pattern and component library. Layout, typography, color, and the shared figure template are in [references/style.md](references/style.md).
3. Register the figure template once, before building any chart, so no figure is styled by hand.
4. Build the layout skeleton before callbacks.
5. Implement callbacks with clear inputs and outputs. Project structure, the data-callback-to-render-callback fan-out, and the advanced callback tools are in [references/architecture.md](references/architecture.md).
6. Optimize slow callbacks with caching, pre-aggregation, or background callbacks; the same reference covers when each applies.
7. Start from [examples/app.py](examples/app.py), the runnable app this skill tests. Copy its structure rather than writing a skeleton from scratch.

## Input Requirements

- Audience and key decisions
- Data sources and update cadence
- Required filters and views
- Deployment constraints

## Output

- Dash app scaffold (layout + callbacks)
- Consistent theming and figure templates
- README with usage notes

## Quality Gates

Run the smoke test before calling a dashboard done:

```bash
uv run --script examples/app.py --smoke --latency-budget-ms 300
```

It must return HTTP 200 with a measured pure-callback p95 inside the declared budget.

Visual and interaction:

- [ ] Page has a clear title and a "last updated" stamp
- [ ] Filters are grouped, have sensible defaults, and their current state is visible
- [ ] Spacing, alignment, and legend placement are consistent; legends do not cover data
- [ ] Charts carry readable titles and axis labels or units in the title
- [ ] Tooltips include units and clean formatting
- [ ] No chart is rainbow-colored without meaning, and no meaning is encoded by color alone
- [ ] Empty states are handled; no blank white cards
- [ ] Mobile and tablet views are usable, with no unintended horizontal scroll
- [ ] Click-to-filter is obvious and reversible, with a clear reset action

Performance:

- [ ] Common interactions stay under roughly 300 ms
- [ ] Expensive work is cached or moved to background callbacks
- [ ] Large tables use AG Grid virtualization
- [ ] No callback chains that create spaghetti dependencies

Code and documentation:

- [ ] Structure separates pages, components, callbacks, and utils
- [ ] Callbacks are small; reusable figure helpers replace repeated styling code
- [ ] Requirements are pinned
- [ ] README covers purpose, audience, local run, configuration, data sources, and a screenshot
- [ ] A data dictionary defines key metrics and known caveats

## Non-Goals

- Static publication figures. Use `/beautiful-data-viz` for matplotlib or seaborn output.
- Data analysis itself. This skill presents results; it does not compute them.

## Troubleshooting

**Issue**: Slow callbacks
**Solution**: Cache expensive steps or pre-aggregate data. See [references/architecture.md](references/architecture.md).

**Issue**: Charts drift out of a shared look
**Solution**: A figure is being styled inline instead of inheriting the registered template. Move the override into the template in [references/style.md](references/style.md).
