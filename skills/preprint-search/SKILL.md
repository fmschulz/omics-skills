---
name: preprint-search
description: Search arXiv by query, category or ID, and scan bioRxiv by date range, author or DOI with local keyword filtering. Use when you need preprint shortlists, recent-preprint tracking, arXiv or bioRxiv ID lookups, or arXiv Markdown notes.
user-invocable: true
---

# Preprint Search

Three bundled CLIs, installed at `~/.agents/skills/preprint-search/scripts/`: `arxiv_search`, `arxiv_summarize` (Markdown notes) and `biorxiv_search`. `arxiv_search` and `biorxiv_search` print JSON. `arxiv_summarize` writes Markdown files and prints a JSON status. Treat output as discovery metadata; check final candidates on arxiv.org or bioRxiv when the version, withdrawal status or exact dates matter.

## Instructions

1. Pick the source. arXiv covers computer science, mathematics, physics, statistics, quantitative biology and finance. For biology preprints and for peer-reviewed PMC full text, topical or full-text questions go to `polars-dovmed --corpus biorxiv` (or `pmc`).
2. bioRxiv: date and category listing and DOI lookup can use the bioRxiv MCP connector when the session has it. This script adds local keyword and author filtering over a date-range scan.
3. Author requests: run the full-name and initial forms as separate queries (arXiv: `au:"Peter Nugent"` and `au:"P. Nugent"`; bioRxiv: repeated `--author "Peter Nugent" --author "P. Nugent"`). Report the groups separately and label initial-form matches as possibly a different person.

### arXiv

- Plain text: bare words become `all:` terms joined with `AND`; `--phrase` matches them as one phrase. Raw: a query that already uses arXiv syntax (`ti:`, `au:`, `abs:`, `co:`, `jr:`, `cat:`, `rn:`, `all:`, `submittedDate:`, `AND`, `OR`, `ANDNOT`) passes through unchanged.
- Narrow with `--category` (for example `cs.LG`, `stat.ML`, `q-bio.QM`) or a raw `cat:` term.
- Recent papers: `--sort submittedDate --order descending`. `--days N` filters the returned page locally by `published` date, so request enough results to cover the window. A server-side window is a raw term such as `submittedDate:[202609010000 TO 202609302359]`.
- arXiv asks for at least 3 seconds between API calls. The CLI caches identical requests for 24 hours, spaces calls at least 3.1 seconds apart across processes with a file lock, and retries `HTTP 429` with backoff. Prefer one scoped query plus local filtering over many small queries; use OAI-PMH for bulk harvesting.

```bash
S=~/.agents/skills/preprint-search/scripts
$S/arxiv_search "protein language model" 50 --phrase --category cs.LG --sort submittedDate --order descending --days 30
$S/arxiv_search 'cat:cs.LG AND ti:"diffusion" ANDNOT abs:"survey"' 15
$S/arxiv_search --ids 2501.01234,2406.00001
$S/arxiv_summarize 2501.01234 --output-dir arxiv-summaries [--force]
```

`--ids` requests as many results as there are IDs unless you give the positional `max_results`. A raw query with `--category` is wrapped in parentheses before `AND cat:...` is added.

Other options: `--sort relevance|lastUpdatedDate|submittedDate`, `--order`, `--start N`, `--timeout 20`, `--cache-dir PATH` (or `ARXIV_SEARCH_CACHE_DIR`), `--no-cache`, `--cache-ttl 86400`, `--min-interval 3.1`, `--retries 2`, `--retry-backoff 60`. `arxiv_summarize` writes one file per ID (metadata, abstract, citation, empty `## Notes`) and lists missing IDs.

### bioRxiv

The API has no keyword search. The CLI fetches metadata for a bounded interval and filters it locally.

- Interval: `--days N` or `--start-date YYYY-MM-DD --end-date YYYY-MM-DD`. Without one, the last 30 days, noted in `warnings`.
- Scan limit: the API returns 30 records per page, oldest first. The CLI starts at the newest page and reads backward until it has read `--scan-limit` records (default 300) or reached the start of the interval. Recall for a broad or old search is therefore weak; widen the interval and `--scan-limit` deliberately, report `reached_scan_limit`, and do not overstate recall.
- Query syntax: words are `AND`ed; `OR` must be explicit (`organoid OR spheroid`); quoted phrases stay together (`'"single cell" atlas'`); `--phrase` treats the whole query as one phrase. Fields default to `title,abstract,authors`; `--fields abstract` restricts it.
- `--category` takes the bioRxiv name with underscores (`genomics`, `cell_biology`, `developmental_biology`). The API ignores an unknown category, so the CLI drops records of other categories and adds a warning when it did. `--doi 10.1101/...` looks up one DOI and warns when bioRxiv does not know it; medRxiv DOIs are not covered. The CLI keeps the latest version of each DOI; `--all-versions` keeps all.
- Pacing: page requests at least 0.2 seconds apart; `HTTP 429` and transient `5xx` retried with exponential backoff (`--retries 3`, `--retry-backoff 1`). `--timeout 30`.
- Author variants also accept `Surname, F. M.` forms; add middle-initial variants (`"Peter E. Nugent"`, `"P. E. Nugent"`) when results look incomplete.

```bash
$S/biorxiv_search "single cell atlas" 10 --days 30
$S/biorxiv_search 'organoid OR spheroid' 15 --days 90 --category developmental_biology
$S/biorxiv_search "supernova" 20 --days 365 --author "Peter Nugent" --author "P. Nugent"
$S/biorxiv_search --doi 10.1101/682021
```

## Input Requirements

Python 3 and network access to `export.arxiv.org` or `api.biorxiv.org`; a query, ID, DOI, author or category.

## Output

- `arxiv_search`: request fields (`compiled_query`, `query_mode`, `request_url`), `days_filter`, `warnings`, feed totals, and `results` (`title`, `summary`, `authors`, `arxiv_id`, `abs_url`, `pdf_url`, `published`, `updated`, categories, and `comment`, `journal_ref`, `doi` when present).
- `biorxiv_search`: `request`, `api` (`pages_fetched`, `records_scanned`, `total_available`), `result_summary` (including `reached_scan_limit`, `versions_collapsed`), `warnings`, `author_match_groups`, and `results` (`doi`, `title`, `authors`, `date`, `version`, `category`, `abstract`, `doi_url`, `biorxiv_url`, `matched_in`).

## Quality Gates

- A `--days` filter on arXiv is reported as a local filter on the returned page.
- The bioRxiv answer states the interval and `reached_scan_limit`.
- The answer separates preprints from peer-reviewed literature.
