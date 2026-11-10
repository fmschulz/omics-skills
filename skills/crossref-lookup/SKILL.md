---
name: crossref-lookup
description: Query Crossref to validate DOIs, match titles to DOIs, fetch citation metadata and audit bibliographies; also report OpenAlex citation counts. Use when resolving references, cleaning citation records, or comparing papers by citations.
---

# Crossref Lookup

Validate DOIs, find DOIs from titles, and audit bibliographies against the Crossref REST API. Installed at `~/.agents/skills/crossref-lookup`; the CLI is `~/.agents/skills/crossref-lookup/scripts/lookup`.

## Instructions

1. Choose the narrowest mode:
   - `--doi` validates or enriches one DOI.
   - `--title` returns ranked DOI candidates for a title (`--rows`, default 5).
   - `--validate-file` checks one DOI per line.
   - `--audit-bibliography` extracts DOIs from a `.bib` or plain-text file and checks each one.
2. DOI inputs are normalized before lookup: `10.xxxx/...`, `doi:10.xxxx/...` and `https://doi.org/10.xxxx/...` are accepted, and trailing BibTeX punctuation is removed.
3. Pass `--email` only with an address the user gave for Crossref's polite pool. Never take an address from the conversation, git config or system context; without one the CLI uses the public pool. The CLI spaces requests to stay within Crossref's limits: single-DOI lookups at 5 per second (10 with `--email`), title searches at 1 per second (3 with `--email`).
4. When a title search returns several plausible records, show the candidates instead of choosing one silently.
5. Crossref holds citation metadata, not full text. When exact wording, pagination or publisher formatting matters, check the DOI landing page.
6. Use `--strict` for audits that must fail on any invalid, missing or unresolved record. `--output FILE` writes the report (refuses to overwrite).

```bash
L=~/.agents/skills/crossref-lookup/scripts/lookup
$L --doi 10.1038/nature12373
$L --title "CRISPR-Cas9 genome editing" --rows 5
$L --audit-bibliography refs.bib --strict --output crossref-audit.json
```

## Citation impact (OpenAlex)

`~/.agents/skills/crossref-lookup/scripts/measure-impact --doi 10.1038/nature12373 --format text` reports OpenAlex citation counts and a journal impact factor from a small manual table (2024 values). Keep paper-level and journal-level metrics separate. Altmetric is sent only with `--altmetric`, and its key (`ALTMETRIC_API_KEY`, environment only) is never printed. Options, the email rule for `--mailto`, caching and the journal table are in `references/impact.md`.

## Input Requirements

`uv` and network access (the wrapper runs a PEP 723 script that pins `requests`), and one of: a DOI, a title, a DOI list file, or a bibliography file.

## Output

JSON on stdout, or in the `--output` file:

- `--doi`: `status`, `doi`, `detail`, `title`, `journal`, `year`
- `--title`: `query` and `candidates` with `doi`, `title`, `journal`, `year`
- `--validate-file` and `--audit-bibliography`: `records`, `counts` per status (`valid`, `invalid`, `not_found`, `transient_error`, `http_error`), and `potentially_missing_dois` (BibTeX titles without a DOI; a coverage gap, not proof of invalid citations)

Exit codes: 0 on success; 1 for an invalid or missing single DOI, a strict-mode audit failure, or a refused overwrite; 2 for transient service or network failures (HTTP 429, 5xx, timeouts). Exit 2 means rerun later.

## Quality Gates

- `transient_error` records are reported as unchecked, not as invalid.
- `not_found` means Crossref has no record. DataCite and other agencies register DOIs that Crossref does not hold, so check the landing page before calling a citation wrong.
