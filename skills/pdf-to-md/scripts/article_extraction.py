#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ABSTRACT_HEADINGS = {"abstract", "summary"}
STRUCTURED_ABSTRACT_HEADINGS = {
    "aim",
    "aims",
    "background",
    "conclusion",
    "conclusions",
    "findings",
    "methods",
    "objective",
    "objectives",
    "purpose",
    "results",
    "summary",
}
METHOD_HEADINGS = {
    "methods",
    "materials and methods",
    "materials methods",
    "materials method",
    "methods and materials",
    "methodology",
    "experimental procedures",
    "patients and methods",
}
REFERENCE_HEADINGS = {
    "references",
    "bibliography",
    "literature cited",
    "works cited",
}
MAIN_START_HEADINGS = {
    "introduction",
    "background",
    "results",
    "results and discussion",
    "discussion",
    "conclusion",
    "genome packaging",
}
META_HEADINGS = {
    "graphical abstract",
    "research article",
    "open access",
    "author summary",
    "keywords",
    "key words",
    "acknowledgments",
    "acknowledgements",
    "funding",
    "data availability",
    "data availability statement",
    "code availability",
    "change history",
    "competing interests",
    "conflicts of interest",
    "supporting information",
    "supplementary information",
    "supplementary materials",
    "supplementary material",
    "figures",
    "similar content being viewed by others",
    "explore related subjects",
    "author information",
    "authors and affiliations",
    "corresponding author",
    "additional information",
    "additional files",
    "electronic supplementary material",
    "authors original submitted files for images",
    "about this article",
    "cite this article",
    "share this article",
    "what is a tagged pdf",
    "profiles",
    "publisher s note",
    "ethics declarations",
    "author contributions",
    "contributions",
    "footnotes",
}
HEADING_ALIASES = {
    "materials methods": "materials and methods",
    "materials method": "materials and methods",
    "methods and materials": "materials and methods",
    "acknowledgement": "acknowledgments",
    "acknowledgements": "acknowledgments",
    "conflict of interest": "conflicts of interest",
    "conflicts of interests": "conflicts of interest",
    "competing interest": "competing interests",
    "data availability statement": "data availability",
    "key words": "keywords",
}
AFFILIATION_HINTS = (
    "department",
    "university",
    "institute",
    "faculty",
    "school",
    "center",
    "centre",
    "laboratory",
    "lab",
    "research",
    "hospital",
    "college",
    "academy",
    "national laboratory",
)
DROP_LINE_PATTERNS = (
    re.compile(r"^\s*!\[.*\]\(.*\)\s*$"),
    re.compile(r"^\s*-{3,}\s*$"),
    re.compile(r"^\s*\d+\s*/\s*\d+\s*$"),
    re.compile(r"^\s*bio\S*\s*\|", re.IGNORECASE),
    re.compile(r"^\s*.+\bet al\.\s*\|", re.IGNORECASE),
    re.compile(r"^\s*.+\|\s*https?://doi\.org/", re.IGNORECASE),
    re.compile(r"^\s*(received|accepted|published|editor):", re.IGNORECASE),
    re.compile(r"^\s*(citation|copyright):", re.IGNORECASE),
    re.compile(r"^\s*doi:\s*", re.IGNORECASE),
)
CAPTION_START_RE = re.compile(
    r"^\s*(?:fig(?:ure)?\.?|table|supplementary\s+(?:fig(?:ure)?\.?|table))\s+[a-z0-9]+(?:\.[a-z0-9]+)?\s*[:.]",
    re.IGNORECASE,
)
FIGURE_BLOCK_MARKER_RE = re.compile(
    r"^\s*(?:\d+\s+)?(?:supplementary\s+)?figures?\s*$",
    re.IGNORECASE,
)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
FOOTNOTE_MARKER_RE = re.compile(r"\$?\^\{[^}]+\}\$?")
ANGLE_URL_RE = re.compile(r"<(https?://[^>]+)>")
HTML_TAG_RE = re.compile(r"</?([A-Za-z][^>]*)>")
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.\w+\b")
HEADING_NUMBER_PREFIX_RE = re.compile(
    r"^(?:section\s+)?(?:(?:\d+(?:\.\d+)*|[ivxlcdm]+|[A-Za-z])(?:[.)]|\.)*\s+)+",
    re.IGNORECASE,
)


@dataclass
class Section:
    level: int
    heading: str
    normalized_heading: str
    start: int
    end: int
    content_lines: list[str]


def strip_markdown_inline(text: str) -> str:
    text = LINK_RE.sub(lambda match: match.group(1), text)
    text = text.replace("**", "").replace("__", "")
    text = text.replace("`", "")
    text = ANGLE_URL_RE.sub(lambda match: match.group(1), text)
    text = HTML_TAG_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_title_or_text(text: str) -> str:
    text = strip_markdown_inline(text)
    text = FOOTNOTE_MARKER_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip(" ,;")


def strip_heading_numbering(text: str) -> str:
    stripped = clean_title_or_text(text)
    while True:
        updated = HEADING_NUMBER_PREFIX_RE.sub("", stripped).strip()
        if updated == stripped:
            break
        stripped = updated
    return stripped


def normalize_heading(text: str) -> str:
    text = strip_heading_numbering(text).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    return HEADING_ALIASES.get(text, text)


def normalize_count_key(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def looks_like_repeated_furniture(text: str) -> bool:
    stripped = clean_title_or_text(text)
    if not stripped:
        return False
    lower = stripped.lower()
    if "preprint doi" in lower or "this version posted" in lower:
        return True
    if "copyright holder" in lower or "license" in lower:
        return True
    if re.fullmatch(r"\d+\s*/\s*\d+", stripped):
        return True
    if "|" in stripped and ("doi.org" in lower or "biorxiv" in lower or "plos" in lower):
        return True
    if len(stripped.split()) <= 8 and stripped.upper() == stripped and any(ch.isalpha() for ch in stripped):
        return True
    return False


def should_drop_line(text: str, counts: Counter[str]) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    for pattern in DROP_LINE_PATTERNS:
        if pattern.search(stripped):
            return True
    count_key = normalize_count_key(stripped)
    if counts[count_key] >= 2 and looks_like_repeated_furniture(stripped):
        return True
    return False


def load_clean_lines(markdown_path: Path) -> list[str]:
    raw_text = markdown_path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    raw_lines = [line.rstrip() for line in raw_text.split("\n")]
    if raw_lines and raw_lines[0].strip() == "---":
        for index in range(1, len(raw_lines)):
            if raw_lines[index].strip() == "---":
                raw_lines = raw_lines[index + 1 :]
                break
    counts = Counter(normalize_count_key(line) for line in raw_lines if normalize_count_key(line))

    cleaned: list[str] = []
    for line in raw_lines:
        if should_drop_line(line, counts):
            continue
        if cleaned and not line.strip() and not cleaned[-1].strip():
            continue
        cleaned.append(line)
    return cleaned


def parse_sections(lines: list[str]) -> list[Section]:
    heading_positions: list[tuple[int, int, str, str]] = []
    for index, line in enumerate(lines):
        match = HEADING_RE.match(line.strip())
        if not match:
            continue
        raw_heading = clean_title_or_text(match.group(2))
        heading_positions.append((index, len(match.group(1)), raw_heading, normalize_heading(raw_heading)))

    sections: list[Section] = []
    for i, (start, level, heading, normalized_heading) in enumerate(heading_positions):
        end = heading_positions[i + 1][0] if i + 1 < len(heading_positions) else len(lines)
        sections.append(
            Section(
                level=level,
                heading=heading,
                normalized_heading=normalized_heading,
                start=start,
                end=end,
                content_lines=lines[start + 1 : end],
            )
        )
    return sections


def collapse_lines(lines: list[str]) -> str:
    paragraphs: list[str] = []
    current: list[str] = []
    for raw_line in lines:
        line = clean_title_or_text(raw_line)
        if not line:
            if current:
                paragraphs.append(" ".join(current).strip())
                current = []
            continue
        if CAPTION_START_RE.match(line) or re.match(r"^[-*]\s+", line) or re.match(r"^\d+\.\s+", line):
            if current:
                paragraphs.append(" ".join(current).strip())
                current = []
            paragraphs.append(line)
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current).strip())
    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)


def split_blocks(lines: list[str]) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if not line.strip():
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line)
    if current:
        blocks.append(current)
    return blocks


def section_index_by_heading(sections: list[Section], heading_names: set[str]) -> int | None:
    for index, section in enumerate(sections):
        if section.normalized_heading in heading_names:
            return index
    return None


def collect_section_run(sections: list[Section], start_index: int) -> list[Section]:
    start_level = sections[start_index].level
    run = [sections[start_index]]
    for index in range(start_index + 1, len(sections)):
        section = sections[index]
        if section.level <= start_level:
            break
        run.append(section)
    return run


def collect_named_run(sections: list[Section], heading_names: set[str]) -> tuple[list[Section], set[int]]:
    start_index = section_index_by_heading(sections, heading_names)
    if start_index is None:
        return [], set()
    run = collect_section_run(sections, start_index)
    indices = set(range(start_index, start_index + len(run)))
    return run, indices


def format_sections(sections: list[Section]) -> str:
    parts: list[str] = []
    for section in sections:
        body = collapse_lines(section.content_lines)
        heading = strip_heading_numbering(section.heading) or section.heading
        if body:
            parts.append(f"## {heading}\n\n{body}")
        else:
            parts.append(f"## {heading}")
    return "\n\n".join(part for part in parts if part).strip()


def is_journal_banner(text: str) -> bool:
    stripped = clean_title_or_text(text)
    if not stripped:
        return False
    if stripped.upper() == stripped and len(stripped.split()) <= 8 and any(ch.isalpha() for ch in stripped):
        return True
    lower = stripped.lower()
    return lower.startswith(("plos ", "nature ", "science ", "biorxiv", "medrxiv"))


def is_title_candidate(text: str) -> bool:
    stripped = clean_title_or_text(text)
    normalized = normalize_heading(stripped)
    if len(stripped) < 15:
        return False
    if normalized in META_HEADINGS | ABSTRACT_HEADINGS | METHOD_HEADINGS | REFERENCE_HEADINGS:
        return False
    if is_journal_banner(stripped):
        return False
    return True


def find_title(sections: list[Section], lines: list[str]) -> tuple[str, int]:
    for section in sections[:12]:
        if is_title_candidate(section.heading):
            return clean_title_or_text(section.heading), section.start
    for index, line in enumerate(lines[:80]):
        if is_title_candidate(line):
            return clean_title_or_text(line), index
    return "", -1


def find_front_matter_end(lines: list[str], title_index: int) -> int:
    for index in range(title_index + 1, len(lines)):
        match = HEADING_RE.match(lines[index].strip())
        if not match:
            continue
        normalized = normalize_heading(match.group(2))
        if normalized in ABSTRACT_HEADINGS | MAIN_START_HEADINGS | METHOD_HEADINGS:
            return index
    return min(len(lines), title_index + 80) if title_index >= 0 else min(len(lines), 80)


def looks_like_affiliation(text: str) -> bool:
    lower = clean_title_or_text(text).lower()
    if not lower:
        return False
    if any(hint in lower for hint in AFFILIATION_HINTS):
        return True
    if re.match(r"^\(?\d+\)?\s+", lower):
        return True
    if text.strip().startswith("$^{"):
        return True
    return False


def looks_like_author_line(text: str) -> bool:
    cleaned = clean_title_or_text(text)
    lower = cleaned.lower()
    if not cleaned or len(cleaned) > 320:
        return False
    if looks_like_affiliation(cleaned):
        return False
    if "doi" in lower:
        return False
    if lower.startswith(("figure ", "fig. ", "table ", "graphical abstract", "keywords")):
        return False
    if EMAIL_RE.search(cleaned):
        return False
    return "," in cleaned or " and " in lower


def normalize_affiliation_line(text: str) -> str:
    cleaned = clean_title_or_text(text)
    cleaned = re.sub(r"^\(?(\d+)\)?\s*", r"(\1) ", cleaned)
    return cleaned.strip(" ,;")


def parse_front_matter(lines: list[str], title_index: int) -> dict:
    if title_index < 0:
        return {
            "authors": "",
            "affiliations": [],
            "correspondence": [],
            "keywords": "",
            "abstract_candidate": "",
            "front_matter_end": 0,
        }

    end = find_front_matter_end(lines, title_index)
    front_matter = lines[title_index + 1 : end]
    blocks = split_blocks(front_matter)

    authors = ""
    affiliations: list[str] = []
    correspondence: list[str] = []
    keywords = ""
    abstract_candidate = ""

    seen_affiliations: set[str] = set()
    leftover_blocks: list[str] = []

    for block in blocks:
        block_text = collapse_lines(block)
        normalized = normalize_heading(block_text)
        lower = block_text.lower()

        if not authors and looks_like_author_line(block_text):
            authors = block_text
            continue
        if "correspondence" in lower or EMAIL_RE.search(block_text):
            correspondence.append(block_text)
            continue
        if normalized == "keywords" or lower.startswith("keywords:"):
            keywords = block_text
            continue

        aff_lines = [normalize_affiliation_line(line) for line in block if looks_like_affiliation(line)]
        if aff_lines and len(aff_lines) == len(block):
            for aff in aff_lines:
                key = normalize_count_key(aff)
                if key not in seen_affiliations:
                    affiliations.append(aff)
                    seen_affiliations.add(key)
            continue

        cleaned_block = clean_title_or_text(block_text)
        if cleaned_block:
            leftover_blocks.append(cleaned_block)

    for block_text in leftover_blocks:
        if len(block_text) >= 160 and not abstract_candidate:
            abstract_candidate = block_text
            break

    return {
        "authors": authors,
        "affiliations": affiliations,
        "correspondence": correspondence,
        "keywords": keywords,
        "abstract_candidate": abstract_candidate,
        "front_matter_end": end,
    }


def split_reference_entries(text: str) -> list[str]:
    if not text.strip():
        return []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if any(re.match(r"^(\[\d+\]|\d+\.)\s+", line) for line in lines):
        entries: list[str] = []
        current: list[str] = []
        for line in lines:
            if re.match(r"^(\[\d+\]|\d+\.)\s+", line):
                if current:
                    entries.append(" ".join(current).strip())
                current = [line]
            else:
                current.append(line)
        if current:
            entries.append(" ".join(current).strip())
        return entries
    return lines


def extract_abstract(sections: list[Section], front_matter: dict) -> tuple[str, list[str], str]:
    abstract_index = section_index_by_heading(sections, ABSTRACT_HEADINGS)
    if abstract_index is not None:
        abstract_section = sections[abstract_index]
        headings = [abstract_section.heading]
        parts: list[str] = []

        direct_text = collapse_lines(abstract_section.content_lines)
        if direct_text:
            parts.append(direct_text)

        for section in sections[abstract_index + 1 :]:
            if section.level <= abstract_section.level:
                break
            normalized = section.normalized_heading
            if normalized in META_HEADINGS | REFERENCE_HEADINGS:
                break

            body = collapse_lines(section.content_lines)
            structured_heading = normalized in STRUCTURED_ABSTRACT_HEADINGS
            if not body:
                if structured_heading:
                    headings.append(section.heading)
                    continue
                break
            if structured_heading or not parts:
                headings.append(section.heading)
                heading = strip_heading_numbering(section.heading) or section.heading
                parts.append(f"{heading}: {body}" if structured_heading else body)
                continue
            break

        return "\n\n".join(parts).strip(), headings, "section_run" if len(headings) > 1 else "section"
    if front_matter["abstract_candidate"]:
        return front_matter["abstract_candidate"], [], "front_matter"
    return "", [], ""


def extract_methods(sections: list[Section]) -> tuple[str, set[int], list[str]]:
    method_sections, method_indices = collect_named_run(sections, METHOD_HEADINGS)
    return format_sections(method_sections), method_indices, [section.heading for section in method_sections]


def extract_references(sections: list[Section]) -> tuple[list[str], set[int], list[str]]:
    reference_sections, reference_indices = collect_named_run(sections, REFERENCE_HEADINGS)
    if not reference_sections:
        return [], reference_indices, []
    text = collapse_lines(reference_sections[0].content_lines)
    return split_reference_entries(text), reference_indices, [section.heading for section in reference_sections]


def extract_figure_legends(lines: list[str]) -> list[str]:
    captions: list[str] = []
    current: list[str] = []
    for line in lines:
        cleaned = clean_title_or_text(line)
        if not cleaned:
            if current:
                captions.append(" ".join(current).strip())
                current = []
            continue
        if CAPTION_START_RE.match(cleaned):
            if current:
                captions.append(" ".join(current).strip())
            current = [cleaned]
            continue
        if current:
            if HEADING_RE.match(line.strip()) or CAPTION_START_RE.match(cleaned):
                captions.append(" ".join(current).strip())
                current = []
            else:
                current.append(cleaned)
    if current:
        captions.append(" ".join(current).strip())

    deduped: list[str] = []
    seen: set[str] = set()
    for caption in captions:
        key = normalize_count_key(caption)
        if key not in seen:
            deduped.append(caption)
            seen.add(key)
    return deduped


def extract_main(
    sections: list[Section],
    title_index: int,
    excluded_indices: set[int],
) -> tuple[str, list[str]]:
    def trim_figure_tail(lines: list[str]) -> list[str]:
        for idx, raw_line in enumerate(lines):
            cleaned = clean_title_or_text(raw_line)
            if not cleaned:
                continue
            if FIGURE_BLOCK_MARKER_RE.match(cleaned):
                return lines[:idx]
        return lines

    title_section_index = None
    for index, section in enumerate(sections):
        if section.start == title_index:
            title_section_index = index
            break

    parts: list[str] = []
    included_headings: list[str] = []
    started = False
    for index, section in enumerate(sections):
        normalized = section.normalized_heading
        if index == title_section_index:
            continue
        if index in excluded_indices:
            continue
        if normalized in META_HEADINGS | ABSTRACT_HEADINGS:
            continue
        if not started:
            if normalized in MAIN_START_HEADINGS:
                started = True
            else:
                continue
        body = collapse_lines(trim_figure_tail(section.content_lines))
        if not body:
            continue
        parts.append(f"## {strip_heading_numbering(section.heading) or section.heading}\n\n{body}")
        included_headings.append(section.heading)

    if not parts:
        for index, section in enumerate(sections):
            normalized = section.normalized_heading
            if index == title_section_index or index in excluded_indices:
                continue
            if normalized in META_HEADINGS | ABSTRACT_HEADINGS:
                continue
            body = collapse_lines(trim_figure_tail(section.content_lines))
            if body:
                parts.append(f"## {strip_heading_numbering(section.heading) or section.heading}\n\n{body}")
                included_headings.append(section.heading)

    return "\n\n".join(parts).strip(), included_headings


def audit_string_field(expected: bool, text: str, *, source: str = "", headings: list[str] | None = None) -> dict:
    return {
        "expected": expected,
        "populated": bool((text or "").strip()),
        "source": source,
        "source_headings": headings or [],
        "char_count": len(text or ""),
        "preview": (text or "")[:400],
        "text": text or "",
    }


def audit_list_field(expected: bool, entries: list[str], *, source: str = "", headings: list[str] | None = None) -> dict:
    return {
        "expected": expected,
        "populated": bool(entries),
        "source": source,
        "source_headings": headings or [],
        "count": len(entries),
        "preview": entries[:3],
        "entries": entries,
    }


def build_section_audit(markdown_path: Path) -> dict:
    lines = load_clean_lines(markdown_path)
    sections = parse_sections(lines)
    title, title_index = find_title(sections, lines)
    front_matter = parse_front_matter(lines, title_index)
    abstract, abstract_headings, abstract_source = extract_abstract(sections, front_matter)
    methods, method_indices, method_headings = extract_methods(sections)
    references, reference_indices, reference_headings = extract_references(sections)
    figure_legends = extract_figure_legends(lines)
    main_text, main_headings = extract_main(
        sections,
        title_index=title_index,
        excluded_indices=method_indices | reference_indices,
    )

    field_audit = {
        "title": audit_string_field(True, title, source="title_line"),
        "authors": audit_string_field(True, front_matter["authors"], source="front_matter"),
        "affiliations": audit_string_field(bool(front_matter["affiliations"]), ", ".join(front_matter["affiliations"]), source="front_matter"),
        "abstract": audit_string_field(bool(abstract or abstract_headings), abstract, source=abstract_source, headings=abstract_headings),
        "methods": audit_string_field(bool(method_headings), methods, source="section_run", headings=method_headings),
        "main": audit_string_field(True, main_text, source="section_runs", headings=main_headings),
        "figure_legends": audit_list_field(bool(figure_legends), figure_legends, source="caption_scan"),
        "figure_interpretation": audit_string_field(bool(figure_legends), "", source="figure_review_required"),
        "references": audit_list_field(bool(reference_headings), references, source="section_run", headings=reference_headings),
    }

    missing_expected_fields = [
        name
        for name, info in field_audit.items()
        if info.get("expected") and not info.get("populated")
    ]

    return {
        "markdown_path": str(markdown_path),
        "line_count": len(lines),
        "section_count": len(sections),
        "title_index": title_index,
        "front_matter_end_index": front_matter["front_matter_end"],
        "headings": [
            {
                "index": index,
                "level": section.level,
                "heading": section.heading,
                "normalized_heading": section.normalized_heading,
                "start_line": section.start + 1,
                "end_line": section.end,
                "body_char_count": len(collapse_lines(section.content_lines)),
            }
            for index, section in enumerate(sections)
        ],
        "front_matter": {
            "authors_candidate": front_matter["authors"],
            "affiliations": front_matter["affiliations"],
            "correspondence": front_matter["correspondence"],
            "keywords": front_matter["keywords"],
            "abstract_candidate": front_matter["abstract_candidate"],
        },
        "field_audit": field_audit,
        "expected_fields": [name for name, info in field_audit.items() if info.get("expected")],
        "missing_expected_fields": missing_expected_fields,
    }


def build_article_from_audit(audit: dict) -> dict:
    field_audit = audit["field_audit"]
    return {
        "title": field_audit["title"]["text"],
        "authors": field_audit["authors"]["text"],
        "affiliations": field_audit["affiliations"]["text"],
        "abstract": field_audit["abstract"]["text"],
        "main": field_audit["main"]["text"],
        "methods": field_audit["methods"]["text"],
        "figure_legends": field_audit["figure_legends"]["entries"],
        "figure_interpretation": field_audit["figure_interpretation"]["text"],
        "references": field_audit["references"]["entries"],
    }


def default_audit_path(markdown_path: Path) -> Path:
    return markdown_path.with_suffix(".section_audit.json")


def load_audit(audit_path: Path) -> dict:
    return json.loads(audit_path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
