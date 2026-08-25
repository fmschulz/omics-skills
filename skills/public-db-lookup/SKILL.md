---
name: public-db-lookup
description: Fetch bounded JSON records from UniProt, NCBI Entrez, NCBI Datasets, MGnify, InterPro, AlphaFold DB, STRING, or ENA over HTTP GET. Use when looking up an accession, taxon, entry, or structure record from a public database.
---

# Public Database Lookup

One bounded GET against a public life-science REST API. The bundled script picks the base URL, adds a User-Agent, retries on 429 and 5xx, and prints a compact JSON envelope instead of the full payload.

## Instructions

1. Pick the service that owns the record: `uniprot`, `ncbi-entrez`, `ncbi-datasets`, `mgnify`, `interpro`, `alphafold`, `string`, or `ena`.
2. Read the card for that service in [references/services.md](references/services.md) for the path, parameters, and the right `--record-path`.
3. Run the wrapper:
   - In this repository: `skills/public-db-lookup/scripts/lookup`
   - After installation: `~/.agents/skills/public-db-lookup/scripts/lookup`
4. Keep `--max-items` small (default 5). Raise it only when the user needs more rows.
5. When the full payload matters, add `--save-raw PATH` and work from the file; the envelope still carries the compacted view.
6. For the two NCBI services, export `NCBI_API_KEY` and `NCBI_EMAIL` (and `NCBI_TOOL` if you have one). The script adds them as request parameters and redacts the key from its output.
7. Route PubMed and PMC literature searches to `/polars-dovmed` and JGI data to `/jgi-lakehouse`; this skill does not cover them.

### Execution behavior

- Summarize the JSON envelope in Markdown by default.
- Return raw JSON only when the user asks for machine-readable output.
- When the payload is large, use `--save-raw` and report the path instead of pasting the content.
- Re-run the lookup rather than trust tool output from earlier in a long conversation.

## Quick Reference

| Flag | Meaning |
|------|---------|
| `--service NAME` | One of the eight services (required) |
| `--path PATH` | Endpoint path relative to the service base URL, or a full URL under that base (required) |
| `--param KEY=VALUE` | Query parameter; repeat as needed |
| `--record-path a.b.c` | Dotted path to the record list; inferred from common keys when omitted |
| `--max-items N` | Records, list items, and dict keys kept per level (default 5) |
| `--max-depth N` | Nesting depth kept before containers collapse (default 3) |
| `--format auto\|json\|text` | Parse as JSON, or keep the first 800 characters of text (default auto) |
| `--save-raw PATH` | Write the full response body to PATH |
| `--timeout SEC` | Request timeout (default 30) |

## Input Requirements

- `uv` and network access; the PEP 723 script installs its pinned HTTP dependency
- A service name and an endpoint path from the service card
- Optional query parameters, one `--param` each
- Optional `NCBI_API_KEY`, `NCBI_EMAIL`, `NCBI_TOOL` in the environment for NCBI services

## Output

One JSON object on stdout.

- Success: `ok`, `source`, `url` (api_key value removed), `status_code`, `warnings`, `raw_output_path` (the path given to `--save-raw`, else null), plus one of:
  - list results: `record_path`, `record_count_returned`, `record_count_available`, `truncated`, `records`
  - other JSON: `summary`, `top_keys`
  - text: `text_head`, `text_head_truncated`
- Failure: `ok: false`, `source`, and `error` with `code` (`invalid_input`, `network_error`, `http_error`, `invalid_response`) and `message`
- Exit code 0 on success, 2 for `invalid_input`, 1 for the other errors
- Compaction: strings cut at 240 characters, lists at `--max-items` with a trailing count marker, dicts at `--max-items` keys with a `_truncated_keys` count, deeper containers replaced by an ellipsis

## Quality Gates

- [ ] `--max-items` is the smallest count that answers the question
- [ ] `--record-path` matches the service card, or the inferred path in the envelope is the intended list
- [ ] NCBI credentials come from the environment, never from the command line
- [ ] `warnings` and `truncated` from the envelope reach the user
- [ ] Every accession or identifier in the reply came from the response, not from memory

## Troubleshooting

**Issue**: `http_error` with HTTP 429 after retries.

**Solution**: The service is rate limiting you. Wait, lower the request rate, and for NCBI set `NCBI_API_KEY` to raise the allowed rate.

**Issue**: `records` is empty or the envelope falls back to `summary` with a warning.

**Solution**: The record list is not under an inferred key. Read `top_keys` and pass the right `--record-path` from the service card.

**Issue**: NCBI rejects or throttles requests that carry no contact details.

**Solution**: Export `NCBI_EMAIL` and `NCBI_TOOL`; NCBI asks for both on every E-utilities request.

## Non-Goals

- No POST requests, ID-mapping jobs, or other asynchronous job APIs
- No bulk downloads of sequence or structure files
- No literature search; use `/polars-dovmed`
- No JGI data access; use `/jgi-lakehouse`
