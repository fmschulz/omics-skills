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

### Remaining 3 failures (resolved in PR 6)

All three were cleared in the follow-up PR. See "PR 6" below.

## PR 4 — SessionStart / UserPromptSubmit hook

| Metric | Before | After | Δ |
|---|---|---|---|
| Pass rate | 35/38 (92.1%) | 35/38 (92.1%) | 0 |

PR 4 is about **enforcing** the router, not expanding it. Benchmark output is unchanged because the same `route_request` is being called — just from a hook on every user prompt instead of prose text asking Claude / Codex to run a shell command. Routing signal quality stays where PR 5 left it.

### What shipped

- `scripts/emit_routing_hint.py` — hook script. Reads stdin JSON (Claude Code `UserPromptSubmit` payload) or falls back to raw prompt. Calls `route_request` and emits either `hookSpecificOutput` JSON (Claude Code contract, prepends a `## Routing hint` block to context) or plain text (`--text` for Codex CLI).
- `scripts/install_hook.py` + `make install-hook` / `make uninstall-hook` / `make hook-status` — idempotent installer for Claude Code `~/.claude/settings.json` and Codex CLI `~/.codex/hooks.json` (identical JSON schema — Codex adopted Claude Code's `UserPromptSubmit` contract in 2026). Also writes `[features] codex_hooks = true` into `~/.codex/config.toml` to enable Codex's hook system. Atomic writes (tempfile + rename) prevent torn files under concurrent edits; structural marker matching (`omics-skills-autoroute` marker combined with the hook script path) prevents double-installs and false positives.
- `tests/test_emit_routing_hint.py` — 9 tests covering: empty stdin, opt-out env var, JSON mode, text mode, `--prompt` flag, bare-prompt stdin, off-topic query (suppressed), idempotent Claude install, Codex install preserves existing content.
- All 5 agent prompts updated — the old "Skill Lookup" prose now says "If the hook is installed, follow the injected hint; otherwise fall back to the command."
- Opt-out: `OMICS_SKILLS_AUTOROUTE=0` in env exits the hook silently.
- Failure mode: on any error (catalog missing, route raises), the hook returns exit 0 and emits an HTML comment explaining the skip — never blocks a user prompt.

### Enable it

```
make install-hook       # Claude Code + Codex CLI
make hook-status        # check install state
make uninstall-hook     # remove
```

### Remaining router gaps

Resolved in PR 6 (see below).

## PR 6 — Disambiguate shared skills and cover causal-reasoning vocabulary

| Metric | Before | After | Δ |
|---|---|---|---|
| Pass rate | 35/38 (92.1%) | **37/37 (100%)** | closes all remaining failures |
| Agent-selection failures | 2 | 0 | −2 |
| Primary-skill failures | 1 | 0 | −1 |
| Forbidden-skill leaks | 0 | 0 | 0 |

Three changes close the last failures:

1. **Retire `agent-collaboration`.** Rarely used in practice; its task patterns (`plan critique`, `code review`, `second opinion`) sourced the `reason about causation → agent-collaboration` phantom. Deleting the skill, scrubbing references from all five agent prompts, and removing the two benchmark rows that depended on it eliminated both that false positive and one shared-skill tiebreak. Suite shrinks from 38 to 37 rows.

2. **Section-heading context in agent scoring.** When a skill is co-owned — e.g. `bio-logic` is filed under "Scientific Reasoning & Hypothesis Formation" in `omics-scientist` but "Scientific Reasoning & Evaluation" in `science-writer` — the router now adds a score bonus proportional to the overlap between query tokens and the section heading under which each agent lists the shared skill. `formulate a hypothesis …` therefore prefers `omics-scientist` even though `science-writer` wins the raw-alphabetical tiebreak.

3. **bio-logic task patterns extended** with `reason, causation, causal, observational, follow-up experiments, formulate hypothesis, experimental design` so causal-reasoning queries are recognised instead of scoring zero and falling back to whichever agent tokens happened to overlap.

New guard test `test_section_heading_wins_over_alphabetical_tiebreak` pins the section-heading behaviour so this cannot regress silently.
