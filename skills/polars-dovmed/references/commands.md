# polars-dovmed commands

`SKILL_DIR=~/.agents/skills/polars-dovmed`. Run the helper as `uv run --script "$SKILL_DIR/scripts/query_literature.py"` so its dependency is available. It loads `~/.config/polars-dovmed/.env`. Write generated files to a run directory outside `$SKILL_DIR`.

## Hosted API

```bash
SKILL_DIR=~/.agents/skills/polars-dovmed
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

# OpenPMC discovery over the four clean year bands (year-band discovery is synchronous)
timeout 120s uv run --script "$SKILL_DIR/scripts/query_literature.py" \
  --queries-file "$RUN/query.json" --corpus pmc --mode discovery \
  --year-bands clean_split --year-band-workers 4 --skip-details-rerank \
  --extract-matches none --add-group-counts primary \
  --max-results 25 --poll-timeout 120 \
  --save-payload "$RUN/payload_pmc.json" --save-response "$RUN/results_pmc.json" \
  > "$RUN/summary_pmc.json" 2> "$RUN/time_pmc.txt"

# Details for known PMCIDs (bioRxiv: pass DOIs with --corpus biorxiv),
# with bounded Crossref fill-in for missing DOI, year, or journal.
# Add --crossref-email ADDRESS only when the user gave one for this purpose.
uv run --script "$SKILL_DIR/scripts/query_literature.py" \
  --details PMC6362216 PMC10132079 --corpus pmc \
  --crossref-metadata --crossref-limit 10 \
  --save-payload "$RUN/payload_details.json" --save-response "$RUN/results_details.json"
```

## Local parquet

```bash
uv run --script "$SKILL_DIR/scripts/query_literature.py" \
  --execution-mode local --corpus pmc \
  --local-parquet-pattern "$DOVMED_PMC_PARQUET" \
  --queries-file "$RUN/query.json" \
  --save-payload "$RUN/payload_local.json" --save-response "$RUN/results_local.json"
```

- Local mode runs `pixi run dovmed scan` inside a polars-dovmed checkout given by `--local-repo-dir` (default `~/dev/polars-dovmed`); a missing directory stops the run with a clear message.
- With no API key, `--execution-mode auto` uses the hosted API anonymously unless `--local-parquet-pattern` or the corpus variable is set.
- `--corpus pmc` reads `DOVMED_PMC_PARQUET` and `--corpus biorxiv` reads `DOVMED_BIORXIV_PARQUET` unless `--local-parquet-pattern` is given. Run one scan per corpus.
- Local runs record `--corpus-revision` (or `DOVMED_CORPUS_REVISION`) and read `flattened.csv`, falling back to `processed.parquet` (or the legacy `prcoessed.parquet`) only when the compact output is absent. `--timeout` caps a local scan (default 900 seconds).
- Local corpora come from upstream `dovmed download`, `dovmed build-parquet` and `dovmed scan` (<https://github.com/UriNeri/polars-dovmed>). The pack ships neither an API key nor the corpora.

## Reachability and smoke check

`curl -sS --max-time 20 https://api.newlineages.com/` returns service metadata. It proves the service is reachable, not that a corpus scan works. The smoke check runs one bounded bioRxiv discovery and one details lookup:

```bash
uv run --script "$SKILL_DIR/scripts/smoke_test.py" --run-dir tasks/polars-dovmed-runs/smoke-test
```

Run either check before declaring an outage.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `--corpus both` is rejected (the API answers HTTP 502) | Run `--corpus biorxiv` and `--corpus pmc` separately and merge the results. |
| A run pauses without output | Without a key the helper waits for a free slot of its 20 requests per minute. Set `POLARS_DOVMED_API_KEY` to lift the client limit. |
| OpenPMC year-band search returns `Database not found` | Report that the deployment does not expose the indexed OpenPMC bands. Do not fall back to an unbanded scan. |
| OpenPMC year-band search times out | Report the timeout and keep the bioRxiv result. Narrow to the requested bands or refine the anchors; do not retry with longer waits or an unbanded scan. |
| A "topic of X" query returns generic topic papers | Rerun with the entity and its aliases only; use topic terms during triage. |
| Raw `urllib` requests get HTTP 403 with Cloudflare error 1010 | Cloudflare rejects Python's default user agent. Use the helper, or send both `X-API-Key` and a `User-Agent` header. |
| `/usr/bin/time` is missing | Use shell `time -p` or record start and end timestamps. |
