---
name: pdf-to-md
description: >-
  Convert any PDF (or DOCX/PPTX/XLSX/image) to clean Markdown. For scientific
  papers, produce the canonical paper-to-md bundle (Markdown plus section_audit.json
  and article.json) using the remote OCR API when an OCR key is available, or
  LiteParse v2 locally when it is not. For any non-paper PDF, defer to a fast,
  local, no-API-key LiteParse v2 conversion. Use when turning a PDF or manuscript
  into Markdown, extracting article structure, or preparing input for csag-extraction.
license: CC0-1.0
metadata:
  version: "1.0.0"
---

# pdf-to-md

Turn a PDF into Markdown. The right path depends on **what the document is** and
**whether an OCR API key is available**:

- **Scientific paper** → produce the canonical `paper-to-md` bundle (Markdown +
  `section_audit.json` + `article.json`) so it can feed `csag-extraction`.
  Convert with the **OCR API** when a key is set, else **LiteParse v2** locally.
- **Any other PDF** (reports, slides, letters, forms) → just convert to Markdown
  with **LiteParse v2** for a fast, local, no-key result. Stop there.

**LiteParse must be v2** ([run-llama/liteparse](https://github.com/run-llama/liteparse),
the Rust rewrite with the `LiteParse` Python API and `lit` CLI). LiteParse v1 is a
different, unsupported API. `liteparse_to_md.py` pins `liteparse>=2,<3` and refuses
to run on anything else, so `uv run` always provisions the right per-platform v2
binary inside the wheel — nothing to vendor or compile, and no API key. OCR is on by
default (bundled Tesseract).

**LiteParse output is a draft, not the deliverable.** LiteParse is a *mechanical*
parser: it has no native Markdown, infers headings from font size/weight, and
introduces artifacts (split words, broken hyphenation, dropped author blocks, merged
columns). Whenever LiteParse is the engine, the LLM running this skill is responsible
for shaping that draft into the right form — see "Shape the LiteParse output" below.
The OCR API engine needs far less shaping.

## Instructions

### Step 0 — Classify the document and pick a path

| Document | OCR key set? | Path |
|----------|--------------|------|
| Scientific paper / manuscript | yes (`OCR_API_KEY` or `NELLI_API_KEY`) | Mode A, engine = OCR API |
| Scientific paper / manuscript | no | Mode A, engine = LiteParse v2 |
| Anything else (fast Markdown) | n/a | Mode B (LiteParse v2 only) |

Check for a key with `printenv OCR_API_KEY NELLI_API_KEY`. If the paper is
scanned or layout-heavy and no key is set, LiteParse v2 still works (it OCRs
locally), but layout fidelity is lower than the OCR API.

### Mode A — Scientific paper (full bundle)

Produces, beside the input, for stem `<stem>`:
`<stem>.md`, `<stem>.section_audit.json`, `<stem>.article.json`
(and optionally `<stem>.ocr.json`, `<stem>.job.json`, `figure_review/`).

1. **Convert to Markdown** with the first engine that fits.

   OCR API (preferred when a key is available; best layout fidelity):

   ```bash
   uv run skills/pdf-to-md/scripts/ocr_api_job.py \
     /path/to/input.pdf --output-dir /path/to/output-dir
   ```

   The helper auto-detects a local OCR host (`http://127.0.0.1:8002/ocr`) and
   otherwise uses the remote API (`https://api.newlineages.com/ocr`). Override
   with `OCR_BASE_URL` or `--base-url`.

   LiteParse v2 fallback (no key required):

   ```bash
   uv run skills/pdf-to-md/scripts/liteparse_to_md.py \
     /path/to/input.pdf --output-dir /path/to/output-dir
   ```

   If you used the LiteParse engine, **shape `<stem>.md` before continuing** —
   see "Shape the LiteParse output" below. The downstream steps only work as well
   as the Markdown they read.

2. **Build the section audit:**

   ```bash
   uv run skills/pdf-to-md/scripts/build_section_audit.py /path/to/output-dir/<stem>.md
   ```

3. **Populate the first-pass article JSON** (also writes the audit):

   ```bash
   uv run skills/pdf-to-md/scripts/populate_article_json.py /path/to/output-dir/<stem>.md
   ```

   This is a *first pass*. Review and complete fields the heuristics miss
   (authors with superscripts, methods, references, figure interpretation)
   against the Markdown and the article schema.

4. **Render figure pages** when figure/table captions are present, then fill
   `figure_interpretation` from captions plus the rendered pages:

   ```bash
   uv run skills/pdf-to-md/scripts/render_pdf_pages_to_png.py \
     /path/to/input.pdf --output-dir /path/to/output-dir/figure_review
   ```

5. **Validate** against the schema and the section audit:

   ```bash
   uv run skills/pdf-to-md/scripts/validate_article_json.py \
     /path/to/output-dir/<stem>.article.json \
     --scientific-paper \
     --section-audit /path/to/output-dir/<stem>.section_audit.json
   ```

   Resolve every reported error before stopping. A missing field that is
   genuinely absent from the source is fixed by confirming absence, not by
   inventing content.

You may also start Mode A from a Markdown file you already trust — skip step 1
and run steps 2–5 on that `.md`.

### Mode B — Any other PDF (fast Markdown)

One step, fully local, no key:

```bash
uv run skills/pdf-to-md/scripts/liteparse_to_md.py \
  /path/to/input.pdf --output-dir /path/to/output-dir
```

Useful flags: `--no-ocr` (faster on text-based PDFs), `--ocr-server-url URL`
(higher-accuracy OCR server), `--target-pages "1-5,10"`, `--max-pages N`,
`--password PW`. The converter detects the title and section headings from font
size and weight, filters page furniture (watermarks, running headers, repeated
footers), and reflows text into paragraphs — then **shape the result** (next section).

### Shape the LiteParse output (required when LiteParse is the engine)

LiteParse v2 gives a fast first draft. Because it is mechanical, you (the LLM
running this skill) must read `<stem>.md` against the rendered pages and bring it
into the right shape before treating the conversion as done. Do not hand back raw
script output. Fix what the heuristics cannot:

- **Title** — confirm `# ` is the real title, not a journal banner, DOI line, or
  "Downloaded from…" watermark; set it correctly if wrong or missing.
- **Headings** — promote section headings the font heuristic missed (`## Abstract`,
  `## Introduction`, `## Methods`, `## Results`, `## Discussion`, `## References`,
  etc.) and demote false positives; keep reading order.
- **Broken words** — rejoin words split mid-token (e.g. "Berke ley" → "Berkeley")
  and fix hyphenation that did not rejoin across line breaks.
- **Front matter** — reconstruct the author list and affiliations, which LiteParse
  often drops or scrambles around superscripts and email addresses.
- **Captions & tables** — keep one figure/table caption per block; rebuild simple
  tables that collapsed into runs of text.
- **Residual furniture** — delete any leftover running headers, page numbers, or
  license boilerplate the filter missed.
- **References** — ensure each reference is its own entry, not one merged blob.

For **Mode A**, after this Markdown cleanup run `populate_article_json.py`, then
complete every `article.json` field the first-pass heuristics leave empty
(`authors`, `affiliations`, `methods`, `references`, `figure_interpretation`) from
the shaped Markdown and rendered pages, so validation passes for the right reasons —
never by inventing content. For **Mode B**, the shaped Markdown is the deliverable.

## Quick Reference

| Task | Command |
|------|---------|
| Is there an OCR key? | `printenv OCR_API_KEY NELLI_API_KEY` |
| Paper, key set | `ocr_api_job.py INPUT.pdf --output-dir DIR` |
| Paper, no key | `liteparse_to_md.py INPUT.pdf --output-dir DIR` |
| Any PDF, fast | `liteparse_to_md.py INPUT.pdf --output-dir DIR --no-ocr` |
| Section audit | `build_section_audit.py DIR/<stem>.md` |
| Article JSON | `populate_article_json.py DIR/<stem>.md` |
| Figure PNGs | `render_pdf_pages_to_png.py INPUT.pdf --output-dir DIR/figure_review` |
| Validate paper | `validate_article_json.py DIR/<stem>.article.json --scientific-paper --section-audit DIR/<stem>.section_audit.json` |

All commands run from the repo root with `uv run skills/pdf-to-md/scripts/<name>`.
`liteparse_to_md.py` and `render_pdf_pages_to_png.py` carry PEP 723 inline
dependencies (`liteparse`, `pypdfium2`) that `uv run` installs automatically; the
remaining scripts are standard-library only.

## Input Requirements

- A PDF, or a format LiteParse converts to PDF first (DOCX/PPTX/XLSX/ODT/CSV via
  LibreOffice; JPG/PNG/TIFF/etc. via ImageMagick).
- For Mode A from existing Markdown: a `.md` with a clear `# Title`, an
  author/affiliation block, recognizable section headings (Abstract, Introduction,
  Methods, Results, Discussion, Conclusion, References), and figure/table captions
  starting with `Fig.`/`Figure`/`Table`.
- For the OCR API engine: `OCR_API_KEY` or `NELLI_API_KEY`, plus `curl`.
- A writable `--output-dir` (keep it outside this repository).

## Output

- **Mode B:** `<stem>.md`, plus `<stem>.ocr.json` and `<stem>.job.json` provenance.
- **Mode A:** the above plus `<stem>.section_audit.json` and `<stem>.article.json`;
  optionally `figure_review/` PNGs. `csag-extraction` consumes `<stem>.md` and
  `<stem>.article.json`; everything else is provenance.
- The article JSON has exactly these keys: `title`, `authors`, `affiliations`,
  `abstract`, `main`, `methods`, `figure_legends` (list), `figure_interpretation`,
  `references` (list). See `references/article_schema.md` and `references/article.yaml`.

## Quality Gates

- The conversion engine is **LiteParse v2** (or the OCR API); `<stem>.job.json`
  records `tool_version` 2.x for the LiteParse engine.
- When LiteParse was the engine, the Markdown has been **shaped** (title, headings,
  rejoined words, front matter, captions, references) — not handed back raw.
- Mode B Markdown is non-empty, has a sensible `#` title (or none, never a
  watermark), and is free of repeated page furniture.
- Mode A: `validate_article_json.py --scientific-paper` returns `OK`.
- `title`, `authors`, and `main` are populated for a real paper, or their absence
  is confirmed against the source (do not fabricate).
- When figure/table captions exist, `figure_legends` is populated and
  `figure_interpretation` is filled (or an explicit no-interpretation note is
  recorded).
- Provenance (`<stem>.job.json`) records the engine, tool version, and OCR setting.
- No test inputs or outputs are written inside this repository.

## Examples

Fast Markdown from a non-paper PDF:

```bash
uv run skills/pdf-to-md/scripts/liteparse_to_md.py report.pdf --output-dir /tmp/out --no-ocr
# -> /tmp/out/report.md  (+ report.ocr.json, report.job.json)
```

Full paper bundle with no OCR key (LiteParse v2 engine):

```bash
DIR=/tmp/paper
uv run skills/pdf-to-md/scripts/liteparse_to_md.py paper.pdf --output-dir "$DIR"
uv run skills/pdf-to-md/scripts/populate_article_json.py "$DIR/paper.md"
uv run skills/pdf-to-md/scripts/validate_article_json.py \
  "$DIR/paper.article.json" --scientific-paper \
  --section-audit "$DIR/paper.section_audit.json"
```

## Troubleshooting

- **`liteparse is not installed`**: run the script with `uv run skills/pdf-to-md/scripts/liteparse_to_md.py` (not `uv run python ...`), so `uv` reads the PEP 723 inline dependency. Offline: `pip install 'liteparse>=2,<3'` first.
- **`pdf-to-md requires LiteParse v2`**: a v1 (or non-v2) `liteparse` is installed. Reinstall with `pip install 'liteparse>=2,<3'`; the skill targets the run-llama Rust rewrite (`LiteParse` Python API), not the old v1 API.
- **Title is a journal banner, watermark, or "Downloaded from…" line**: the converter filters furniture and repeated headers; if one slips through, remove it in the Markdown before step 2, or note that `article_extraction` re-derives the title from the body.
- **`authors`/`methods`/`references` empty on a real paper**: the first-pass heuristics miss superscript-heavy author lines and short note formats. Fill them by hand from the Markdown; this is expected, not a converter failure.
- **Scanned/image-only PDF gives little text**: keep OCR enabled (default) and raise `--dpi`, or point `--ocr-server-url` at EasyOCR/PaddleOCR; for best fidelity use the OCR API engine.
- **`Missing OCR API key`**: set `OCR_API_KEY`/`NELLI_API_KEY`, or use the LiteParse v2 engine instead.
- **Garbled equations or merged columns**: LiteParse is the fast path; for layout-heavy papers prefer the OCR API engine.
