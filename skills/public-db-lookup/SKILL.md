---
name: public-db-lookup
description: Fetch compact JSON records from UniProt, NCBI, MGnify, InterPro, AlphaFold DB, STRING, or ENA. Use when looking up an accession, taxon, entry, or structure in a public database.
---

# Public Database Lookup

One bounded GET against a public life-science REST API. The bundled script picks the base URL, adds a User-Agent, retries on 429 and 5xx, and prints a compact JSON envelope instead of the full payload. Flags: `~/.agents/skills/public-db-lookup/scripts/lookup --help`.

## Instructions

1. Pick the service that owns the record: `uniprot`, `ncbi-entrez`, `ncbi-datasets`, `mgnify`, `interpro`, `alphafold`, `string`, or `ena`.
2. Read the card for that service in [references/services.md](references/services.md) for the path, parameters, and the right `--record-path`. When `records` is empty or the envelope falls back to `summary` with a warning, read `top_keys` and pass the card's `--record-path`.
3. Run `~/.agents/skills/public-db-lookup/scripts/lookup --service NAME --path PATH [--param KEY=VALUE ...]`.
4. Keep `--max-items` small (default 5). Raise it only when the user needs more rows.
5. When the full payload matters, add `--save-raw PATH` and work from the file; the envelope still carries the compacted view. Report the path instead of pasting a large payload.
6. For the two NCBI services, the script reads `NCBI_API_KEY` and `NCBI_TOOL` from the environment and adds them as request parameters. A contact address is sent only when you pass `--email ADDRESS`, and only with an address the user gave for this purpose, never one from the conversation, git config or system context. The script removes the key and the address from the printed URL, errors and response text.
7. Requests are paced across invocations, so calling the CLI in a loop stays inside each service's documented rate. The timestamps live under `$XDG_STATE_HOME/omics-skills/public-db-lookup`; override with `--state-dir`. On HTTP 429 after retries, wait and lower the request rate; for NCBI set `NCBI_API_KEY`. Never pass a credential in `--path` or `--param`: the script refuses it, because it would be echoed back in the emitted URL and land in shell history.
8. Route PubMed and PMC literature searches to `/polars-dovmed`; this skill does not cover them.

## Input Requirements

- `uv` and network access; the PEP 723 script installs its HTTP dependency.
- A service name and an endpoint path from the service card.

## Output

One JSON object on stdout. Exit code 0 on success, 2 for `invalid_input`, 1 for the other errors.

- Success: `ok`, `source`, `url` (api_key and email values removed), `status_code`, `warnings`, `raw_output_path`, plus `records` with `record_path`, `record_count_returned`, `record_count_available` (the service total when the response reports one, such as esearch `count` or a top-level `count`; else the length of the returned list) and `truncated` for list results, `summary` and `top_keys` for other JSON, or `text_head` for text (first 800 characters, with `text_head_truncated` set when the text is longer).
- Failure: `ok: false`, `source`, and `error` with `code` (`invalid_input`, `network_error`, `http_error`, `invalid_response`, `service_error` for an HTTP 200 reply with an error body) and `message`.
- Compaction: strings are cut at 240 characters; lists and dicts at `--max-items`; containers deeper than `--max-depth` (default 3) collapse.

## Quality Gates

- [ ] `--max-items` is the smallest count that answers the question.
- [ ] `--record-path` matches the service card, or the inferred path in the envelope is the intended list.
- [ ] `warnings` and `truncated` from the envelope reach the user.
- [ ] Every accession or identifier in the reply came from the response, not from memory.

## Non-Goals

- No POST requests, ID-mapping jobs, or other asynchronous job APIs.
- No bulk downloads of sequence or structure files.
- No JGI-internal data access (GOLD, IMG, JAMO); this skill covers public endpoints only.
