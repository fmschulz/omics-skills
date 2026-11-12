# Citation impact (OpenAlex)

`scripts/measure-impact` reports paper-level citation data from OpenAlex.

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
- `OPENALEX_API_KEY` is optional and read only from the environment (there is no key option). It is sent as `Authorization: Bearer` (OpenAlex also takes an `api_key` URL parameter, which this script avoids so the key stays out of URLs and cache names). Without a key OpenAlex allows 10 requests per second, with a free key 30 (checked 2026-11 at https://help.openalex.org/api/authentication/). The key is never printed and is removed from error messages.
- HTTP 429 is retried, 4 attempts in all. The wait is the `Retry-After` value when present, else 2, 4 and 8 seconds, and never more than 60 seconds. After the last attempt the command exits 1 with the HTTP error.
- `--output FILE` refuses to overwrite an existing file; pass `--force` to replace it. `lookup --output` follows the same rule.
- Altmetric is optional and off by default: a set `ALTMETRIC_API_KEY` alone sends nothing. Pass `--altmetric` to request it. The key comes only from the environment (there is no key option, so it never appears in argv), and it is never printed, not even in an error. Without `--altmetric` the report says `altmetric.status: unavailable` (`not_requested`); with the flag and no key, `no_api_key`. A keyless request to `api.altmetric.com` returned HTTP 403 when checked in 2026-10.

## Reporting

Citation counts depend on the field and the age of the paper; compare like with like. Attention scores are not scholarly citation impact.

## Tests

`tests/test_measure_impact.py` (repository only) uses the fixtures in `fixtures/`.
