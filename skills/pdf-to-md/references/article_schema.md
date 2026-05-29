# Article Schema (paper-to-md)

The article JSON is the structured handoff between PDF/Markdown ingestion and CSAG extraction. Use it whenever the source is scientific literature.

## Required output shape

One JSON object with these keys and no extra top-level fields:

```json
{
  "title": "",
  "authors": "",
  "affiliations": "",
  "abstract": "",
  "main": "",
  "methods": "",
  "figure_legends": [],
  "figure_interpretation": "",
  "references": []
}
```

## Field semantics

- `title` — article title exactly as written.
- `authors` — author list as a single comma-separated string.
- `affiliations` — affiliations as a single comma-separated string.
- `abstract` — abstract text verbatim when present.
- `main` — combined narrative body (introduction + results + discussion + conclusion in reading order).
- `methods` — Methods or Materials section text only.
- `figure_legends` — one entry per figure or table caption.
- `figure_interpretation` — concise interpretation of figures/tables, grounded in captions and direct figure review.
- `references` — one entry per cited reference.

## Extraction rules

- Prefer fidelity over rewriting.
- Keep headings and section order when they help preserve structure.
- Deduplicate page headers, footers, and page numbers before structuring.
- Do not invent missing sections.
- If a section is absent, leave the field empty (`""` or `[]`); do not stuff unrelated text into it.

## Minimum content expectation

For a real scientific paper these should normally be non-empty:

- `title`, `authors`, `main`

Usually also expected when recoverable:

- `affiliations`, `abstract`, `methods`, `figure_legends`, `references`

## Validation

The repo-local validator at `scripts/validate_article_json.py` enforces:

- exact top-level key set
- correct types (strings vs lists of strings)
- non-empty `title` / `authors` / `main` for `--scientific-paper`
- consistency with the section audit when `--section-audit` is provided

The LinkML shape is in `references/article.yaml`.
