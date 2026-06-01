---
name: polars-dovmed
description: Search the PMC Open Access literature with polars-dovmed. Author structured JSON queries directly, then use the hosted API when an API key is available or fall back to local dovmed scan over PMC, bioRxiv, or both parquet corpora.
user-invocable: true
---

# polars-dovmed

Search PubMed Central Open Access and bioRxiv parquet corpora with `polars-dovmed`.

Use the bundled helper, `skills/polars-dovmed/scripts/query_literature.py`, for hosted API or local parquet-backed searches. The helper auto-loads `~/.config/polars-dovmed/.env`.

Current hosted API defaults:
- Treat API keys as secrets. Do not put a key in command lines, saved artifacts, memory records, summaries, or final answers. If the user pasted a real key into chat, tell them it should be rotated.
- Save generated run artifacts under `tasks/polars-dovmed-runs/<slug>/` by default, not under `skills/polars-dovmed/`.
- Prefer structured async search through `/api/jobs` targeting `scan_literature_advanced(mode="discovery")`.
- Do not use the flat `/api/search_literature` endpoint for smoke tests or normal skill work. It is opt-in only with `--allow-flat-query` and may hang behind the edge proxy.
- Do not start with `--corpus both`. Run `--corpus biorxiv` and `--corpus pmc` as separate calls, then merge results.
- Do not start with hosted `--year-bands recent_split` or `--year-bands clean_split`. Some deployments do not expose those materialized database names and return `Database not found`.
- For recent or emerging taxa, run bioRxiv anchor-only discovery first with a hard timeout. Run PMC separately only when the user needs PMC/peer-reviewed coverage.
- For interactive work, pass `--poll-timeout` and, when available, wrap long searches in `/usr/bin/timeout` or `timeout`. Do not let broad PMC scans run unbounded.

Public access note:
- `omics-skills` does not provide a hosted API key or the PMC/bioRxiv parquet corpora.
- Public users can prepare local PMC searches from Uri Neri's upstream package: <https://github.com/UriNeri/polars-dovmed>.
- Local setup uses upstream `dovmed download`, `dovmed build-parquet`, and `dovmed scan`.
- If no API key and no local corpus exist, state that `polars-dovmed` is not configured and use another literature fallback.

## Instructions

1. Route the task and decide execution mode.
   - Use hosted API when `POLARS_DOVMED_API_KEY` is configured or provided.
   - Use local `dovmed scan` when hosted access is unavailable and local parquet paths exist.
   - Do not imply that this repo ships hosted access or local corpora.
2. Create a dedicated run directory.
   - Default: `tasks/polars-dovmed-runs/<date-topic>/`.
   - Save `prompt.txt`, `query.json`, submitted payloads, raw responses, timing files, and any curated summary.
   - Never save secrets.
3. Author a structured query JSON directly.
   - Start with exact anchor names and aliases.
   - Add relation groups only when they improve precision.
   - Use `disqualifying_terms` for acronym collisions and wrong systems.
   - For "hosts of X" or other recent-taxonomy prompts, first run an anchor-only query for X and aliases; use host terms during triage or a second pass.
4. Inspect the query JSON before searching.
   - Check spelling, taxonomy aliases, regex escaping, and noisy terms.
   - Keep support terms soft in discovery; avoid generic anchors such as `host` alone.
5. Run discovery first.
   - API path: `--queries-file ... --mode discovery --corpus biorxiv|pmc`.
   - Use `--extract-matches none --add-group-counts primary`.
   - Use bounded polling, for example `--poll-timeout 75` for bioRxiv and `--poll-timeout 110` for PMC.
   - Keep `--details-rerank-limit` modest, usually 8-12.
6. Inspect the first 5-10 hits.
   - If results are noisy, refine `query.json` and rerun.
   - For citation-quality answers, verify final metadata in PubMed/PMC, Crossref, DOI landing pages, or journal pages.
7. Record timings when the user asks about speed.
   - Capture wall time with shell `time -p` or `timeout ...`.
   - Also report helper/API `elapsed_ms` when present.
   - Timeouts and failed endpoints are valid measured results; do not hide them.

## Hosted API Reachability

Minimal reachability check:

```bash
curl -sS --max-time 20 https://api.newlineages.com/
```

Expected: service metadata from the root endpoint. This only proves the service is reachable, not that a corpus scan is healthy.

Structured smoke check:

```bash
RUN=tasks/polars-dovmed-runs/smoke-$(date +%Y%m%d)
mkdir -p "$RUN"
cp skills/polars-dovmed/fixtures/smoke_prompt.txt "$RUN/prompt.txt"
cp skills/polars-dovmed/fixtures/smoke_query.json "$RUN/query.json"

timeout 90s uv run --no-project python skills/polars-dovmed/scripts/query_literature.py \
  --queries-file "$RUN/query.json" \
  --corpus biorxiv \
  --mode discovery \
  --max-results 3 \
  --skip-details-rerank \
  --poll-timeout 75 \
  --save-payload "$RUN/payload_smoke.json" \
  --save-response "$RUN/results_smoke.json" \
  > "$RUN/summary_smoke.json" 2> "$RUN/time_smoke.txt"
```

If `timeout` is unavailable, still pass `--poll-timeout` and record that no outer wall-clock guard was available. Avoid `/usr/bin/time`; use shell `time -p` unless you have confirmed the path exists.

Known client pitfall: Cloudflare can reject Python `urllib`'s default user agent with HTTP `403` and error code `1010`. The helper sends a normal user agent. If raw `urllib` is unavoidable, send both `X-API-Key` and `User-Agent`.

## Preferred Workflow

### Step 1: Author Query JSON

Use compact concept groups:

```json
{
  "anchor_entity": [
    ["primary_name"],
    ["alias_1"],
    ["alias_2"]
  ],
  "relation_or_property": [
    ["primary_name", "relation_term"],
    ["alias_1", "specific_relation_alias"]
  ],
  "disqualifying_terms": [
    ["term_to_exclude"]
  ]
}
```

For recent taxa or sparse terms, begin with anchor-only JSON:

```json
{"anchor_entity": [["Mirusviricota"], ["mirusvirus"], ["mirusviruses"]]}
```

### Step 2: Search With Hosted API

Fast first pass for emerging taxa:

```bash
RUN=tasks/polars-dovmed-runs/mirusviricota-hosts-$(date +%Y%m%d)
mkdir -p "$RUN"
printf '%s\n' "papers describing hosts of Mirusviricota" > "$RUN/prompt.txt"
# Write and inspect "$RUN/query.json" before running the search.

timeout 90s uv run --no-project python skills/polars-dovmed/scripts/query_literature.py \
  --queries-file "$RUN/query.json" \
  --corpus biorxiv \
  --mode discovery \
  --extract-matches none \
  --add-group-counts primary \
  --max-results 25 \
  --details-rerank-limit 12 \
  --poll-timeout 75 \
  --save-payload "$RUN/payload_biorxiv.json" \
  --save-response "$RUN/results_biorxiv.json" \
  > "$RUN/summary_biorxiv.json" 2> "$RUN/time_biorxiv.txt"
```

Optional PMC pass with a bounded wait:

```bash
timeout 120s uv run --no-project python skills/polars-dovmed/scripts/query_literature.py \
  --queries-file "$RUN/query.json" \
  --corpus pmc \
  --mode discovery \
  --extract-matches none \
  --add-group-counts primary \
  --max-results 25 \
  --details-rerank-limit 8 \
  --poll-timeout 110 \
  --save-payload "$RUN/payload_pmc.json" \
  --save-response "$RUN/results_pmc.json" \
  > "$RUN/summary_pmc.json" 2> "$RUN/time_pmc.txt"
```

Use `--year-band 2024_plus` only for an explicitly era-limited PMC query. Use `--year-bands ...` only after a smoke check confirms the current hosted deployment exposes those band names.

Fetch details directly when you already know identifiers:

```bash
uv run --no-project python skills/polars-dovmed/scripts/query_literature.py \
  --details PMC6912108 PMC8490762 \
  --corpus pmc \
  --save-payload "$RUN/payload_details.json" \
  --save-response "$RUN/results_details.json"
```

For bioRxiv details, pass DOI values with `--corpus biorxiv`.

### Step 3: Search Locally With dovmed scan

Use local mode when hosted access is unavailable or explicitly unwanted.

```bash
uv run --no-project python skills/polars-dovmed/scripts/query_literature.py \
  --execution-mode local \
  --corpus pmc \
  --local-parquet-pattern "$DOVMED_PMC_PARQUET" \
  --queries-file "$RUN/query.json" \
  --save-payload "$RUN/payload_local.json" \
  --save-response "$RUN/results_local.json"
```

Local corpus aliases:
- `--corpus pmc`: set `DOVMED_PMC_PARQUET` or pass `--local-parquet-pattern`.
- `--corpus biorxiv`: set `DOVMED_BIORXIV_PARQUET` or pass `--local-parquet-pattern`.
- `--corpus both`: only with one compatible explicit parquet pattern; otherwise run separate scans.

## Search Semantics

- Prefer structured JSON over ad hoc natural-language search strings.
- Build searches around anchor concepts first.
- Put alternate names and spelling variants inside the same concept group.
- Treat support concepts as refiners, not anchors.
- For "X of Y" prompts, combine X and relation terms inside an OR-of-AND group only after an anchor-only discovery pass if recall is poor.
- Down-rank papers matching only generic support terms or full-text-only background mentions.

Ranking priority:
1. exact anchor hit in title
2. exact anchor hit in abstract
3. anchor plus support co-occurrence in title or abstract
4. multiple distinct relevant group matches
5. full-text-only matches

## Quick Reference

| Task | Action |
|------|--------|
| Run directory | `tasks/polars-dovmed-runs/<date-topic>/` |
| Preferred query | Authored `query.json`, inspected before search |
| Preferred hosted path | async `scan_literature_advanced(mode="discovery")` via helper |
| Emerging taxon first pass | `--corpus biorxiv`, anchor-only query, bounded timeout |
| PMC pass | separate `--corpus pmc` call with `--poll-timeout` and outer timeout |
| Avoid by default | flat `/api/search_literature`, `--corpus both`, hosted `--year-bands` |
| Details endpoint | `--details ... --corpus pmc|biorxiv` |
| Local fallback | `--execution-mode local --local-parquet-pattern ...` |
| Quick verification | `uv run --no-project python skills/polars-dovmed/scripts/smoke_test.py --run-dir tasks/polars-dovmed-runs/smoke-test` |
| Timing | shell `time -p`, helper `elapsed_ms`, and timeout status |

## Input Requirements

- A literature search prompt or inspected structured `query.json`.
- Hosted API key or local parquet files for the requested corpus.
- Writable run directory outside the skill source tree.

## Output

- `prompt.txt`, `query.json`, payload JSON, raw response JSON, timing files, and optional curated summary.
- Paper list with titles, identifiers, corpus, relevance notes, and timing.
- Warnings for timeout, 502, database-not-found, missing metadata, or fallback use.

## Quality Gates

- [ ] API key handled as a secret and not persisted.
- [ ] Run directory is outside `skills/polars-dovmed/`.
- [ ] Query JSON authored and inspected before search.
- [ ] Hosted API root or helper smoke checked before declaring outage.
- [ ] Flat endpoint, `--corpus both`, and hosted `--year-bands` avoided unless explicitly justified.
- [ ] Discovery mode used before advanced refinement.
- [ ] First 5-10 hits reviewed and noisy terms refined.
- [ ] Long PMC scans have bounded poll and wall-clock timeout.
- [ ] Timings and failure modes reported when speed is part of the request.
- [ ] Citation metadata verified externally when final citation quality matters.

## Examples

### Mirusviricota Host Search

1. Create `tasks/polars-dovmed-runs/mirusviricota-hosts-YYYYMMDD/query.json` with:

```json
{"anchor_entity": [["Mirusviricota"], ["mirusvirus"], ["mirusviruses"]], "disqualifying_terms": [["MIRU-VNTR"], ["mycobacterium"]]}
```

2. Run the bioRxiv hosted command from Step 2.
3. Inspect `results_biorxiv.json` and any companion details response.
4. Run the bounded PMC command only if PMC coverage is needed.
5. Summarize direct host evidence separately from background mentions.

### Local PMC Search

```bash
RUN=tasks/polars-dovmed-runs/klosneuvirinae-hosts
uv run --no-project python skills/polars-dovmed/scripts/query_literature.py \
  --execution-mode local \
  --corpus pmc \
  --local-parquet-pattern "$DOVMED_PMC_PARQUET" \
  --queries-file "$RUN/query.json" \
  --save-payload "$RUN/payload_local.json" \
  --save-response "$RUN/results_local.json"
```

## Troubleshooting

**Issue**: User pasted an API key into chat
**Solution**: Do not repeat or save it. Tell the user to rotate the key if it is real, then use an environment file or shell environment.

**Issue**: Flat `/api/search_literature` times out
**Solution**: Do not use it for smoke tests. Use the root endpoint plus structured helper smoke.

**Issue**: `--corpus both` returns 502
**Solution**: Run separate `--corpus biorxiv` and `--corpus pmc` calls and merge results manually.

**Issue**: `--year-bands recent_split` or `clean_split` returns `Database not found`
**Solution**: Drop `--year-bands`. Use a single corpus search, or a single verified `--year-band`.

**Issue**: PMC scan is still running after a practical interactive wait
**Solution**: Stop at the configured timeout, report the measured timeout, and try a narrower anchor-only or era-limited PMC query.

**Issue**: `/usr/bin/time` is missing
**Solution**: Use shell `time -p` or record start/end timestamps; do not assume `/usr/bin/time` exists.

**Issue**: Artifacts were written under `skills/polars-dovmed/runs/`
**Solution**: Move future run artifacts to `tasks/polars-dovmed-runs/` and do not commit generated run outputs.

**Issue**: Hosted API key is missing and local parquet files are missing
**Solution**: State that `polars-dovmed` is not configured. Use another literature-search skill or ask the user to provide hosted access or local corpora.
