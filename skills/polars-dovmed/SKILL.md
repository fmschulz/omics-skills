---
name: polars-dovmed
description: Run structured full-text searches of PMC Open Access and bioRxiv with polars-dovmed. Use for reproducible literature searches through the hosted API or local parquet corpora.
user-invocable: true
---

# polars-dovmed

Search the PubMed Central Open Access and bioRxiv corpora with `polars-dovmed`, through the hosted API or local parquet files.

`SKILL_DIR` is the directory that contains this `SKILL.md`, installed at `~/.agents/skills/polars-dovmed`. Run the helper as `uv run --script "$SKILL_DIR/scripts/query_literature.py"` so its pinned dependency is available. The helper loads `~/.config/polars-dovmed/.env`.

## Access

- Hosted API: needs `POLARS_DOVMED_API_KEY` in the environment or in the `.env` file. Never pass the key in argv, and never write it to run directories, memory records, summaries, or answers. The API root (`https://api.newlineages.com/`) states that keys are issued by the admin only.
- Local corpora: upstream `dovmed download`, `dovmed build-parquet`, and `dovmed scan` from <https://github.com/UriNeri/polars-dovmed>. `omics-skills` ships neither an API key nor the corpora.
- With neither, state that `polars-dovmed` is not configured and use another literature skill.

## Instructions

1. Create a run directory, `tasks/polars-dovmed-runs/<date-topic>/`, outside `$SKILL_DIR`. Save `prompt.txt`, `query.json`, payloads, raw responses, timing files, and any curated summary there. Do not commit generated runs.
2. Write `query.json` (format below) and inspect it before searching: spelling, taxonomy aliases, regex escaping, and noisy terms.
   - Start anchor-only: exact entity names and evidence-based aliases. For prompts such as "hosts of X" or "distribution and genomics of X", search X and its aliases first and use the topic words for triage or a second pass. Never add generic words (distribution, genome, environment, host, taxonomy) as peer OR concepts.
   - Do not invent aliases by splitting compact taxon, gene, or clade names. Keep a real multi-word synonym as one phrase term.
   - Put acronym collisions and wrong systems in `disqualifying_terms`.
3. Run discovery first, one corpus per call. Never start with `--corpus both`.
   - bioRxiv: async discovery with `--poll-timeout 75` and `--details-rerank-limit` 8 to 12.
   - OpenPMC: `--sync --year-bands clean_split --year-band-workers 4 --skip-details-rerank --poll-timeout 120`. Map a requested year range to its bands and search only those (table below). Never run a broad unbanded OpenPMC scan. Fetch details by PMCID after inspecting the top hits.
   - Use `--extract-matches none --add-group-counts primary` for discovery.
   - Wrap calls in `timeout` when it exists.
4. Inspect the first 5 to 10 hits. If they are noisy, refine `query.json` and rerun.
5. Fill citation metadata from the corpus details first, then from `--crossref-metadata` or `/crossref-lookup`. Use DOI landing pages only when corpus metadata and Crossref disagree or stay ambiguous; do not use generic web search for DOI repair.
6. When speed matters, record wall time with shell `time -p` or `timeout`, plus the helper's `elapsed_ms`. Timeouts and failed endpoints are results; report them.
7. Do not use the flat `/api/search_literature` endpoint. It needs `--allow-flat-query` and can hang behind the edge proxy.

### Query JSON

```json
{
  "anchor_entity": [["primary_name"], ["alias_1"], ["alias_2"]],
  "relation_or_property": [["primary_name", "relation_term"]],
  "disqualifying_terms": [["term_to_exclude"]]
}
```

Both search paths (FTS and parquet scan) apply the same logic: terms in one inner group are AND'd and must co-occur; inner groups in a concept are OR'd; concepts are OR'd, and items matching more groups rank higher. A multi-word term matches as an exact phrase. List each synonym as its own single-term group; use a multi-term group only to require co-occurrence.

Rank hits in this order: anchor in title, anchor in abstract, anchor plus support term in title or abstract, several distinct group matches, full-text-only matches. Down-rank hits that match only generic support terms.

### Year bands (OpenPMC)

| Requested years | `--year-bands` value |
|---|---|
| 2009 and earlier | `pre_2010` |
| 2010 to 2020 | `2010_2020` |
| 2021 to 2023 | `2021_2023` |
| 2024 and later | `2024_plus` |
| No constraint | `clean_split` (all four) |

For a range that crosses bands, pass a comma list, for example `--year-bands 2021_2023,2024_plus`.

### Hosted API commands

```bash
RUN=tasks/polars-dovmed-runs/mirusviricota-hosts-$(date +%Y%m%d)
mkdir -p "$RUN"
printf '%s\n' "papers describing hosts of Mirusviricota" > "$RUN/prompt.txt"
# Write and inspect "$RUN/query.json" before searching.

# bioRxiv discovery
timeout 90s uv run --script "$SKILL_DIR/scripts/query_literature.py" \
  --queries-file "$RUN/query.json" --corpus biorxiv --mode discovery \
  --extract-matches none --add-group-counts primary \
  --max-results 25 --details-rerank-limit 12 --poll-timeout 75 \
  --save-payload "$RUN/payload_biorxiv.json" --save-response "$RUN/results_biorxiv.json" \
  > "$RUN/summary_biorxiv.json" 2> "$RUN/time_biorxiv.txt"

# OpenPMC discovery over the four clean year bands
timeout 120s uv run --script "$SKILL_DIR/scripts/query_literature.py" \
  --queries-file "$RUN/query.json" --corpus pmc --mode discovery \
  --sync --year-bands clean_split --year-band-workers 4 --skip-details-rerank \
  --extract-matches none --add-group-counts primary \
  --max-results 25 --poll-timeout 120 \
  --save-payload "$RUN/payload_pmc.json" --save-response "$RUN/results_pmc.json" \
  > "$RUN/summary_pmc.json" 2> "$RUN/time_pmc.txt"

# Details for known PMCIDs (bioRxiv: pass DOIs with --corpus biorxiv),
# with bounded Crossref fill-in for missing DOI, year, or journal
uv run --script "$SKILL_DIR/scripts/query_literature.py" \
  --details PMC6362216 PMC10132079 --corpus pmc \
  --crossref-metadata --crossref-limit 10 \
  --save-payload "$RUN/payload_details.json" --save-response "$RUN/results_details.json"
```

### Local commands

```bash
uv run --script "$SKILL_DIR/scripts/query_literature.py" \
  --execution-mode local --corpus pmc \
  --local-parquet-pattern "$DOVMED_PMC_PARQUET" \
  --queries-file "$RUN/query.json" \
  --save-payload "$RUN/payload_local.json" --save-response "$RUN/results_local.json"
```

- `--corpus pmc` reads `DOVMED_PMC_PARQUET` and `--corpus biorxiv` reads `DOVMED_BIORXIV_PARQUET` unless `--local-parquet-pattern` is given. `--corpus both` needs one compatible explicit pattern; otherwise run separate scans.
- Local runs record `--corpus-revision` (or `DOVMED_CORPUS_REVISION`) and read `flattened.csv`, falling back to `processed.parquet` (or the legacy `prcoessed.parquet`) only when the compact output is absent. `--timeout` caps a local scan (default 900 seconds).

### Reachability and smoke check

`curl -sS --max-time 20 https://api.newlineages.com/` returns service metadata. It proves the service is reachable, not that a corpus scan works. The smoke check runs one bounded bioRxiv discovery and one details lookup:

```bash
uv run --script "$SKILL_DIR/scripts/smoke_test.py" --run-dir tasks/polars-dovmed-runs/smoke-test
```

Run either check before declaring an outage.

## Input Requirements

- A literature question, turned into an inspected `query.json`.
- A hosted API key or local parquet files for the requested corpus.
- A writable run directory outside `$SKILL_DIR`.

## Output

- `prompt.txt`, `query.json`, payload JSON, raw response JSON, timing files, and an optional curated summary in the run directory.
- A paper list with titles, identifiers, corpus, relevance notes, and timing.
- Warnings for timeouts, HTTP 502, `Database not found`, missing metadata, or fallback use.

## Quality Gates

- [ ] The API key stayed in the environment and appears in no artifact.
- [ ] The run directory is outside `$SKILL_DIR`.
- [ ] `query.json` was written anchor-first and inspected before the search.
- [ ] Each corpus ran as its own discovery call; OpenPMC used clean year bands with `--sync` and `--skip-details-rerank`, limited to the requested years.
- [ ] The flat endpoint, `--corpus both`, and unbanded OpenPMC scans were avoided, or the reason is stated.
- [ ] Every hosted call had a poll timeout and, where available, a wall-clock `timeout`.
- [ ] The first 5 to 10 hits were reviewed and noisy terms refined.
- [ ] Citation metadata came from corpus details, then bounded Crossref, not generic web search.
- [ ] Timings and failures are reported when speed is part of the request.

## Troubleshooting

**Issue**: `--corpus both` returns HTTP 502.
**Solution**: Run `--corpus biorxiv` and `--corpus pmc` separately and merge the results.

**Issue**: OpenPMC year-band search returns `Database not found`.
**Solution**: Report that the deployment does not expose the indexed OpenPMC bands. Do not fall back to an unbanded scan.

**Issue**: OpenPMC year-band search times out.
**Solution**: Report the timeout and keep the bioRxiv result. Narrow to the requested bands or refine the anchors; do not retry with longer waits or an unbanded scan.

**Issue**: A "topic of X" query returns generic topic papers.
**Solution**: Rerun with the entity and its aliases only, and use topic terms during triage.

**Issue**: Raw `urllib` requests get HTTP 403 with Cloudflare error 1010.
**Solution**: Cloudflare rejects Python's default user agent. Use the helper, or send both `X-API-Key` and a `User-Agent` header.

**Issue**: `/usr/bin/time` is missing.
**Solution**: Use shell `time -p` or record start and end timestamps.
