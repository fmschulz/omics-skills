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

| Metric | Before | After | Δ |
|---|---|---|---|
| Pass rate | 23/38 (60.5%) | 23/38 (60.5%) | 0 |

Pure plumbing change — no routing signal should move. Catalog JSON now stores repo-relative paths (`skills/add-molab-badge/SKILL.md`); `route_request` resolves them against `metadata.source_repo` so output paths stay absolute. `catalog/*.json` is committed and shareable across checkouts.

## PR 5 — Router consumes typed edges + cross-refs

| Metric | Before | After | Δ |
|---|---|---|---|
| Pass rate | 23/38 (60.5%) | **35/38 (92.1%)** | **+12** |
| Agent-selection failures | 3 | 2 | −1 |
| Primary-skill failures | 12 | 1 | −11 |
| Ordered-skill failures | 0 | 0 | 0 |
| Forbidden-skill leaks | 1 | 0 | −1 |
| `compose_with` edges | 6 | 46 | +40 |
| Total graph edges | 18 | 58 | +40 |

### What changed

1. **Agents now expose the full notebook / writing specialist set.** `dataviz-artist` gained `marimo-notebook`, `jupyter-to-marimo`, `anywidget`, `add-molab-badge`, `implement-paper-auto` as first-class Mandatory Skills; `science-writer` gained `proposal-review` and `ai-scientist-evaluator`; `codexloop` gained `get-api-docs`. Task-recognition patterns updated to match. Each skill remains independently invocable.
2. **Router consumes `compose_with` and `similar_to` edges.** `route_request` now surfaces typed neighbours of every primary skill as supporting skills (new `compose_neighbors()` helper). Respects the active agent filter and platform gate.
3. **`## Related Skills` sections added to 15 cluster SKILL.md files** (literature × 5, notebook × 5, writing/review × 5). Parser picks these up as `compose_with` edges, enriching the graph from 6→46 typed edges.
4. **Alternative-source cross-refs tuned.** `arxiv-search` and `biorxiv-search` intentionally do NOT cross-reference each other; they serve different query domains and would leak into the wrong `forbidden_skills` set if treated as composable partners.

### Remaining 3 failures (deferred)

All three are shared-skill agent-selection tiebreaks:

- "formulate a hypothesis" — `bio-logic` is owned by both `omics-scientist` and `science-writer`; alphabetical tiebreak picks science-writer. Fix: add agent-description weighting or prefer-earlier-owner tiebreak. Out of scope for PR 5.
- "ask a peer Codex pane" — `agent-collaboration` is owned by every agent; picks `science-writer` over `codexloop`. Same tiebreak problem.
- "reason about causation" — `bio-logic` not recognised; `agent-collaboration` wins via a phantom single-token overlap (`plan` → `plan critique`). Needs either tighter pattern thresholds (attempted, regressed other tests) or a stop-word list.

Tracked for a follow-up router-disambiguation PR.

## PR 4 — SessionStart hook

_Pending._
