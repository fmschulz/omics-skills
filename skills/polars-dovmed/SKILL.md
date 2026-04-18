---
name: polars-dovmed
description: Search the PMC Open Access literature with polars-dovmed. Author structured JSON queries directly, then use the hosted API when an API key is available or fall back to local dovmed scan over PMC, bioRxiv, or both parquet corpora.
user-invocable: true
---

# polars-dovmed

Search the PubMed Central Open Access subset and the local bioRxiv parquet corpus with `polars-dovmed`.

The preferred workflow is always:
1. decide execution mode up front
2. author a structured query JSON directly
3. inspect and refine the query JSON
4. run structured discovery first
5. fetch paper details for candidate PMC IDs
6. use structured advanced scans only for final refinement when needed

Search execution has two modes:
- Preferred when available: hosted API over the formatted PMC/OpenPMC parquet database
- Fallback: local `dovmed scan` over local parquet files for `pmc`, `biorxiv`, or `both`

Do not skip the structured-query authoring step unless the user explicitly supplies a ready query JSON file and asks to use it as-is.

For every search prompt, create a dedicated run directory and save:
- the original prompt text
- the authored or supplied query JSON
- the exact payload submitted to the API or local scan
- the raw results returned
- any curated summary derived from those results
- if discovery fallback is used, separate discovery payload and result artifacts

## Instructions

1. Decide execution mode up front.
   - Check API availability first.
   - If `POLARS_DOVMED_API_KEY` is available in the environment, in the configured polars-dovmed env file, or the user provides an API key, use the hosted API for PMC/OpenPMC searches.
   - Use local `dovmed` CLI plus local parquet files whenever the user explicitly wants bioRxiv, a PMC+bioRxiv combined scan, or there is no hosted API key.
2. Author a structured query JSON directly.
   - The agent should write the JSON itself instead of calling another helper to generate it.
   - If the user already gave a query JSON, inspect it before use.
3. Create a dedicated run directory before searching.
   - Use a slug based on the prompt or topic.
   - Save the original prompt text there as `prompt.txt`.
   - Save the authored or supplied query JSON there as `query.json`.
4. Review the query JSON before searching.
   - Check that concept groups match the biological question.
   - Remove or tighten noisy groups.
   - Add `disqualifying_terms` if obvious acronym or taxonomy collisions exist.
   - Be especially careful with short isolate names or generic tokens.
5. Run the search.
   - API mode: read the query JSON and send its contents in the JSON request body under `primary_queries`. Do not upload the file itself.
   - Local mode: run `dovmed scan` against the local parquet files using the JSON query file.
   - Save the exact submitted payload in the run directory before sending it.
   - Save the raw returned results in the run directory immediately after the search completes.
   - Default structured API path:
     - `scan_literature_advanced(mode="discovery")`
     - `get_paper_details(pmc_ids=[...])`
     - `scan_literature_advanced(mode="advanced")` only for final refinement
   - If advanced refinement is too slow or too noisy, return to discovery-plus-details rather than forcing repeated heavy scans.
6. Inspect the first results before trusting the full set.
   - For targeted questions, review the first 5-10 titles.
   - If results are noisy, refine the JSON and rerun instead of widening free-text queries.
7. If the user needs citation-quality output, verify missing metadata in PubMed or PMC before finalizing.

## Preferred Workflow

### Step 1: Author Query JSON Directly

Always start here unless the user already provided a query JSON file.

Use this structure:

```json
{
  "anchor_entity": [
    ["primary_name"],
    ["alias_1"],
    ["alias_2"]
  ],
  "relation_or_property": [
    ["primary_name", "relation_term"],
    ["alias_1", "relation_term"],
    ["primary_name", "specific_relation_alias"]
  ],
  "disqualifying_terms": [
    ["term_to_exclude"]
  ]
}
```

Interpretation:
- outer keys are concept groups
- each inner list is an AND-group of patterns
- separate inner lists inside the same key are OR alternatives
- `disqualifying_terms` suppresses known false positives

### Query Authoring Rules

- Build searches around anchor concepts first.
- Use explicit biological names over generic role words.
- Treat support concepts as refiners, not anchors.
- Keep relation terms soft in discovery unless they are essential to relevance.
- Use `disqualifying_terms` aggressively for acronym collisions or wrong systems.
- Prefer direct JSON authoring over verbose natural-language planning.

### Quick Templates

Anchor plus relation:

```json
{
  "anchor_entity": [
    ["entity_name"],
    ["entity_alias"]
  ],
  "relation_or_property": [
    ["entity_name", "relation_term"],
    ["entity_alias", "relation_term"]
  ]
}
```

Anchor-only high-recall discovery:

```json
{
  "anchor_entity": [
    ["entity_name"],
    ["entity_alias_1"],
    ["entity_alias_2"]
  ]
}
```

Example: `"hosts of Klosneuvirinae"`

```json
{
  "anchor_klosneuvirinae": [
    ["klosneuvirinae"],
    ["klosneuvirus"]
  ],
  "host_relation": [
    ["klosneuvirinae", "host"],
    ["klosneuvirus", "infect"]
  ]
}
```

Example: `"Mirusviricota and the eukaryotic nucleus"`

```json
{
  "anchor_mirusviricota": [
    ["mirusviricota"],
    ["mirusvirus"],
    ["mirusviruses"]
  ],
  "nucleus_association": [
    ["mirusviricota", "eukaryotic", "nucleus"],
    ["mirusvirus", "nuclear"],
    ["mirusviruses", "nucleus"]
  ]
}
```

### Step 2: Create A Run Directory

Create a directory for each prompt, for example:

```bash
mkdir -p runs/klosneuvirinae-hosts
printf '%s\n' "find papers that describe hosts of Klosneuvirinae" > runs/klosneuvirinae-hosts/prompt.txt
cp queries/klosneuvirus_hosts.json runs/klosneuvirinae-hosts/query.json
```

This is mandatory. Every run should preserve the input prompt, structured query, submitted payload, raw results, and a curated summary.

### Step 3A: Search With Hosted API

Use this mode when `POLARS_DOVMED_API_KEY` is available or provided by the user.

This repository includes `scripts/query_literature.py` as a convenience wrapper for the hosted parquet-backed API.

Recommended API workflow:
1. author `query.json`
2. inspect the JSON
3. run `POST /api/scan_literature_advanced` with `mode="discovery"`
4. inspect top hits and collect candidate `pmc_id` values
5. run `POST /api/get_paper_details` with `pmc_ids`
6. if needed, run `POST /api/scan_literature_advanced` with `mode="advanced"` for final structured refinement

Use discovery mode first for candidate retrieval. Use advanced mode only for final structured refinement.

The query JSON is the source of truth for API mode.
- In local mode, the JSON file is passed directly to `dovmed scan`.
- In API mode, the agent should read the JSON file and serialize its contents into the API request body as `primary_queries`.
- Do not bypass the structured-query authoring step and jump straight to improvised free-text queries unless the user explicitly asks for a quick exploratory search.
- `scripts/query_literature.py --query ...` is explicit opt-in only and requires `--allow-flat-query`.
- Save the exact API payload to the run directory as a JSON file before submitting it.
- Save the raw API response to the run directory as a JSON file after the request returns.
- If discovery fallback is used, save it separately as `payload_discovery.json` and `results_discovery.json`.
- The helper auto-loads `~/.config/polars-dovmed/.env`, so a configured `POLARS_DOVMED_API_KEY` does not need manual `source` in typical agent runs.
- The helper submits hosted search work through `/api/jobs` and polls for completion, instead of holding one long edge request open.
- For structured discovery runs, the helper automatically fetches details for the top candidate PMC IDs and reranks them using grouped query evidence before summarizing results.

Example:

```bash
python skills/polars-dovmed/scripts/query_literature.py \
  --queries-file runs/klosneuvirinae-hosts/query.json \
  --mode discovery \
  --extract-matches none \
  --add-group-counts primary \
  --max-results 25 \
  --save-payload runs/klosneuvirinae-hosts/payload_discovery.json \
  --save-response runs/klosneuvirinae-hosts/results_discovery.json

python skills/polars-dovmed/scripts/query_literature.py \
  --details PMC6912108 PMC8490762 PMC5871332 \
  --save-payload runs/klosneuvirinae-hosts/payload_details.json \
  --save-response runs/klosneuvirinae-hosts/results_details.json
```

### Step 3B: Search Locally With dovmed scan

Use this mode when no hosted API key is available, or when the user explicitly wants the local bioRxiv parquet corpus.

```bash
dovmed scan \
  --corpus pmc \
  --queries-file runs/klosneuvirinae-hosts/query.json \
  --extract-matches primary \
  --add-group-counts primary \
  --output-path results/klosneuvirus_hosts \
  --verbose
```

Local corpus aliases on this workstation:
- `--corpus pmc`: `~/dev/polars-dovmed/data/pubmed_central/parquet_files/*/*.parquet`
- `--corpus biorxiv`: `/mnt/taskmaster2/biorxiv/parquet/latest/*.parquet`
- `--corpus both`: both corpora in one scan

Examples:

```bash
dovmed scan \
  --corpus biorxiv \
  --queries-file runs/mirusvirus/query.json \
  --extract-matches primary \
  --add-group-counts primary \
  --output-path results/mirusvirus_biorxiv \
  --verbose

dovmed scan \
  --corpus both \
  --queries-file runs/mirusvirus/query.json \
  --extract-matches primary \
  --add-group-counts primary \
  --output-path results/mirusvirus_pmc_plus_biorxiv \
  --verbose
```

The helper wrapper also supports local execution directly:

```bash
python skills/polars-dovmed/scripts/query_literature.py \
  --execution-mode local \
  --local-corpus biorxiv \
  --queries-file runs/mirusvirus/query.json \
  --save-payload runs/mirusvirus/payload_local.json \
  --save-response runs/mirusvirus/results_local.json
```

Use `--local-corpus both` to scan PMC plus bioRxiv in one pass.

## Search Semantics

- Prefer structured JSON over ad hoc natural-language search strings.
- For complex questions, prefer multiple concept groups instead of one long flat phrase.
- If grouped concepts matter, preserve that grouping in both API payloads and local query JSON.

### Retrieval Quality Playbook

- Build searches around anchor concepts first.
- Treat support concepts as refiners, not anchors.
- Prefer explicit biological names over generic role words.
- Put alternate names and spelling variants inside the same concept group.
- Use `disqualifying_terms` for acronym collisions, wrong clades, and predictable false positives.

### Hit Ranking Guidance

Rank hits in this order:
1. exact anchor-name hit in the title
2. exact anchor-name hit in the abstract
3. anchor plus support co-occurrence in title or abstract
4. multiple distinct relevant group matches
5. full-text-only matches last

Down-rank or discard:
- papers matching only generic support terms
- papers with no anchor-name evidence in title or abstract
- papers clearly centered on the wrong clade, host, or system
- papers whose relevance depends only on a broad background mention

### Recall-First Principle

- When the key evidence may only appear in full text, prefer higher recall over early precision.
- Use discovery mode first.
- Fetch details for the best candidate PMC IDs.
- Only tighten with advanced grouped refinement if needed.

### Retrieval Loop

1. author structured JSON
2. run discovery mode
3. review the first 5-10 titles
4. fetch paper details for the most relevant PMC IDs
5. refine the query JSON
6. run advanced mode only if discovery plus details is not enough

### "X Of Y" Query Construction

For requests shaped like:
- `"hosts of X"`
- `"symbionts of Y"`
- `"pathways in Z"`
- `"genes involved in W"`

do not represent the query as loose top-level concepts like:
- `X`
- `host`
- `symbiont`
- `pathway`

Instead:
1. identify the entity anchor
2. identify the relation or property term
3. build OR-of-AND groups that combine them inside the same pattern group

## Quick Smoke Test

Use this to verify that the API-backed discovery path, paper-details lookup, saved payloads, saved responses, and expected output shape are all working before a real run.

Run:

```bash
python skills/polars-dovmed/scripts/smoke_test.py
```

Default artifact directory:

```bash
skills/polars-dovmed/runs/smoke-test/
```

Expected success indicators in `summary.json`:
- `success: true`
- discovery result has:
  - `mode: "discovery"`
  - `strategy_used`
  - `elapsed_ms`
  - at least one paper
  - per-paper `ranking`
- details result has:
  - `found >= 1`
  - `normalized_pmc_ids`
  - empty `missing_ids` for the known test PMC

## Quick Reference

| Task | Action |
|------|--------|
| Preferred first step | author `query.json` directly |
| Search artifact | Query JSON file |
| Preferred execution when key exists | Hosted API |
| Fallback execution | `dovmed scan` on local parquet files |
| Execution-order rule | Check API first, local fallback second |
| Local dataset requirement | PMC OA parquet files |
| Helper wrapper in this repo | `skills/polars-dovmed/scripts/query_literature.py` |
| Preferred candidate endpoint | `POST /api/scan_literature_advanced` with `mode="discovery"` |
| Structured API endpoint | `POST /api/scan_literature_advanced` |
| Flat exploratory endpoint | `POST /api/search_literature` only with explicit opt-in |
| Automatic second pass | discovery -> paper details -> grouped rerank |
| Paper details endpoint | `POST /api/get_paper_details` with `pmc_ids` |
| Required run artifacts | `prompt.txt`, `query.json`, `payload.json`, `results.json`, optional summary |
| Quick skill verification | `python skills/polars-dovmed/scripts/smoke_test.py` |

## Confirmed API Contract

### Structured Advanced Search

Use:

```json
{
  "primary_queries": {
    "concept_a": [["pattern1"], ["pattern2"]],
    "concept_b": [["pattern3"]]
  },
  "search_columns": ["title", "abstract_text", "full_text"],
  "extract_matches": "none",
  "add_group_counts": "primary",
  "max_results": 5
}
```

Send this to:
- `POST /api/scan_literature_advanced`
- header: `X-API-Key: ...`

### Structured Discovery Search

Use the same structured request body but set:

```json
{
  "mode": "discovery"
}
```

### Paper Details

Use:

```json
{
  "pmc_ids": ["PMC1234567"]
}
```

Send this to:
- `POST /api/get_paper_details`

Do not use `paper_ids`.

## Output

- curated paper lists with titles and identifiers
- query JSON files used for the search
- saved run artifacts for reproducibility
- notes on noisy concepts, exclusions, and refinements
- warnings about incomplete citation metadata or likely indexing gaps

## Quality Gates

- [ ] execution mode chosen correctly: API when key exists, local otherwise
- [ ] API availability checked before local fallback assumptions
- [ ] structured query file authored first or user-supplied
- [ ] dedicated run directory created for the prompt
- [ ] `prompt.txt`, `query.json`, `payload.json`, raw results, and summary saved
- [ ] query JSON inspected before search
- [ ] first 5-10 results reviewed before trusting the result set
- [ ] noisy concept groups refined instead of widening free-text queries blindly
- [ ] discovery mode used before paper-details lookup and advanced refinement
- [ ] discovery fallback artifacts saved separately if used
- [ ] missing citation metadata verified in PubMed or PMC when needed
- [ ] final answer states whether results came from hosted API or local parquet scan

## Troubleshooting

**Issue**: Hosted API key is missing  
**Solution**: Fall back to local `dovmed scan` if local parquet files exist.

**Issue**: Local parquet files are missing  
**Solution**: Use hosted API mode if a key is available, otherwise state that the local corpus must be prepared first.

**Issue**: Authored query JSON is noisy  
**Solution**: Tighten anchor terms, remove generic support groups, and add `disqualifying_terms`.

**Issue**: Search returns too many generic hits  
**Solution**: Refine the query JSON rather than broadening the free-text query.

**Issue**: Citation fields are incomplete  
**Solution**: Verify in PubMed or PMC before final output.
