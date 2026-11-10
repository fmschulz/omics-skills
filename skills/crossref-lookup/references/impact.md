# Citation impact (OpenAlex)

`scripts/measure-impact` reports paper-level citation data from OpenAlex and journal-level context from a small manual table.

```bash
S=~/.agents/skills/crossref-lookup/scripts
$S/measure-impact --doi 10.1038/nature12373 --format text
$S/measure-impact --openalex-id W2741809807 --output impact-report.json
```

## Behaviour

- Input is a DOI or an OpenAlex work ID. With only a title, resolve a DOI first with `scripts/lookup --title`.
- OpenAlex returns `cited_by_count`, publication year, journal name and citation counts by year.
- Repeated OpenAlex lookups use a response cache and a cross-process pacing lock. Defaults: `--cache-ttl 86400`, `--min-interval 0.1`. Set `--cache-dir` or `OPENALEX_CACHE_DIR` for a project or site cache. Live reports record this request policy.
- `--mailto ADDRESS` adds the OpenAlex polite-pool address. Use it only when the user gave an address for this purpose; no environment variable supplies it.
- Altmetric is optional and off by default: a set `ALTMETRIC_API_KEY` alone sends nothing. Pass `--altmetric` to request it. The key comes only from the environment (there is no key option, so it never appears in argv), and it is never printed, not even in an error. Without `--altmetric` the report says `altmetric.status: unavailable` (`not_requested`); with the flag and no key, `no_api_key`. A keyless request to `api.altmetric.com` returned HTTP 403 when checked in 2026-10.
- A journal missing from the table: return the OpenAlex result and say the journal lookup was not available.

## Journal table

`journal_metrics_2024.tsv` is a small manual table: 13 journals, metric year 2024, verified 2026-03-19, columns `journal_name`, `category`, `metric_name`, `metric_year`, `value`, `source_url`, `source_kind`, `verified_date`, `aliases`, `notes`.

- Values are public web values, mostly from official publisher pages. Rows with `source_kind` `third_party` (the `Science` row: no public official AAAS page was found) must be labeled as third-party in the answer.
- Clarivate's Journal Impact Factor is licensed. The table is a convenience reference, not a substitute for Journal Citation Reports.
- Read impact factors from the table, never from memory.

## Reporting

Keep paper-level and journal-level metrics separate. A journal impact factor is not a proxy for article quality, and attention scores are not scholarly citation impact.

## Tests

`tests/test_scientific_impact_assessment.py` (repository only) uses the fixtures in `fixtures/`.
