---
name: biorxiv-search
description: Scan bioRxiv by date range, category, author, or DOI through its official API, with local keyword filtering. Use for recent biology preprints, bioRxiv DOI lookups, or author shortlists.
---

# bioRxiv Search

Scan bioRxiv metadata through its official API for recent preprints, date ranges, DOI lookups, and author shortlists, with local keyword filtering over title, abstract, and authors.

## Instructions

1. Use this skill for bioRxiv preprints and for preprint metadata that may lag in PubMed, PMC, or Crossref. Use `/arxiv-search` for arXiv and `/polars-dovmed` for peer-reviewed PMC full text.
2. Run the bundled CLI, `scripts/search`. Paths below are relative to this skill's directory, installed at `~/.agents/skills/biorxiv-search`.
3. The API has no keyword search. The CLI fetches metadata for a bounded interval and filters it locally.
   - Set the interval with `--days N` or `--start-date YYYY-MM-DD --end-date YYYY-MM-DD`. Without one, the CLI uses the last 30 days and says so in `warnings`.
   - The API returns 30 records per page, oldest first. The CLI starts at the newest page and scans backward until it has read `--scan-limit` records (default 300) or reached the start of the interval, then returns up to `max_results` matches.
4. Write keyword queries in local query syntax:
   - Words are combined with `AND`: `single cell atlas` needs all three words.
   - `OR` must be explicit: `organoid OR spheroid`.
   - Quoted phrases stay together: `'"single cell" atlas'`. `--phrase` treats the whole query as one phrase.
   - Matching covers `title,abstract,authors` by default; `--fields abstract` restricts it to abstracts.
5. Narrow the scan with `--category`, using the bioRxiv category name with underscores (`genomics`, `cell_biology`, `developmental_biology`).
6. For author requests, pass the full-name and initial forms as separate `--author` values, for example `--author "Peter Nugent" --author "P. Nugent"`. The CLI also accepts `Surname, F. M.` forms and reports each form in its own match group. Report the groups separately and label initial-form matches as possibly a different person.
7. The CLI keeps the latest version of each DOI. Use `--all-versions` when version history matters.
8. Treat API output as discovery metadata. Check the final candidates on bioRxiv or the DOI landing page when citation or version details matter.
9. The CLI spaces page requests at least 0.2 seconds apart and retries `HTTP 429` and transient `5xx` responses with exponential backoff (`--retries`, default 3; `--retry-backoff`, default 1 second).

## Quick Reference

| Task | Action |
|------|--------|
| Keyword scan | `scripts/search "<query>" [max_results]` (default 10) |
| Recent window | `--days 30` |
| Date range | `--start-date YYYY-MM-DD --end-date YYYY-MM-DD` |
| DOI lookup | `--doi 10.1101/...` |
| Category | `--category genomics` |
| Author | `--author "Name"`, repeatable |
| Search fields | `--fields title,abstract,authors` (default) or `--fields abstract` |
| Scan depth | `--scan-limit 300` |
| Keep all versions | `--all-versions` |
| Network timeout | `--timeout 30` |

## Input Requirements

- Python 3 on `PATH` and network access to `api.biorxiv.org`.
- One of: a keyword query, an author, a category, a bioRxiv DOI via `--doi`, or a request for recent preprints.
- A bounded interval. For old or broad searches, widen the interval and `--scan-limit` deliberately, and say that recall depends on both.

## Output

JSON with:

- `request`: query, `query_groups`, phrase flag, DOI, interval, category, author filters and expanded variants, search fields, limits, and retry settings
- `api`: `base_url`, `pages_fetched`, `records_scanned`, `total_available`, `request_urls`
- `result_summary`: matches before and after deduplication, `returned`, `versions_collapsed`, `version_policy`, `reached_scan_limit`
- `warnings`: defaulted interval, scan-limit truncation, missing filters
- `author_match_groups`: matches per requested author form
- `results`: `doi`, `title`, `authors`, `date`, `version`, `category`, `abstract`, `published`, `doi_url`, `biorxiv_url`, `matched_in`, and further API fields

## Quality Gates

- [ ] The scan uses a bounded interval, and `--scan-limit` fits the query breadth; `reached_scan_limit` is reported.
- [ ] Search fields match the request, especially when abstract matching matters.
- [ ] Author requests report full-name and initial-form groups separately, with initial-form matches labeled ambiguous.
- [ ] The answer does not overstate recall for a broad historical search.
- [ ] Citation or version details were checked on bioRxiv when they matter.

## Examples

```bash
# Recent keyword scan over title, abstract, and authors
scripts/search "single cell atlas" 10 --days 30

# Synonyms with OR, one category
scripts/search 'organoid OR spheroid' 15 --days 90 --category developmental_biology

# Abstract-only matching
scripts/search "CRISPR screen" 10 --days 60 --fields abstract

# Author variants, reported in separate groups
scripts/search "supernova" 20 --days 365 --author "Peter Nugent" --author "P. Nugent"

# DOI lookup
scripts/search --doi 10.1101/682021
```

## Troubleshooting

**Issue**: Results are too broad.
**Solution**: Shorten the interval, add `--category`, restrict `--fields`, or use a phrase.

**Issue**: Results are sparse or a known preprint is missing.
**Solution**: Widen the interval, raise `--scan-limit`, add `OR` synonyms, and state the change in the answer.

**Issue**: Author results look incomplete.
**Solution**: Add more `--author` variants, such as a middle initial (`"Peter E. Nugent"`, `"P. E. Nugent"`), and keep each group separate.

## Related Skills

- `/crossref-lookup`: citation metadata for bioRxiv DOIs
- `/arxiv-search`: arXiv preprints
- `/polars-dovmed`: peer-reviewed PMC full text and bioRxiv full text
