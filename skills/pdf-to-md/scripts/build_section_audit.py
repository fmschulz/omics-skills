#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from article_extraction import build_section_audit, default_audit_path, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a section audit JSON from OCR markdown before schema population."
    )
    parser.add_argument("markdown_path", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    markdown_path = args.markdown_path.expanduser().resolve()
    if not markdown_path.exists():
        raise FileNotFoundError(markdown_path)

    output_path = args.output.expanduser().resolve() if args.output else default_audit_path(markdown_path)
    audit = build_section_audit(markdown_path)
    write_json(output_path, audit)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
