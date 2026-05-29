#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from article_extraction import (
    build_article_from_audit,
    build_section_audit,
    default_audit_path,
    write_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Populate a first-pass Article-schema JSON file from OCR markdown."
    )
    parser.add_argument("markdown_path", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--audit-output",
        type=Path,
        default=None,
        help="Path to write the section audit JSON. Defaults to <stem>.section_audit.json.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    markdown_path = args.markdown_path.expanduser().resolve()
    if not markdown_path.exists():
        raise FileNotFoundError(markdown_path)

    output_path = args.output.expanduser().resolve() if args.output else markdown_path.with_suffix(".article.json")
    audit_output_path = args.audit_output.expanduser().resolve() if args.audit_output else default_audit_path(markdown_path)

    audit = build_section_audit(markdown_path)
    write_json(audit_output_path, audit)

    article = build_article_from_audit(audit)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(article, indent=2) + "\n", encoding="utf-8")

    print(audit_output_path)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
