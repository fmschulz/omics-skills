# Routing improvements

Track how router changes affect the benchmark in `tests/routing_benchmark.yaml`.

Run:

```bash
python3 scripts/routing_benchmark.py                 # human report
python3 scripts/routing_benchmark.py --json          # machine output
python3 scripts/routing_benchmark.py --compare docs/routing_baseline.json
```

## Baseline (post–parser-fix, before PR 3–5)

| Metric | Value |
|---|---|
| Pass rate | **23/38 (60.5%)** |
| Agent-selection failures | 3 |
| Primary-skill failures | 12 |
| Ordered-skill failures | 0 |
| Forbidden-skill leaks | 1 |

**Failure categories:**

1. **Aspirational notebook-cluster routing (5 rows)** — tasks that name marimo / jupyter-to-marimo / add-molab-badge / anywidget / implement-paper-auto expect the specialist skill, but `dataviz-artist.md` only exposes `/notebook-ai-agents-skill` for all notebook work. These rows target the desired post-PR-5 behaviour, not current contract. Fix requires either tightening agent skill lists or teaching the router to surface specialists via typed edges.
2. **Writing-specialist router misses (3 rows)** — `manuscript-review-council`, `proposal-review`, `ai-scientist-evaluator` are listed in `science-writer.md` but collapse to `bio-logic` + `scientific-writing` under token overlap. Genuine router weakness — likely closeable with task-pattern specificity.
3. **Agent selection (3 rows)** — `agent-collaboration` picks `science-writer` over `codexloop`; "reason about causation" routes to `codexloop` over `bio-logic`; notebook tasks misroute.
4. **Catalog/utility (1 row)** — `get-api-docs` description tokens miss "API documentation" queries.
5. **Forbidden-skill leaks (1 row)** — low-overlap cases where the specialist is not named but a related utility sneaks into `ordered_skills`.

## PR 3 — Repo-relative catalog paths

_Pending._

## PR 5 — Router consumes typed edges + cross-refs

_Pending._

## PR 4 — SessionStart hook

_Pending._
