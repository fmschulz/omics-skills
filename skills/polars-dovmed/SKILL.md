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
| Rate limit | 100 queries/hour |

## Input Requirements

- API key (`POLARS_DOVMED_API_KEY`)
- Search query and filters (year, journal, organism, etc.)
- Optional `fast_mode`:
  - `false` (default): full-text search (`title`, `abstract_text`, `abstract`, `full_text`)
  - `true`: abstract-only search (`abstract_text`, `abstract`)

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

## Troubleshooting

**Issue**: 401 Unauthorized
**Solution**: Verify `POLARS_DOVMED_API_KEY` and reload the environment.

**Issue**: 429 Rate limited
**Solution**: Wait for quota reset or reduce request frequency.

**Issue**: Fast mode returns too few results
**Solution**: Retry with `fast_mode=false` to include full text.
