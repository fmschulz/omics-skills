---
name: polars-dovmed
description: Search the PMC Open Access literature with polars-dovmed. Prefer dovmed create-patterns to build structured JSON queries, then use the hosted API when an API key is available or fall back to local dovmed scan over parquet files.
user-invocable: true
---

# polars-dovmed

Search the PubMed Central Open Access subset with `polars-dovmed`.

The preferred workflow is always:
1. use the vendored `create_patterns.py` helper to mirror upstream `dovmed create-patterns` and turn the research question into structured query JSON
2. inspect and refine the generated JSON
3. run structured discovery first
4. fetch paper details for candidate PMC IDs
5. use structured advanced scans only for final refinement when needed

Search execution has two modes:
- Preferred when available: hosted API over the formatted parquet database
- Fallback: local `dovmed scan` over local parquet files

Do not skip the structured-query generation step unless the user explicitly supplies a ready query JSON file and asks to use it as-is.

For every search prompt, create a dedicated run directory and save:
- the original prompt text
- the generated query JSON
- the exact LLM request payload used to generate the query JSON
- the exact payload submitted to the API or local scan
- the raw results returned
- any curated summary derived from those results
- if discovery fallback is used, save separate discovery payload and result artifacts

## Instructions

1. Decide execution mode up front.
   - Check API availability first.
   - If `POLARS_DOVMED_API_KEY` is available in the environment, in the configured polars-dovmed env file, or the user provides an API key, use the hosted API.
   - Only fall back to local `dovmed` CLI plus local parquet files if API mode is unavailable.
2. Start by generating a structured query JSON with `dovmed create-patterns`.
   - Treat this as the default and preferred way of searching.
   - This step creates the valid JSON format for pattern search.
   - In this skill, use `python skills/polars-dovmed/scripts/create_patterns.py ...` because it vendors the upstream `create-patterns` behavior directly into the skill directory.
   - The helper auto-loads `~/.config/polars-dovmed/.env` if present.
   - If the user already gave a query JSON, inspect it before use.
3. Create a dedicated run directory before searching.
   - Use a slug based on the prompt or topic.
   - Save the original prompt text there as `prompt.txt`.
   - Save the generated or supplied query JSON there.
4. Review the generated JSON before searching.
   - Check that concept groups match the biological question.
   - Remove or tighten noisy groups.
   - Add `disqualifying_terms` if obvious acronym or taxonomy collisions exist.
   - Be especially careful with short isolate names or generic tokens. Tighten them with whole-word boundaries, replace them with fuller names, or remove them if they introduce obvious ambiguity.
5. Run the search.
   - API mode: read the query JSON and send its contents in the JSON request body under `primary_queries`. Do not upload the file itself.
   - Local mode: run `dovmed scan` against the local parquet files using the JSON query file.
   - Save the exact submitted payload in the run directory before sending the request.
   - Save the raw returned results in the run directory immediately after the search completes.
   - Default structured API path:
     - `discover_literature` or `scan_literature_advanced(mode="discovery")`
     - `get_paper_details(pmc_ids=[...])`
     - `scan_literature_advanced(mode="advanced")` only for final refinement
   - If advanced refinement is too slow or too noisy, return to discovery-plus-details rather than forcing repeated heavy scans.
   - Save discovery artifacts separately rather than overwriting the structured advanced artifacts.
6. Inspect the first results before trusting the full set.
   - For targeted questions, review the first 5-10 titles.
   - If results are noisy, refine the JSON and rerun instead of widening free-text queries.
7. If the user needs citation-quality output, verify missing metadata in PubMed or PMC before finalizing.

## Preferred Workflow

### Step 1: Generate Query JSON

Always start here unless the user already provided a query JSON file.

```bash
python skills/polars-dovmed/scripts/create_patterns.py \
  --input-text "native hosts of Klosneuviruses" \
  --output-file queries/klosneuvirus_hosts.json \
  --save-payload runs/klosneuvirinae-hosts/llm_payload.json \
  --save-raw-response runs/klosneuvirinae-hosts/llm_response.txt
```

This helper mirrors the upstream `dovmed create-patterns` step and uses the prompt template shipped with this skill:
- `skills/polars-dovmed/scripts/create_patterns.py`
- `skills/polars-dovmed/prompts/pattern_groups_query.txt`

### Step 2: Inspect And Refine

The generated JSON is the main search artifact. Review it before running the search.

Expected structure:

```json
{
  "concept_group_1": [
    ["pattern_1"],
    ["pattern_2"]
  ],
  "concept_group_2": [
    ["pattern_a", "pattern_b"]
  ],
  "disqualifying_terms": [
    ["term_to_exclude"]
  ]
}
```

Interpretation:
- outer keys are concept groups
- each inner list is a grouped pattern set
- use `disqualifying_terms` to suppress known false positives

### Step 2.5: Create A Run Directory

Create a directory for each prompt, for example:

```bash
mkdir -p runs/klosneuvirinae-hosts
printf '%s\n' "find papers that describe hosts of Klosneuvirinae" > runs/klosneuvirinae-hosts/prompt.txt
cp queries/klosneuvirus_hosts.json runs/klosneuvirinae-hosts/query.json
```

This is mandatory. Every run should preserve the input prompt, structured query, submitted payload, raw results, and ideally the raw LLM response used to create the query JSON.

### Step 3A: Search With Hosted API

Use this mode when `POLARS_DOVMED_API_KEY` is available or provided by the user.

This repository includes `scripts/query_literature.py` as a convenience wrapper for the hosted parquet-backed API.

Recommended API workflow:
1. generate query JSON with `python skills/polars-dovmed/scripts/create_patterns.py ...`
2. inspect the JSON
3. run `POST /api/discover_literature` or `POST /api/scan_literature_advanced` with `mode="discovery"`
4. inspect top hits and collect candidate `pmc_id` values
5. run `POST /api/get_paper_details` with `pmc_ids`
6. if needed, run `POST /api/scan_literature_advanced` with `mode="advanced"` for final structured refinement

Use discovery mode first for candidate retrieval. Use advanced mode only for final structured refinement.

The query JSON is the source of truth for API mode.
- In local mode, the JSON file is passed directly to `dovmed scan`.
- In API mode, the agent should read the JSON file and serialize its contents into the API request body as `primary_queries`.
- Do not bypass the structured-query generation step and jump straight to improvised free-text queries unless the user explicitly asks for a quick exploratory search.
- Save the exact API payload to the run directory as a JSON file before submitting it.
- Save the raw API response to the run directory as a JSON file after the request returns.
- If discovery fallback is used, save it separately as `payload_discovery.json` and `results_discovery.json`.
- The helper auto-loads `~/.config/polars-dovmed/.env`, so a configured `POLARS_DOVMED_API_KEY` does not need manual `source` in typical agent runs.
- For hard cases, prefer this sequence:
  - structured query
  - discovery mode
  - paper-details lookup
  - advanced scan only if needed
  - curated PMC verification

### Step 3B: Search Locally With dovmed scan

Use this mode when no hosted API key is available.

```bash
dovmed scan \
  --parquet-pattern "data/pubmed_central/parquet_files/*/*.parquet" \
  --queries-file queries/klosneuvirus_hosts.json \
  --extract-matches primary \
  --add-group-counts primary \
  --output-path results/klosneuvirus_hosts \
  --verbose
```

For more specific searches, use secondary queries:

```bash
dovmed scan \
  --parquet-pattern "data/pubmed_central/parquet_files/*/*.parquet" \
  --queries-file queries/primary.json \
  --secondary-queries-file queries/secondary.json \
  --extract-matches both \
  --add-group-counts both \
  --output-path results/literature_scan \
  --verbose
```

## Quick Reference

| Task | Action |
|------|--------|
| Preferred first step | `dovmed create-patterns` |
| Vendored helper for agents | `python skills/polars-dovmed/scripts/create_patterns.py ...` |
| Search artifact | Query JSON file |
| Preferred execution when key exists | Hosted API |
| Fallback execution | `dovmed scan` on local parquet files |
| Execution-order rule | Check API first, local fallback second |
| Local dataset requirement | PMC OA parquet files |
| Helper wrapper in this repo | `skills/polars-dovmed/scripts/query_literature.py` |
| Preferred candidate endpoint | `POST /api/discover_literature` |
| Structured API endpoint | `POST /api/scan_literature_advanced` |
| Paper details endpoint | `POST /api/get_paper_details` with `pmc_ids` |
| Required run artifacts | `prompt.txt`, `query.json`, `payload.json`, `results.json`, optional summary |
| Recommended extra artifacts | `llm_payload.json`, `llm_response.txt`, refined query variants, `payload_discovery.json`, `results_discovery.json` |

## Input Requirements

- Research question or topic description
- Either:
  - hosted API key via `POLARS_DOVMED_API_KEY`, or
  - local parquet files plus local `dovmed` installation
- Optional existing query JSON
- Optional year or metadata requirements for post-search verification
- A writable directory for run artifacts

## Search Semantics

- Prefer structured JSON over ad hoc natural-language search strings.
- `create_patterns.py` is used to generate the valid structured JSON format for search and mirrors upstream `dovmed create-patterns`.
- The helper auto-loads `~/.config/polars-dovmed/.env` so configured API keys are picked up without extra shell setup.
- Refine concept groups instead of repeatedly retrying loose text searches.
- Use narrow biological names first, then expand with synonyms or alternate taxonomy names.
- Use `disqualifying_terms` when collisions are predictable.
- Avoid short ambiguous names unless they are tightly bounded and clearly necessary.
- For complex questions, prefer multiple concept groups instead of one long flat phrase.
- If grouped concepts matter, preserve that grouping in both API payloads and local query JSON.

## Local Workflow Notes

- Upstream `polars-dovmed` is built around local parquet scanning.
- Local search requires:
  - `dovmed download`
  - `dovmed build-parquet`
  - `dovmed create-patterns`
  - `dovmed scan`
- If the local corpus is not available, do not pretend the local workflow is runnable.
  - Either switch to hosted API mode or state that local parquet files are missing.
- Save the local scan inputs and raw outputs into the run directory as well.

Agent note:
- In this repository, do not assume `dovmed` is installed.
- Use `skills/polars-dovmed/scripts/create_patterns.py` to create the structured JSON if the CLI is unavailable.
- That helper is included specifically so agents can still follow the upstream workflow.

## API Workflow Notes

- The hosted API is a convenience layer over the formatted parquet database.
- Prefer it when a key is available because it avoids rebuilding or hosting the local corpus.
- Check for API availability before looking for a local checkout or local parquet setup.
- Still begin with the structured-query generation step and query JSON.
- The query JSON is not just a note or scratch artifact.
  - It defines the structured search intent.
  - The API request should be built from that JSON.
  - For structured searches, send it as `primary_queries` to `POST /api/scan_literature_advanced`.
- Authentication is via `X-API-Key`.
- Structured query files are not uploaded to the API.
- `POST /api/get_paper_details` expects `pmc_ids`, not `paper_ids`.
- For debugging or triage, include `add_group_counts: "primary"` and inspect returned `_group_*_count` fields.
- Discovery mode is the fast candidate-first path and should be the default for agents.
- Advanced grouped scans may still be slow and are for final structured refinement, not first-pass discovery.
- If an advanced scan stalls, times out, or returns diffuse results, go back to discovery mode and paper-details lookup.
- Do not jump directly to improvised free-text queries unless the user explicitly wants a quick exploratory lookup.

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

Send this to either:
- `POST /api/discover_literature`
- or `POST /api/scan_literature_advanced`

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

- Curated paper lists with titles and identifiers
- Match snippets or extracted terms when requested
- Query JSON files used for the search
- Saved run artifacts for reproducibility
- Notes on noisy concepts, exclusions, and refinements
- Warnings about incomplete citation metadata or likely indexing gaps

## Quality Gates

- [ ] Execution mode chosen correctly: API when key exists, local otherwise
- [ ] API availability checked before local fallback assumptions
- [ ] Structured query file created first with `create_patterns.py` or an explicit user-supplied JSON
- [ ] Dedicated run directory created for the prompt
- [ ] `prompt.txt`, `query.json`, `payload.json`, raw results, and ideally `llm_payload.json` plus `llm_response.txt` saved
- [ ] Query JSON inspected before search
- [ ] First 5-10 results reviewed before trusting the result set
- [ ] Noisy concept groups refined instead of widening free-text queries blindly
- [ ] Discovery mode used before paper-details lookup and advanced refinement
- [ ] Discovery fallback artifacts saved separately if used
- [ ] Missing citation metadata verified in PubMed or PMC when needed
- [ ] Final answer states whether results came from hosted API or local parquet scan

## Examples

### Example 1: Preferred API-backed workflow

```bash
python skills/polars-dovmed/scripts/create_patterns.py \
  --input-text "native hosts of Klosneuviruses" \
  --output-file runs/klosneuvirinae-hosts/query.json \
  --save-payload runs/klosneuvirinae-hosts/llm_payload.json \
  --save-raw-response runs/klosneuvirinae-hosts/llm_response.txt

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

### Example 2: Preferred local workflow

```bash
python skills/polars-dovmed/scripts/create_patterns.py \
  --input-text "native hosts of Klosneuviruses" \
  --output-file runs/klosneuvirinae-hosts/query.json \
  --save-payload runs/klosneuvirinae-hosts/llm_payload.json \
  --save-raw-response runs/klosneuvirinae-hosts/llm_response.txt

dovmed scan \
  --parquet-pattern "data/pubmed_central/parquet_files/*/*.parquet" \
  --queries-file runs/klosneuvirinae-hosts/query.json \
  --extract-matches primary \
  --add-group-counts primary \
  --output-path results/klosneuvirus_hosts \
  --verbose
```

### Example 3: Use an existing query JSON as-is

If the user provides a ready JSON file and asks not to regenerate it:

```bash
dovmed scan \
  --parquet-pattern "data/pubmed_central/parquet_files/*/*.parquet" \
  --queries-file queries/user_supplied.json \
  --output-path results/user_query \
  --verbose
```

## Troubleshooting

**Issue**: Hosted API key is missing  
**Solution**: Fall back to local `dovmed scan` if local parquet files exist.

**Issue**: Local parquet files are missing  
**Solution**: Use hosted API mode if a key is available, otherwise state that the local corpus must be prepared first.

**Issue**: `create-patterns` generated noisy concepts  
**Solution**: Edit the JSON manually, tighten taxonomy names, and add `disqualifying_terms`.

**Issue**: Search returns too many generic hits  
**Solution**: Refine the query JSON rather than broadening the free-text query.

**Issue**: Citation fields are incomplete  
**Solution**: Verify in PubMed or PMC before final output.
