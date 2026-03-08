---
name: polars-dovmed
description: Search 2.4M+ full-text PubMed Central Open Access papers for literature reviews, trends, and data extraction.
user-invocable: true
---

# polars-dovmed

Search across 2.4M+ PMC Open Access papers for literature discovery and extraction tasks.

## Instructions

1. Load the API key from a secure location.
2. Run a full-text search or metadata query.
3. Extract required fields (titles, DOIs, accessions, snippets).
4. Summarize results and cite sources.

## Quick Reference

| Task | Action |
|------|--------|
| API key | `POLARS_DOVMED_API_KEY` in env or `~/.config/polars-dovmed/.env` |
| Base URL | `https://api.newlineages.com` |
| Search endpoint | `POST /api/search_literature` |
| Paper details endpoint | `POST /api/get_paper_details` |
| Advanced endpoint | `POST /api/scan_literature_advanced` |
| Rate limit | 100 queries/hour |

## Input Requirements

- API key (`POLARS_DOVMED_API_KEY`)
- Search query and filters (year, journal, organism, etc.)
- Optional `fast_mode`:
  - `false` (default): full-text search (`title`, `abstract_text`, `abstract`, `full_text`)
  - `true`: abstract-only search (`abstract_text`, `abstract`)

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
- Do not assume the endpoint understands natural-language intent.
  - Bad: `"papers on hosts of mirusviricota"`
  - Better: `"Mirusviricota OR mirusvirus"`
  - Then fetch details for the returned papers and inspect host text directly.

## Query Strategy

1. Start broad with the core concept.
   - Example: `"Mirusviricota OR mirusvirus"`
2. Add explicit synonym queries if taxonomy/naming drift is likely.
   - Example: `"Mirusviricota OR mirusvirus OR giant virus"`
3. If a direct multi-word query returns `0`, retry with broader `OR` terms rather than adding more words.
4. Use `/api/get_paper_details` once you have relevant PMC IDs and need abstracts, full text, or DOI fields.
5. Use `/api/scan_literature_advanced` only when you need structured multi-group logic, secondary filters, or identifier extraction.

## Synonym Query Examples

- `"Mirusviricota OR mirusvirus"`
- `"bacteriophage OR phage"`
- `"Nucleocytoviricota OR giant virus"`
- `"host range OR host specificity"`
- `"protist OR microeukaryote"`

## Output

- Paper lists with metadata (PMC ID, DOI, title, year)
- Matched text snippets
- Extracted entities (genes, accessions, terms)
- Mode metadata (`search_mode`, `searched_columns`)

## Quality Gates

- [ ] API key loaded successfully
- [ ] Query results match expected scope
- [ ] Extracted fields validated for completeness

## Examples

### Example 1: Minimal search (Python)

```python
import httpx

headers = {"X-API-Key": "YOUR_KEY"}
resp = httpx.post(
    "https://api.newlineages.com/api/search_literature",
    headers=headers,
    json={
        "query": "CRISPR archaea",
        "max_results": 10,
        "extract_matches": False,
        "fast_mode": False,  # set True for abstract-only
    },
)
print(resp.json())
```

### Example 2: Broadening with OR syntax

```python
import httpx

headers = {"X-API-Key": "YOUR_KEY"}
resp = httpx.post(
    "https://api.newlineages.com/api/search_literature",
    headers=headers,
    json={
        "query": "Mirusviricota OR mirusvirus",
        "max_results": 20,
        "extract_matches": True,
        "fast_mode": False,
    },
    timeout=120.0,
)
print(resp.json())
```

### Example 3: Fetch details for candidate papers

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

### Example 4: Advanced structured scan

Use `/api/scan_literature_advanced` when simple `query` strings are not enough.

```python
import httpx

headers = {"X-API-Key": "YOUR_KEY"}
resp = httpx.post(
    "https://api.newlineages.com/api/scan_literature_advanced",
    headers=headers,
    json={
        "primary_queries": {
            "virus_terms": [["mirusviricota"], ["mirusvirus"]],
            "host_terms": [["host"], ["host range"], ["microeukaryote"], ["protist"]],
        },
        "search_columns": ["title", "abstract_text", "full_text"],
        "extract_matches": "primary",
        "add_group_counts": "primary",
        "max_results": 100,
    },
    timeout=600.0,
)
print(resp.json())
```

Use this endpoint when:
- you need multiple concept groups instead of one flat query
- you want to count which groups matched
- you need secondary filters, identifier patterns, or coordinate extraction
- simple search is either too broad or too brittle

## Timeout And Relevance Guidance

- Simple `/api/search_literature` queries usually fit in `60-120s`.
- Broad or high-frequency terms may take longer; use `120s` unless you know the query is tiny.
- `/api/scan_literature_advanced` can take minutes; use `600s` for non-trivial scans.
- If the API is healthy but results look wrong:
  - check whether you accidentally overconstrained the query with implicit `AND`
  - retry with `OR` across synonyms or taxonomy variants
  - search broad first, then inspect paper details
  - treat `0` hits from a long natural-language phrase as a query-construction problem before assuming the literature is absent

## Troubleshooting

**Issue**: 401 Unauthorized
**Solution**: Verify `POLARS_DOVMED_API_KEY` and reload the environment.

**Issue**: 429 Rate limited
**Solution**: Wait for quota reset or reduce request frequency.

**Issue**: Fast mode returns too few results
**Solution**: Retry with `fast_mode=false` to include full text.

**Issue**: Multi-word query returns `0` but related papers should exist
**Solution**: Remember plain space-separated terms are `AND`. Retry with explicit `OR` synonyms, then use `/api/get_paper_details` on returned PMCs.

**Issue**: Need host/pathway/accession extraction across several concept groups
**Solution**: Use `/api/scan_literature_advanced` instead of forcing everything into one `query` string.
