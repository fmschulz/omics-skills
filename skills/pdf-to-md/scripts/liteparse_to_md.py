#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["liteparse>=2,<3"]
# ///
"""Convert a PDF (or DOCX/PPTX/XLSX/image) to Markdown with LiteParse v2.

LiteParse v2 (https://github.com/run-llama/liteparse) parses fully locally with
NO API key. OCR is on by default via bundled Tesseract; point ``--ocr-server-url``
at an HTTP OCR server (EasyOCR/PaddleOCR/custom) for higher accuracy. This is the
fast / no-key fallback for the pdf-to-md skill. For layout-heavy scientific PDFs,
``ocr_api_job.py`` (remote OCR API) is preferred when an OCR key is available.

The native parser ships inside the ``liteparse`` wheel, so running this script
with ``uv run`` auto-provisions the right per-platform executable — nothing to
vendor or compile.

Outputs mirror the OCR helper layout so downstream steps are identical:
- <stem>.md         canonical Markdown
- <stem>.ocr.json   minimal job-result stub for compatibility
- <stem>.job.json   provenance for this conversion run
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


# Section headings worth promoting to "## " even when font size alone misses them.
SECTION_HEADINGS = {
    "abstract", "summary", "introduction", "background", "results",
    "results and discussion", "discussion", "conclusion", "conclusions",
    "methods", "materials and methods", "methods and materials", "methodology",
    "experimental procedures", "data availability", "code availability",
    "acknowledgements", "acknowledgments", "author contributions",
    "competing interests", "conflicts of interest", "funding", "references",
    "bibliography", "supplementary information", "supplementary materials",
}
# Leading "1.", "2 ", "IV.", "A)" numbering on a heading line.
HEADING_NUMBER_RE = re.compile(r"^(?:\d+(?:\.\d+)*|[ivxlcdm]+|[A-Z])[.)]?\s+", re.IGNORECASE)
CAPTION_RE = re.compile(
    r"^(?:fig(?:ure)?\.?|table|supplementary\s+(?:fig(?:ure)?\.?|table))\s+[a-z0-9]+",
    re.IGNORECASE,
)
PAGE_MARKER_RE = re.compile(r"^-{2,}\s*page\s+\d+\s*-{2,}$", re.IGNORECASE)
BOLD_FONT_RE = re.compile(r"bold|black|heavy|semibold|cmbx|cmb\d|[-_ ]bd\b|bx\d", re.IGNORECASE)
# Publisher watermarks / running headers / footers that pollute heading detection.
FURNITURE_RE = re.compile(
    r"downloaded from|by guest on|academic\.oup\.com|all rights reserved|"
    r"this version posted|is the author/funder|^https?://|doi\.org/|^doi:\s|"
    r"creativecommons\.org|©\s*\d{4}|©\s*the author",
    re.IGNORECASE,
)


def load_liteparse():
    try:
        import liteparse  # noqa: F401
        return liteparse
    except ImportError as exc:  # pragma: no cover - exercised only without the dep
        raise SystemExit(
            "liteparse is not installed. Run this script with `uv run` (which "
            "auto-installs the inline dependency), or `pip install liteparse`."
        ) from exc


def liteparse_version(liteparse) -> str:
    try:
        from importlib.metadata import version
        return version("liteparse")
    except Exception:
        return getattr(liteparse, "__version__", "unknown")


def ensure_v2(liteparse) -> str:
    """This skill targets LiteParse v2 (the run-llama Rust rewrite, `LiteParse`
    Python API). v1 is a different, unsupported API. Fail clearly otherwise."""
    version = liteparse_version(liteparse)
    major = version.split(".")[0]
    if not major.isdigit() or int(major) != 2 or not hasattr(liteparse, "LiteParse"):
        raise SystemExit(
            f"pdf-to-md requires LiteParse v2 (run-llama Rust rewrite); found "
            f"version {version!r}. Install it with: pip install 'liteparse>=2,<3'"
        )
    return version


def normalize(text: str) -> str:
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")
    return re.sub(r"\s+", " ", text).strip()


def strip_numbering(text: str) -> str:
    stripped = text
    while True:
        updated = HEADING_NUMBER_RE.sub("", stripped).strip()
        if updated == stripped:
            return stripped
        stripped = updated


def normalize_heading_key(text: str) -> str:
    key = strip_numbering(normalize(text)).lower().rstrip(":.")
    return re.sub(r"[^a-z0-9 ]+", "", key).strip()


def is_furniture(line: str) -> bool:
    stripped = normalize(line)
    if not stripped:
        return False
    if PAGE_MARKER_RE.match(stripped):
        return True
    if re.fullmatch(r"\d{1,4}", stripped):  # bare page number
        return True
    if re.fullmatch(r"\d+\s*/\s*\d+", stripped):  # "3 / 12"
        return True
    return False


def build_drop_keys(pages) -> set[str]:
    """Normalized keys for lines that are page furniture: watermarks plus short
    lines repeated across two or more pages (running headers/footers)."""
    page_presence: Counter[str] = Counter()
    for page in pages:
        seen: set[str] = set()
        for raw in page.text.splitlines():
            key = normalize_heading_key(raw)
            if key and key not in seen:
                seen.add(key)
                page_presence[key] += 1
    return {key for key, count in page_presence.items() if count >= 2 and len(key.split()) <= 15}


def is_drop(text: str, drop_keys: set[str]) -> bool:
    if FURNITURE_RE.search(text):
        return True
    return normalize_heading_key(text) in drop_keys


def collect_font_signals(pages, drop_keys: set[str]) -> tuple[float, set[str], list[str]]:
    """Return (body_font_size, heading_keys, title_lines) from positioned items."""
    sizes = [
        it.font_size
        for page in pages
        for it in page.text_items
        if it.font_size and len(it.text.split()) >= 5
    ]
    if not sizes:
        sizes = [it.font_size for page in pages for it in page.text_items if it.font_size]
    body_size = statistics.median(sizes) if sizes else 0.0

    heading_keys: set[str] = set()
    for page in pages:
        for it in page.text_items:
            text = normalize(it.text)
            words = text.split()
            if not (1 <= len(words) <= 14) or is_drop(text, drop_keys):
                continue
            bigger = bool(it.font_size) and body_size and it.font_size >= body_size * 1.15
            bold = bool(it.font_name) and bool(BOLD_FONT_RE.search(it.font_name))
            if bigger or bold:
                heading_keys.add(normalize_heading_key(text))

    # Title: the largest-font, non-furniture lines on page 1, in reading order.
    title_lines: list[str] = []
    if pages and pages[0].text_items:
        sized = [it for it in pages[0].text_items if it.font_size and not is_drop(normalize(it.text), drop_keys)]
        if sized:
            top = max(it.font_size for it in sized)
            if not body_size or top >= body_size * 1.2:
                title_lines = [
                    normalize(it.text)
                    for it in sized
                    if it.font_size >= top * 0.98 and normalize(it.text)
                ]
    return body_size, heading_keys, title_lines


def to_markdown(pages, heading_keys: set[str], title_lines: list[str], drop_keys: set[str]) -> tuple[str, int]:
    out: list[str] = []
    paragraph: list[str] = []
    title_tokens: set[str] = set()
    for line in title_lines:
        title_tokens.update(normalize_heading_key(line).split())
    in_title_zone = bool(title_lines)
    heading_count = 0

    def flush() -> None:
        if paragraph:
            out.append(" ".join(paragraph).strip())
            paragraph.clear()

    if title_lines:
        out.append(f"# {' '.join(title_lines)}")
        out.append("")

    for page in pages:
        for raw in page.text.splitlines():
            line = normalize(raw)
            if not line:
                flush()
                continue
            if is_furniture(line) or is_drop(line, drop_keys):
                continue
            key = normalize_heading_key(line)
            # Drop the leading lines that just re-state the title emitted above.
            if in_title_zone:
                tokens = set(key.split())
                if tokens and tokens.issubset(title_tokens):
                    continue
                in_title_zone = False
            if key in SECTION_HEADINGS or (key and key in heading_keys):
                flush()
                out.append("")
                out.append(f"## {strip_numbering(line)}")
                out.append("")
                heading_count += 1
                continue
            if CAPTION_RE.match(line):
                flush()
                out.append("")
                out.append(line)
                out.append("")
                continue
            if line.endswith("-") and not line.endswith(" -"):
                paragraph.append(line[:-1])  # de-hyphenate across line breaks
            else:
                paragraph.append(line)
        flush()

    markdown = "\n".join(out)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip() + "\n"
    return markdown, heading_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a document to Markdown with LiteParse v2 (local, no API key)."
    )
    parser.add_argument("input_path", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--no-ocr", action="store_true",
                        help="Disable OCR (faster on text-based PDFs).")
    parser.add_argument("--ocr-server-url", default=None,
                        help="HTTP OCR server URL for higher-accuracy OCR.")
    parser.add_argument("--ocr-language", default=None, help="OCR language code, e.g. 'eng'.")
    parser.add_argument("--target-pages", default=None, help="e.g. '1-5,10,15-20'.")
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--dpi", type=float, default=None)
    parser.add_argument("--password", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = args.input_path.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    if not input_path.exists():
        raise FileNotFoundError(input_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    liteparse = load_liteparse()
    lp_version = ensure_v2(liteparse)
    config = {"output_format": "json", "quiet": True}
    if args.no_ocr:
        config["ocr_enabled"] = False
    if args.ocr_server_url:
        config["ocr_server_url"] = args.ocr_server_url
    if args.ocr_language:
        config["ocr_language"] = args.ocr_language
    if args.target_pages:
        config["target_pages"] = args.target_pages
    if args.max_pages is not None:
        config["max_pages"] = args.max_pages
    if args.dpi is not None:
        config["dpi"] = args.dpi
    if args.password:
        config["password"] = args.password

    parser = liteparse.LiteParse(**config)
    result = parser.parse(input_path)
    pages = result.pages

    drop_keys = build_drop_keys(pages)
    body_size, heading_keys, title_lines = collect_font_signals(pages, drop_keys)
    markdown, heading_count = to_markdown(pages, heading_keys, title_lines, drop_keys)

    stem = input_path.stem
    markdown_path = output_dir / f"{stem}.md"
    ocr_json_path = output_dir / f"{stem}.ocr.json"
    job_meta_path = output_dir / f"{stem}.job.json"

    markdown_path.write_text(markdown, encoding="utf-8")
    ocr_json_path.write_text(
        json.dumps(
            {
                "source": "liteparse",
                "metadata": {
                    "page_count": len(pages),
                    "body_font_size": round(body_size, 3),
                    "heading_count": heading_count,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    job_meta_path.write_text(
        json.dumps(
            {
                "tool": "liteparse",
                "tool_version": lp_version,
                "input_path": str(input_path),
                "ocr_enabled": not args.no_ocr,
                "ocr_server_url": args.ocr_server_url,
                "page_count": len(pages),
                "run_datetime": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"job={job_meta_path}")
    print(f"markdown={markdown_path}")
    print(f"json={ocr_json_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
