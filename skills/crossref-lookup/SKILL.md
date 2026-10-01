---
name: crossref-lookup
description: Query Crossref to validate DOIs, match titles to DOIs, fetch citation metadata, and audit bibliographies. Use when resolving references or cleaning citation records.
---

# Crossref Lookup

Validate DOIs, find DOIs from titles, and audit bibliographies against the Crossref REST API.

## Instructions

1. Run the bundled CLI, `scripts/lookup`. Paths below are relative to this skill's directory, installed at `~/.agents/skills/crossref-lookup`.
2. Choose the narrowest mode:
   - `--doi` validates or enriches one DOI.
   - `--title` returns ranked DOI candidates for a title (`--rows`, default 5).
   - `--validate-file` checks one DOI per line.
   - `--audit-bibliography` extracts DOIs from a `.bib` or plain-text file and checks each one.
3. DOI inputs are normalized before lookup. `10.xxxx/...`, `doi:10.xxxx/...`, and `https://doi.org/10.xxxx/...` are all accepted, and trailing BibTeX punctuation is removed.
4. Pass `--email` to identify the caller and use Crossref's polite pool. The CLI spaces requests to stay within the limits Crossref reported on 2026-10-01: single-DOI lookups at 5 per second (10 with `--email`), title searches at 1 per second (3 with `--email`).
5. When a title search returns several plausible records, show the candidates instead of choosing one silently.
6. Crossref holds citation metadata, not full text. When exact wording, pagination, or publisher formatting matters, check the DOI landing page.
7. Use `--strict` for audits that must fail on any invalid, missing, or unresolved record.

## Quick Reference

| Task | Command |
|------|---------|
| Validate a DOI | `scripts/lookup --doi 10.1038/nature12373` |
| Search by title | `scripts/lookup --title "CRISPR-Cas9 genome editing" --rows 5` |
| Validate a DOI list | `scripts/lookup --validate-file dois.txt` |
| Audit a bibliography | `scripts/lookup --audit-bibliography refs.bib` |
| Write the report to a file | `--output crossref-report.json` (refuses to overwrite) |
| Polite pool | `--email you@example.org` |
| Fail on any unresolved record | `--strict` |

## Input Requirements

- `uv` and network access; the wrapper runs the PEP 723 script, which pins `requests`.
- One of: a DOI, a title, a DOI list file, or a bibliography file.
- Optional: `--email`, `--rows`, `--output`, `--strict`.

## Output

JSON on stdout, or in the `--output` file:

- `--doi`: `status`, `doi`, `detail`, `title`, `journal`, `year`
- `--title`: `query` and `candidates` with `doi`, `title`, `journal`, `year`
- `--validate-file` and `--audit-bibliography`: `records`, `counts` per status (`valid`, `invalid`, `not_found`, `transient_error`, `http_error`), and `potentially_missing_dois` (BibTeX titles without a DOI)

Exit codes: 0 on success; 1 for an invalid or missing single DOI, a strict-mode audit failure, or a refused overwrite; 2 for transient service or network failures (HTTP 429, 5xx, timeouts).

## Quality Gates

- [ ] The lookup mode matches the request.
- [ ] DOIs were normalized before any was reported as invalid.
- [ ] Ambiguous title matches are shown as candidates.
- [ ] `transient_error` records are reported as unchecked, not as invalid.
- [ ] The answer separates Crossref metadata from publisher full text; reference formatting is left to the citation manager.

## Examples

```bash
scripts/lookup --doi "10.1038/nature12373"

scripts/lookup --title "CRISPR-Cas9 genome editing" --email you@example.org

scripts/lookup --audit-bibliography refs.bib --strict --output crossref-audit.json
```

## Troubleshooting

**Issue**: A DOI looks valid but Crossref returns `not_found`.
**Solution**: Report that Crossref has no record. DataCite and other agencies register DOIs that Crossref does not hold, so check the DOI landing page before calling the citation wrong.

**Issue**: Many bibliography entries have no DOI.
**Solution**: Treat `potentially_missing_dois` as a coverage gap, not proof of invalid citations.

**Issue**: Exit code 2.
**Solution**: Crossref rate-limited the run or was unreachable. Wait, add `--email`, and rerun.

## Related Skills

- `/polars-dovmed`: full-text PMC Open Access search when the DOI is unknown
- `/arxiv-search` and `/biorxiv-search`: preprint search
- `/scientific-impact-assessment`: citation counts and journal impact
