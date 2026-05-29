#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pypdfium2", "pillow"]
# ///
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pypdfium2 as pdfium


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render PDF pages to PNG files for figure review."
    )
    parser.add_argument("input_pdf", type=Path, help="Path to the input PDF")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for PNG output")
    parser.add_argument("--dpi", type=int, default=144, help="Rendering DPI (default: 144)")
    parser.add_argument("--first-page", type=int, default=None, help="First page to render (1-based)")
    parser.add_argument("--last-page", type=int, default=None, help="Last page to render (1-based)")
    parser.add_argument("--prefix", default="page", help="PNG filename prefix (default: page)")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.dpi <= 0:
        raise SystemExit("--dpi must be positive")
    if args.first_page is not None and args.first_page <= 0:
        raise SystemExit("--first-page must be positive")
    if args.last_page is not None and args.last_page <= 0:
        raise SystemExit("--last-page must be positive")
    if (
        args.first_page is not None
        and args.last_page is not None
        and args.first_page > args.last_page
    ):
        raise SystemExit("--first-page cannot be greater than --last-page")


def render_pages(args: argparse.Namespace) -> list[Path]:
    input_pdf = args.input_pdf.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    if not input_pdf.exists():
        raise SystemExit(f"Input PDF does not exist: {input_pdf}")

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf = pdfium.PdfDocument(str(input_pdf))
    page_count = len(pdf)

    first_page = args.first_page or 1
    last_page = args.last_page or page_count
    if first_page > page_count:
        raise SystemExit(f"--first-page {first_page} exceeds PDF page count {page_count}")
    if last_page > page_count:
        last_page = page_count

    pattern = re.compile(rf"^{re.escape(args.prefix)}-(\d+)\.png$")
    pngs: list[Path] = []
    scale = args.dpi / 72.0
    for page_number in range(first_page, last_page + 1):
        page = pdf[page_number - 1]
        bitmap = page.render(scale=scale)
        image = bitmap.to_pil()
        output_path = output_dir / f"{args.prefix}-{page_number}.png"
        image.save(output_path)
        if pattern.match(output_path.name):
            pngs.append(output_path)
    if not pngs:
        raise SystemExit("No PNG files were produced")
    return pngs


def write_manifest(output_dir: Path, pngs: list[Path]) -> Path:
    manifest_path = output_dir / "render_manifest.json"
    manifest = {
        "page_count": len(pngs),
        "pages": [
            {
                "path": str(path),
                "name": path.name,
            }
            for path in pngs
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def main() -> int:
    args = parse_args()
    validate_args(args)
    pngs = render_pages(args)
    manifest_path = write_manifest(args.output_dir.expanduser().resolve(), pngs)
    for path in pngs:
        print(path)
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
