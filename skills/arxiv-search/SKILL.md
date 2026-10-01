---
name: arxiv-search
description: Search arXiv through its official API and write Markdown notes for arXiv IDs. Use for CS, math, physics, statistics, or quantitative-biology preprints, or to resolve arXiv IDs.
user-invocable: true
---

# arXiv Search

Search arXiv through its official API for discovery, shortlists, recent-preprint tracking, and local Markdown notes for known arXiv IDs.

## Instructions

1. Use this skill for arXiv-native preprints: computer science, mathematics, physics, statistics, quantitative biology, and quantitative finance. Use `/biorxiv-search` for biology preprints and `/polars-dovmed` for peer-reviewed PMC full text.
2. Run the bundled CLI, `scripts/search`; `scripts/summarize` writes Markdown notes. Paths below are relative to this skill's directory, installed at `~/.agents/skills/arxiv-search`.
3. Choose the query mode:
   - Plain text: bare words become `all:` terms joined with `AND`. Add `--phrase` to match the words as one phrase.
   - Raw: a query that already uses arXiv syntax (`ti:`, `au:`, `abs:`, `co:`, `jr:`, `cat:`, `rn:`, `all:`, `submittedDate:`, `AND`, `OR`, `ANDNOT`) passes through unchanged.
4. Narrow the scope with `--category` (for example `cs.LG`, `stat.ML`, `q-bio.QM`) or a raw `cat:` term.
5. For recent papers, use `--sort submittedDate --order descending`. `--days N` filters the returned page locally by `published` date, so request enough results to cover the window. A server-side window is a raw term such as `submittedDate:[202609010000 TO 202609302359]` (returned results on 2026-10-01).
6. For author requests, run the full-name and initial forms as separate raw queries, for example `au:"Peter Nugent"` and `au:"P. Nugent"`. Report the two result sets separately and label initial-form matches as possibly a different person.
7. Treat API output as discovery metadata. When the version, withdrawal status, or exact dates matter, check the final candidates on arxiv.org.
8. Keep request volume low. arXiv asks for at least 3 seconds between API calls. The CLI caches identical requests for 24 hours, spaces calls at least 3.1 seconds apart across processes with a file lock, and retries `HTTP 429` with backoff. Prefer one scoped query plus local filtering over many small queries; use OAI-PMH for bulk harvesting.
9. Use `scripts/summarize` when the user wants stable local notes for specific arXiv IDs.

## Quick Reference

| Task | Action |
|------|--------|
| Search | `scripts/search "<query>" [max_results]` (default 10) |
| Exact phrase | `--phrase` |
| Category | `--category cs.LG` |
| Recent first | `--sort submittedDate --order descending` |
| Sort fields | `--sort relevance\|lastUpdatedDate\|submittedDate`, `--order ascending\|descending` |
| Local date filter | `--days 30` |
| Paging | `--start N` |
| ID lookup | `--ids 2501.01234,2406.00001` |
| Markdown notes | `scripts/summarize 2501.01234 --output-dir arxiv-summaries [--force]` |
| Network timeout | `--timeout 20` |
| Cache and pacing | `--cache-dir PATH` (or `ARXIV_SEARCH_CACHE_DIR`), `--no-cache`, `--cache-ttl 86400`, `--min-interval 3.1`, `--retries 2`, `--retry-backoff 60` |

## Input Requirements

- Python 3 on `PATH` and network access to `export.arxiv.org`.
- A plain-text or raw arXiv query, or one or more arXiv IDs.
- For notes: arXiv IDs, an optional `--output-dir` (default `arxiv-summaries`), and `--force` to overwrite existing files.

## Output

- `scripts/search` prints JSON with:
  - request fields: `query`, `compiled_query`, `query_mode` (raw or plain text), `start`, `max_results`, `sort_by`, `sort_order`, `request_url`
  - `days_filter` when `--days` is set, and `warnings` for local workarounds
  - feed fields: `total_results`, `items_per_page`, `start_index`, `feed_updated`
  - `results`: `title`, `summary`, `authors`, `arxiv_id`, `abs_url`, `pdf_url`, `published`, `updated`, `primary_category`, `categories`, and `comment`, `journal_ref`, `doi` when present
- `scripts/summarize` prints JSON listing written files and missing IDs, and writes one Markdown file per arXiv ID with metadata, abstract, citation, and an empty `## Notes` section.

## Quality Gates

- [ ] The query mode fits the request, and the first page of titles is small enough to inspect.
- [ ] Recent-paper requests sort by `submittedDate`; a `--days` filter is reported as a local filter on the returned page.
- [ ] Category-sensitive requests use `--category` or `cat:`.
- [ ] Author requests report full-name and initial-form results separately, with initial-form matches labeled ambiguous.
- [ ] The answer separates arXiv preprints from peer-reviewed literature.
- [ ] Version or date claims were checked on arxiv.org.

## Examples

```bash
# Recent machine-learning preprints, newest first, last 30 days
scripts/search "protein language model" 50 --phrase --category cs.LG \
  --sort submittedDate --order descending --days 30

# Raw arXiv syntax
scripts/search 'cat:cs.LG AND ti:"diffusion" ANDNOT abs:"survey"' 15

# Author variants, reported separately
scripts/search 'au:"Peter Nugent"' 20 --sort submittedDate --order descending
scripts/search 'au:"P. Nugent"' 20 --sort submittedDate --order descending

# Records and notes for known IDs
scripts/search --ids 2501.01234,2406.00001
scripts/summarize 2501.01234 2406.00001 --output-dir arxiv-summaries
```

## Troubleshooting

**Issue**: Results are too broad or too sparse.
**Solution**: Add or drop `--category` and `--phrase`, switch to raw `ti:`/`abs:` fields, or broaden with `OR`.

**Issue**: `--days` returns few results.
**Solution**: The filter applies to the returned page only. Raise `max_results` with `--sort submittedDate --order descending`, or use a raw `submittedDate:[... TO ...]` term.

**Issue**: `HTTP 429 Rate exceeded` persists after retries.
**Solution**: Wait several minutes, reduce the number of queries, reuse cached results, or check final IDs on arxiv.org.

**Issue**: The request hangs or times out.
**Solution**: Lower `max_results`, raise `--timeout` modestly, and check that `export.arxiv.org` is reachable.

## Related Skills

- `/crossref-lookup`: citation metadata for arXiv DOIs
- `/biorxiv-search`: biology preprints
- `/polars-dovmed`: peer-reviewed PMC full text
