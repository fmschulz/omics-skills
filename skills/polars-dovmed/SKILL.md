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
   - Use `/api/search_literature` for one concept or a flat synonym query.
   - Use `/api/scan_literature_advanced` for multi-concept biology searches such as host + symbiont, organism + pathway, or organism + recent-year questions.
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
- Do not assume endpoint-level year or journal filters exist unless you have verified the current API syntax.
  - If the user asks for a specific year, treat it as a post-filtering and citation-verification step.

## Search Semantics

- Plain multi-word queries are `AND` queries.
  - `"mirusvirus host"` means papers must match both `mirusvirus` and `host`.
  - This is often too strict for natural-language searches.
- `OR` must be written explicitly to broaden synonyms or alternate taxonomy names.
  - `"Mirusviricota OR mirusvirus"`
  - `"bacteriophage OR phage"`
  - `"host range OR host specificity"`
- Mixed queries are grouped by `OR`.
  - `"CRISPR OR Cas9 archaea"` means `(CRISPR AND archaea) OR (Cas9 AND archaea)`.
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
   - Example: `"Mirusviricota OR mirusvirus OR giant virus"`
3. If the request combines multiple biological concepts, switch early to `/api/scan_literature_advanced`.
   - Use grouped queries for cases like host + symbiont, organism + pathway, or organism + time window.
4. Use `/api/get_paper_details` on candidate PMC IDs to inspect abstract/full text and collect citation metadata.
5. If metadata fields such as `year`, `publication_date`, or `doi` are blank, verify the citation in PubMed or PMC before final output.
6. If a recent paper is missing from the API but exists in PubMed or PMC, report the gap rather than assuming the literature is absent.

## Synonym Query Examples

- `"Mirusviricota OR mirusvirus"`
- `"bacteriophage OR phage"`
- `"Nucleocytoviricota OR giant virus"`
- `"host range OR host specificity"`
- `"protist OR microeukaryote"`

## Recent-Paper And Metadata Caveats

- Recent papers may be partially indexed or missing entirely from this API even when they are already in PubMed or PMC.
- `get_paper_details` can return blank `year`, `publication_date`, `doi`, or `authors` fields for valid papers.
- When the user asks for "2025 papers", "latest papers", or complete citations:
  - treat API results as discovery, not final authority
  - verify dates and DOI in PubMed or PMC if metadata is incomplete
  - say explicitly when the API appears to have indexing gaps

## Output

- Paper lists with metadata (PMC ID, DOI, title, year)
- Matched text snippets
- Extracted entities (genes, accessions, terms)
- Mode metadata (`search_mode`, `searched_columns`)
- Warnings about missing metadata or likely indexing gaps when relevant

## Quality Gates

- [ ] API key loaded successfully
- [ ] Chosen endpoint matches the query shape
- [ ] First 5-10 returned titles match expected scope
- [ ] Extracted citation fields checked for missing `year`, `publication_date`, `doi`, or `authors`
- [ ] Recent-year requests verified in PubMed or PMC if API metadata is incomplete
- [ ] Final answer calls out indexing gaps or low-confidence matches when present

## Examples

### Example 1: Flat synonym search (Python)

```python
import httpx

headers = {"X-API-Key": "YOUR_KEY"}
resp = httpx.post(
    "https://api.newlineages.com/api/search_literature",
    headers=headers,
    json={
        "query": "Mirusviricota OR mirusvirus OR giant virus",
        "max_results": 10,
        "extract_matches": False,
        "fast_mode": False,
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

**Issue**: Multi-word query returns `0` but related papers should exist
**Solution**: Remember plain space-separated terms are `AND`. Retry with explicit `OR` synonyms, then switch to `/api/scan_literature_advanced` for grouped concepts.

**Issue**: Need host/pathway/accession extraction across several concept groups
**Solution**: Use `/api/scan_literature_advanced` instead of forcing everything into one `query` string.

**Issue**: Results look topically wrong even though the API returned hits
**Solution**: Check the first 5-10 titles, reduce single-term queries, and tighten the concept groups before extracting details.

**Issue**: A recent paper appears in PubMed or PMC but not in this API
**Solution**: Treat this as an indexing gap, cite the external source, and mention that the API missed a relevant paper.

**Issue**: `get_paper_details` returns blank `year`, `publication_date`, or `doi`
**Solution**: Verify the citation in PubMed or PMC before giving a year-specific or publication-ready answer.
