---
name: polars-dovmed
description: Search 2.4M+ full-text PubMed Central Open Access papers for literature reviews, trend scans, and structured host-microbe literature queries.
user-invocable: true
---

# polars-dovmed

Search across 2.4M+ PMC Open Access papers for literature discovery and extraction tasks.

## Instructions

1. Load the API key from a secure location.
2. Pick the endpoint based on query shape:
   - Use `/api/search_literature` for one concept, a quoted phrase, or a flat synonym query.
   - Use `/api/scan_literature_advanced` when you need precise multi-concept logic such as host + symbiont, organism + pathway, or explicit concept grouping.
   - Use `/api/get_paper_details` once you have candidate PMC IDs.
3. Start with exact taxa or core terms, then broaden with explicit `OR` synonyms.
4. Inspect the first 5-10 returned titles before trusting the result set.
5. If the user needs a specific recent year or complete citation fields, verify missing metadata in PubMed or PMC before finalizing the answer.

## Quick Reference

| Task | Action |
|------|--------|
| API key | `POLARS_DOVMED_API_KEY` in env or `~/.config/polars-dovmed/.env` |
| Base URL | `https://api.newlineages.com` |
| Search endpoint | `POST /api/search_literature` |
| Paper details endpoint | `POST /api/get_paper_details` |
| Advanced endpoint | `POST /api/scan_literature_advanced` |
| Helper script | `scripts/query_literature.py` for grouped scans and compact output |
| Rate limit | 100 queries/hour |

## Input Requirements

- API key (`POLARS_DOVMED_API_KEY`)
- Search query or grouped concepts
- Optional local year target for post-filtering and verification
- Optional `fast_mode`:
  - `false` (default): full-text search (`title`, `abstract_text`, `abstract`, `full_text`)
  - `true`: abstract-only search (`abstract_text`, `abstract`)
- Optional `match_mode` on `/api/search_literature`:
  - `literal` (default): case-insensitive literal matching with whole-word behavior for single terms and simple plural expansion
  - `substring`: case-insensitive partial matching
  - `regex`: raw regex matching on the simple endpoint; use sparingly
- Do not assume endpoint-level year or journal filters exist unless you have verified the current API syntax.
  - If the user asks for a specific year, treat it as a post-filtering and citation-verification step.
- On the simple endpoint, `total_found` may be approximate unless the service is configured to compute exact counts.
  - Treat returned titles as the authoritative signal unless `total_found_is_exact` is `true`.

## Search Semantics

- Plain multi-word queries are literal `AND` queries.
  - `"mirusvirus host"` means papers must match both `mirusvirus` and `host`.
  - This is often too strict for natural-language searches.
- The simple endpoint defaults to `match_mode="literal"`.
  - This is usually the safest choice for scientific names and exact terms.
- Quoted phrases are preserved on the simple endpoint.
  - `"\"giant virus\" OR mimivirus"` preserves the phrase `giant virus` and broadens with `mimivirus`.
- Single-word literal terms use whole-word matching on the simple endpoint.
  - This reduces substring noise such as matching `virus` inside unrelated longer tokens.
- Literal mode also applies simple plural expansion for single-word terms.
  - A query term like `virus` can match both `virus` and `viruses`.
- Use `match_mode="substring"` only when partial matching is intentional.
  - Example: catching surface forms that differ in ways not covered by the simple plural expansion.
- Use `match_mode="regex"` only when you really need regex behavior on the simple endpoint.
  - Otherwise prefer `literal` or move to `/api/scan_literature_advanced`.
- `OR` must be written explicitly to broaden synonyms or alternate taxonomy names.
  - `"Mirusviricota OR mirusvirus"`
  - `"bacteriophage OR phage"`
  - `"\"giant virus\" OR giant viruses OR Nucleocytoviricota"`
- Do not rely on ambiguous flat mixed boolean intent.
  - If grouping matters, switch to `/api/scan_literature_advanced` instead of assuming how `"A OR B C"` will be parsed.
- Stop words such as `the`, `a`, `an`, `in`, `of`, `for`, `and`, `to`, `from` are removed.
- Single high-frequency terms can be noisy.
  - A query like `"CRISPR"` may return low-precision results.
- Do not assume the endpoint understands natural-language intent.
  - Bad: `"papers on hosts of mirusviricota"`
  - Better: `"Mirusviricota OR mirusvirus"`
  - Then fetch details for the returned papers and inspect host text directly.

## Query Workflow

1. Start with the narrowest exact concept that should exist in the literature.
   - Example: `"Holospora OR Caedibacter"`
2. Broaden with explicit synonym queries when taxonomy or naming drift is likely.
   - Example: `"Mirusviricota OR mirusvirus OR \"giant virus\""`
3. If recall still looks too low, consider whether `match_mode="substring"` is justified before switching endpoints.
   - Do this only when partial matching is intentional and you have checked the first titles for noise.
4. If the request combines multiple biological concepts or needs explicit boolean grouping, switch early to `/api/scan_literature_advanced`.
   - Use grouped queries for cases like host + symbiont, organism + pathway, or organism + time window.
5. Use `/api/get_paper_details` on candidate PMC IDs to inspect abstract/full text and collect citation metadata.
6. If metadata fields such as `year`, `publication_date`, or `doi` are blank, verify the citation in PubMed or PMC before final output.
7. If a recent paper is missing from the API but exists in PubMed or PMC, report the gap rather than assuming the literature is absent.
8. If the simple endpoint reports `total_found_is_exact: false`, do not over-interpret `total_found`.

## Synonym Query Examples

- `"Mirusviricota OR mirusvirus"`
- `"bacteriophage OR phage"`
- `"Nucleocytoviricota OR \"giant virus\" OR giant viruses"`
- `"host range OR host specificity"`
- `"protist OR microeukaryote"`

## Recent-Paper And Metadata Caveats

- Recent papers may be partially indexed or missing entirely from this API even when they are already in PubMed or PMC.
- `get_paper_details` can return blank `year`, `publication_date`, `doi`, or `authors` fields for valid papers.
- The simple endpoint can return approximate `total_found` counts when exact counting is disabled for performance.
- When the user asks for "2025 papers", "latest papers", or complete citations:
  - treat API results as discovery, not final authority
  - verify dates and DOI in PubMed or PMC if metadata is incomplete
  - say explicitly when the API appears to have indexing gaps

## Output

- Paper lists with metadata (PMC ID, DOI, title, year)
- Matched text snippets
- Extracted entities (genes, accessions, terms)
- Mode metadata (`search_mode`, `searched_columns`)
- Count metadata (`total_found_is_exact`, when present)
- Warnings about missing metadata or likely indexing gaps when relevant

## Quality Gates

- [ ] API key loaded successfully
- [ ] Chosen endpoint matches the query shape
- [ ] First 5-10 returned titles match expected scope
- [ ] If `total_found_is_exact` is false or missing, answer does not overstate the count
- [ ] Extracted citation fields checked for missing `year`, `publication_date`, `doi`, or `authors`
- [ ] Recent-year requests verified in PubMed or PMC if API metadata is incomplete
- [ ] Final answer calls out indexing gaps or low-confidence matches when present

## Examples

### Example 1: Flat synonym or phrase search (Python)

```python
import httpx

headers = {"X-API-Key": "YOUR_KEY"}
resp = httpx.post(
    "https://api.newlineages.com/api/search_literature",
    headers=headers,
    json={
        "query": "\"giant virus\" OR giant viruses OR Nucleocytoviricota",
        "max_results": 10,
        "extract_matches": False,
        "fast_mode": False,
        "match_mode": "literal",
    },
)
print(resp.json())
```

### Example 2: Grouped host-microbe scan with the helper script

Use the bundled script when the query has multiple concept groups and you want compact output.

```bash
POLARS_DOVMED_API_KEY=YOUR_KEY \
python skills/polars-dovmed/scripts/query_literature.py \
  --group host_terms=ciliate,ciliates,Ciliophora,Paramecium,Loxodes \
  --group symbiont_terms=endosymbiont,symbionts,intracellular,Holosporales,Rickettsiales,Legionellales \
  --max-results 25
```

### Example 3: Advanced structured scan (Python)

```python
import httpx

headers = {"X-API-Key": "YOUR_KEY"}
resp = httpx.post(
    "https://api.newlineages.com/api/scan_literature_advanced",
    headers=headers,
    json={
        "primary_queries": {
            "host_terms": [["ciliate"], ["ciliates"], ["Ciliophora"], ["Paramecium"], ["Loxodes"]],
            "symbiont_terms": [["endosymbiont"], ["symbionts"], ["intracellular"], ["Holosporales"], ["Rickettsiales"], ["Legionellales"]],
        },
        "search_columns": ["title", "abstract_text", "full_text"],
        "extract_matches": "primary",
        "add_group_counts": "primary",
        "max_results": 25,
    },
    timeout=600.0,
)
print(resp.json())
```

Use this endpoint when:
- you need more than one concept group
- the flat search endpoint returns `0` or low-precision results
- the user is asking about host-associated bacteria, symbionts, pathogens, or recent organism-specific literature

### Example 4: Fetch details for candidate papers

Use `/api/get_paper_details` after a broad search has identified relevant PMC IDs.

```python
import httpx

headers = {"X-API-Key": "YOUR_KEY"}
resp = httpx.post(
    "https://api.newlineages.com/api/get_paper_details",
    headers=headers,
    json={"pmc_ids": ["PMC10827195", "PMC11465185"]},
    timeout=120.0,
)
print(resp.json())
```

Use this endpoint when:
- you already have candidate PMC IDs
- you need abstract/full-text fields for manual review
- you want DOI, journal, and publication metadata without rerunning broader searches

## Timeout And Relevance Guidance

- Simple `/api/search_literature` queries usually fit in `60-120s`.
- Broad or high-frequency terms may take longer; use `120s` unless you know the query is tiny.
- `/api/scan_literature_advanced` can take minutes; use `600s` for non-trivial scans.
- For multi-concept biology searches, prefer the advanced endpoint instead of repeatedly retrying brittle flat queries.
- If the API is healthy but results look wrong:
  - check whether you accidentally overconstrained the query with implicit `AND`
  - check whether a quoted phrase or whole-word literal would be better than a loose flat query
  - retry with `OR` across synonyms or taxonomy variants
  - switch to grouped `primary_queries` instead of adding more words to a flat query
  - inspect candidate titles before trusting the set
  - treat `0` hits from a long natural-language phrase as a query-construction problem before assuming the literature is absent
  - treat missing recent papers as a possible indexing problem and verify externally

## Troubleshooting

**Issue**: 401 Unauthorized
**Solution**: Verify `POLARS_DOVMED_API_KEY` and reload the environment.

**Issue**: 429 Rate limited
**Solution**: Wait for quota reset or reduce request frequency.

**Issue**: Fast mode returns too few results
**Solution**: Retry with `fast_mode=false` to include full text.

**Issue**: Literal mode is too strict and misses expected variants
**Solution**: First add explicit synonyms or quoted phrases. If partial matching is really intended, retry with `match_mode="substring"` and inspect the first titles for new noise.

**Issue**: Substring mode is noisy
**Solution**: Go back to `match_mode="literal"` or move the query to `/api/scan_literature_advanced` with explicit grouped concepts.

**Issue**: Multi-word query returns `0` but related papers should exist
**Solution**: Remember plain space-separated terms are `AND`. Retry with explicit `OR` synonyms, then switch to `/api/scan_literature_advanced` for grouped concepts.

**Issue**: `total_found` equals `returned` on the simple endpoint
**Solution**: Treat the returned set as authoritative and check `total_found_is_exact`. If exact counting matters, do not overstate the total unless the response marks it exact.

**Issue**: Need host/pathway/accession extraction across several concept groups
**Solution**: Use `/api/scan_literature_advanced` instead of forcing everything into one `query` string.

**Issue**: Results look topically wrong even though the API returned hits
**Solution**: Check the first 5-10 titles, prefer exact taxa or quoted phrases, reduce single-term queries, and tighten the concept groups before extracting details.

**Issue**: Flat query grouping is ambiguous
**Solution**: Do not rely on implicit boolean parsing for complex intent. Move the query to `/api/scan_literature_advanced` and spell out the concept groups.

**Issue**: A recent paper appears in PubMed or PMC but not in this API
**Solution**: Treat this as an indexing gap, cite the external source, and mention that the API missed a relevant paper.

**Issue**: `get_paper_details` returns blank `year`, `publication_date`, or `doi`
**Solution**: Verify the citation in PubMed or PMC before giving a year-specific or publication-ready answer.
