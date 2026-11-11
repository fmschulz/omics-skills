---
name: polars-dovmed
description: Run reproducible full-text searches of PMC Open Access and bioRxiv with polars-dovmed (saved query file, year bands, local parquet). Use when a literature search must be repeatable, or for a quick lookup through the hosted API.
user-invocable: true
---

# polars-dovmed

Search the PubMed Central Open Access (`pmc`) and bioRxiv (`biorxiv`) corpora through the hosted API or local parquet files.

**Connector or script.** The session may also have a `polars-dovmed` MCP connector (tools `search_literature`, `get_paper_full_text`) over the same hosted corpora. Use the connector for a quick lookup or to read one paper. Use this skill's script when the search must be reproducible (a saved query file and run directory), spans year bands, uses local parquet, or needs Crossref fill-in.

## Access

- Hosted API: the key is optional. Without `POLARS_DOVMED_API_KEY` the helper runs anonymously, and `/api/usage` reports the anonymous rate limit (`rate_limit: 120` on 2026-11-10). With a key, set it in the environment or in `~/.config/polars-dovmed/.env`; the helper then sends it as `X-API-Key`, and an invalid key fails with HTTP 403. Never pass the key in argv, and never write it to run directories, memory records, summaries or answers. Keys come from the service admin.
- Local corpora: see `references/commands.md`.
- Crossref contact address: pass `--crossref-email` only when the user gave an address for that purpose. Never take one from conversation, git config or system context. The helper reads no environment variable for it.
- Without a key or local corpora the helper uses the hosted API anonymously. If the API is unreachable or the anonymous rate limit is spent, say so and use another literature skill.

## Instructions

Run the helper as `uv run --script ~/.agents/skills/polars-dovmed/scripts/query_literature.py`. Commands, the smoke check and troubleshooting are in `references/commands.md`.

1. Create a run directory `tasks/polars-dovmed-runs/<date-topic>/` outside the skill directory. Save `prompt.txt`, `query.json`, payloads, raw responses, timing files and any curated summary there. Do not commit generated runs.
2. Write `query.json` (format below) and inspect it before searching: spelling, aliases, regex escaping, noisy terms.
   - Start anchor-only: exact entity names and evidence-based aliases. For "hosts of X" or "distribution and genomics of X", search X and its aliases and use the topic words for triage or a second pass. Never add generic words (distribution, genome, environment, host, taxonomy) as peer OR concepts.
   - Do not invent aliases by splitting compact taxon, gene or clade names.
   - Put acronym collisions and wrong systems in `disqualifying_terms`.
3. Run discovery first, one corpus per call. Never use `--corpus both`.
   - bioRxiv: async discovery, `--poll-timeout 75`, `--details-rerank-limit` 8 to 12.
   - OpenPMC: `--sync --year-bands <bands> --year-band-workers 4 --skip-details-rerank --poll-timeout 120`. Map the requested years to bands (table below) and search only those. Never run a broad unbanded OpenPMC scan. Fetch details by PMCID after inspecting the top hits.
   - Use `--extract-matches none --add-group-counts primary` for discovery. Wrap calls in `timeout` when it exists.
4. Inspect the first 5 to 10 hits. If they are noisy, refine `query.json` and rerun.
5. Fill citation metadata from the corpus details first, then `--crossref-metadata` or `/crossref-lookup`. Use DOI landing pages only when corpus metadata and Crossref disagree; do not use generic web search for DOI repair.
6. When speed matters, record wall time (`time -p` or `timeout`) and the helper's `elapsed_ms`. Report timeouts and failed endpoints as results.
7. Do not use the flat `/api/search_literature` endpoint. It needs `--allow-flat-query` and can hang behind the edge proxy.

### Query JSON

```json
{
  "anchor_entity": [["primary_name"], ["alias_1"], ["alias_2"]],
  "relation_or_property": [["primary_name", "relation_term"]],
  "disqualifying_terms": [["term_to_exclude"]]
}
```

Terms in one inner group are AND'd and must co-occur; inner groups in a concept are OR'd; concepts are OR'd, and items matching more groups rank higher. List each synonym as its own single-term group; use a multi-term group only to require co-occurrence.

Multi-word terms, by path:

- Verified in `query_literature.py`: the helper sends the terms unchanged to the hosted API and to the upstream `dovmed scan`. It does not turn a term into a phrase. When it extracts match contexts itself, it treats each term as a case-insensitive regular expression (a literal match if the regex is invalid), so a multi-word term then matches its words in that order with that spacing.
- Per the service notes (hosted connector): the hosted index has no phrase operator, quotation marks are stripped, and the words of one alternative are AND'd. Only the fallback scan matches a quoted term literally. Write bare words, and expect a multi-word term to match papers that contain all its words, not only the exact phrase.
- Not verified here: how the upstream local scan treats a multi-word term. Check the first hits before relying on phrase matching.

Rank hits in this order: anchor in title, anchor in abstract, anchor plus support term in title or abstract, several distinct group matches, full-text-only matches. Down-rank hits that match only generic support terms.

### Year bands (OpenPMC)

| Requested years | `--year-bands` value |
|---|---|
| 2009 and earlier | `pre_2010` |
| 2010 to 2020 | `2010_2020` |
| 2021 to 2023 | `2021_2023` |
| 2024 and later | `2024_plus` |
| No constraint | `clean_split` (all four) |

For a range that crosses bands, pass a comma list, for example `--year-bands 2021_2023,2024_plus` (the helper runs one call per band). The connector takes one band per call.

## Input Requirements

A literature question turned into an inspected `query.json`, network access to the hosted API (a key is optional) or local parquet files, and a writable run directory.

## Output

The run directory files, plus a paper list with titles, identifiers, corpus, relevance notes and timing. Warn about timeouts, HTTP 502, `Database not found`, missing metadata and fallback use.

## Quality Gates

- The key appears in no artifact.
- Each corpus ran as its own call; OpenPMC used only the requested year bands with `--sync` and `--skip-details-rerank`.
- The first 5 to 10 hits were reviewed before the list was reported.
