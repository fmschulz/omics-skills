#!/usr/bin/env python3
"""Validate DOI registration and title metadata for tracked skill Markdown."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CACHE = ROOT / "catalog" / "citation-cache.json"
# A cached registration check has a shelf life: without one, CI can accept a
# result from years ago for a DOI whose metadata has since changed.
MAX_CACHE_AGE_DAYS = 180
DOI_PATTERN = re.compile(r"10\.\d{4,9}/[^\s<>\"'`]+", re.IGNORECASE)
FRONTMATTER_DOI = re.compile(r"^\s*doi:\s*[\"']?([^\"'#\s]+)", re.IGNORECASE | re.MULTILINE)
FRONTMATTER_TITLE = re.compile(
    r"^\s*title:\s*(?:[\"'](.*?)[\"']|([^#\n]+))\s*$",
    re.IGNORECASE | re.MULTILINE,
)
TITLE_TOKEN = re.compile(r"[a-z0-9]+")
TITLE_CHECK_SKIP_PREFIXES = ("10.48550/", "10.5281/")
# A preprint landing URL appends a version the DOI resolver rejects:
# https://www.biorxiv.org/content/10.64898/2026.01.08.698506v3
PREPRINT_HOST = re.compile(r"(?:^|[/.])(?:bio|med)rxiv\.org/content/?$", re.IGNORECASE)
# ...698506v3, ...698506v3.full, ...698506v3?x=1 all resolve to the same DOI.
PREPRINT_VERSION_SUFFIX = re.compile(r"(?<=\d)v\d+(?:\.[a-z]+)?(?:[?#].*)?$", re.IGNORECASE)


# A citation in prose already states who wrote the paper and when:
#   - MetaBAT2: Kang et al. (2019) *PeerJ* https://doi.org/10.7717/peerj.7359
#   Saary P, Mitchell AL, Finn RD. (2020)
#   ... *Genome Biology* 21:244. https://doi.org/10.1186/s13059-020-02155-4
# Discarding that and checking only that the DOI resolves means a DOI swapped
# for any other registered DOI still passes. These patterns recover the claim.
CLAIMED_YEAR = re.compile(r"\((\d{4})[a-z]?\)|\b(19|20)(\d{2})\b")
# Only the constructions that actually name an author. A bare `Word (2024)` is
# just as often a venue -- "npj Viruses (2024)", "(Journal of Genetics and
# Genomics 2021)" -- so it counts only as the first token of the citation body.
CLAIMED_SURNAME = re.compile(
    r"\b([A-Z][a-zA-Z\u00C0-\u024F'\u2019-]{2,})\b"
    r"(?=\s*(?:\bet\s+al\b"
    # "Shen & Ren (2021)" is an author pair; "Genetics and Genomics 2021)" is a
    # venue. The parenthesised year is what separates them.
    r"|(?:&|and)\s+[A-Z][a-zA-Z\u00C0-\u024F'\u2019-]+\s*\(\d{4}"
    r"|[A-Z]{1,3}[,.]|[A-Z]{1,3}\s+\d{4}))"
)
LEADING_SURNAME = re.compile(r"^([A-Z][a-zA-Z\u00C0-\u024F'\u2019-]{2,})\s*\(\d{4}")
# `- MetaBAT2: Kang et al. (2019) ...` - the label before the colon is the tool,
# not an author.
LIST_LABEL = re.compile(r"^\s*[-*+]\s+[^:\n]{1,40}:\s*")
# Words that look like surnames but are tool names, venues, or sentence starts.
SURNAME_STOPWORDS = frozenset(
    {
        "The", "This", "See", "Citation", "Cite", "Preprint", "Paper", "Reference",
        "Published", "Available", "Nature", "Science", "Genome", "Biology", "Methods",
        "Bioinformatics", "Microbiome", "Communications", "Biotechnology", "Journal",
        "Proceedings", "Research", "Reports", "Letters", "Systems", "Frontiers",
        "Molecular", "Nucleic", "Acids", "Cell", "PLoS", "PeerJ", "eLife", "GigaScience",
        "Use", "Used", "Using", "From", "For", "With", "And", "Version", "Release",
    }
)


@dataclass(frozen=True)
class Citation:
    doi: str
    path: Path
    line: int
    title: str | None = None
    claimed_year: int | None = None
    claimed_surnames: tuple[str, ...] = ()


def citation_context(lines: list[str], index: int) -> str:
    """The reference block around a DOI.

    A one-line reference is self-contained; walking back would pick up the
    neighbouring list item's author and year. Only a line that states neither a
    year nor an author continues a multi-line reference such as:

        Saary P, Mitchell AL, Finn RD. (2020)
        Estimating the quality of eukaryotic genomes ...
        *Genome Biology* 21:244. https://doi.org/10.1186/s13059-020-02155-4
    """
    own = lines[index]
    if CLAIMED_YEAR.search(LIST_LABEL.sub("", own)):
        return own
    start = index
    while start > 0 and index - start < 3:
        previous = lines[start - 1].strip()
        if not previous or previous.startswith(("#", "|", "```", "-", "*", "+")):
            break
        start -= 1
        if CLAIMED_YEAR.search(previous):
            break
    return " ".join(lines[start : index + 1])


def parse_claim(context: str, doi: str | None = None) -> tuple[int | None, tuple[str, ...]]:
    """Return the (year, surnames) the prose asserts for a citation."""
    context = LIST_LABEL.sub("", context)
    # One line can carry several references separated by semicolons; keep only
    # the segment that actually contains this DOI.
    if doi and ";" in context:
        for segment in context.split(";"):
            if doi in segment:
                context = segment.strip()
                break
    year_match = CLAIMED_YEAR.search(context)
    year = None
    if year_match:
        year = int(year_match.group(1) or f"{year_match.group(2)}{year_match.group(3)}")
    names = CLAIMED_SURNAME.findall(context)
    leading = LEADING_SURNAME.match(context.strip())
    if leading:
        names.append(leading.group(1))
    surnames = tuple(
        dict.fromkeys(
            name
            for name in names
            if name not in SURNAME_STOPWORDS and not name.isupper()
        )
    )
    return year, surnames


def normalize_doi(raw: str) -> str | None:
    doi = raw.strip()
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.IGNORECASE)
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    previous = ""
    while doi != previous:
        previous = doi
        doi = doi.rstrip(".,;:")
        # Markdown emphasis leaks into a bare DOI (`10.5281/zenodo.19154110**`).
        # Strip a trailing run only when it is unbalanced, since these characters
        # are legal inside a DOI.
        for mark in ("**", "*", "__", "_", "~~", "~"):
            while doi.endswith(mark) and doi.count(mark) % 2 == 1:
                doi = doi[: -len(mark)]
        while doi.endswith(("}", "]")):
            doi = doi[:-1]
        while doi.endswith(")") and doi.count(")") > doi.count("("):
            doi = doi[:-1]
    return doi.lower() if re.fullmatch(r"10\.\d{4,9}/\S+", doi, re.IGNORECASE) else None


def frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end >= 0 else ""


def tracked_markdown(repo_root: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "skills"],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return sorted((repo_root / "skills").rglob("*.md"))
    return sorted(
        repo_root / raw.decode()
        for raw in result.stdout.split(b"\0")
        if raw and raw.decode().endswith(".md") and (repo_root / raw.decode()).is_file()
    )


def collect_citations(paths: list[Path]) -> list[Citation]:
    citations: list[Citation] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        header = frontmatter(text)
        title_match = FRONTMATTER_TITLE.search(header)
        title = None
        if title_match:
            title = (title_match.group(1) or title_match.group(2) or "").strip()
        for match in FRONTMATTER_DOI.finditer(header):
            doi = normalize_doi(match.group(1))
            if doi:
                citations.append(Citation(doi, path, text[: match.start()].count("\n") + 2, title))
        header_dois = {citation.doi for citation in citations if citation.path == path}
        lines = text.splitlines()
        for match in DOI_PATTERN.finditer(text):
            doi = normalize_doi(match.group(0))
            if doi and PREPRINT_HOST.search(text[max(0, match.start() - 60) : match.start()]):
                doi = PREPRINT_VERSION_SUFFIX.sub("", doi)
            if doi and doi not in header_dois:
                index = text[: match.start()].count("\n")
                year, surnames = parse_claim(citation_context(lines, index), doi)
                citations.append(
                    Citation(doi, path, index + 1, None, year, surnames)
                )
    return citations


def crossref_year(message: dict) -> int | None:
    """Crossref reports several dates; take the earliest real publication year."""
    years = []
    for field in ("published-print", "published-online", "published", "issued"):
        parts = (message.get(field) or {}).get("date-parts") or [[]]
        if parts and parts[0]:
            try:
                years.append(int(parts[0][0]))
            except (TypeError, ValueError):
                continue
    return min(years) if years else None


def title_overlap(left: str, right: str) -> float:
    left_tokens = set(TITLE_TOKEN.findall(left.lower()))
    right_tokens = set(TITLE_TOKEN.findall(right.lower()))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(len(left_tokens), len(right_tokens))


def fetch_json(url: str, timeout: float) -> dict[str, object]:
    request = Request(url, headers={"User-Agent": "omics-skills-citation-validator/1.0"})
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise HTTPError(url, response.status, response.reason, response.headers, None)
        return json.load(response)


def refresh_cache(
    citations: list[Citation], cache_path: Path, timeout: float
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    transient: list[str] = []
    records: dict[str, dict[str, object]] = {}
    by_doi: dict[str, list[Citation]] = {}
    for citation in citations:
        by_doi.setdefault(citation.doi, []).append(citation)

    for doi, sources in sorted(by_doi.items()):
        try:
            handle_url = f"https://doi.org/api/handles/{quote(doi, safe='/')}"
            handle = fetch_json(handle_url, timeout)
            if handle.get("responseCode") != 1:
                errors.append(f"{doi}: DOI handle responseCode={handle.get('responseCode')}")
                continue

            cached_title = None
            families: list[str] = []
            registered_year = None
            declared_title = next((source.title for source in sources if source.title), None)
            claims_identity = any(source.claimed_year or source.claimed_surnames for source in sources)
            if (declared_title or claims_identity) and not doi.startswith(TITLE_CHECK_SKIP_PREFIXES):
                crossref_url = f"https://api.crossref.org/works/{quote(doi, safe='')}"
                payload = fetch_json(crossref_url, timeout)
                message = payload.get("message") if isinstance(payload, dict) else None
                message = message if isinstance(message, dict) else {}
                titles = message.get("title", [])
                cached_title = str(titles[0]) if isinstance(titles, list) and titles else None
                if declared_title and not cached_title:
                    errors.append(f"{doi}: Crossref returned no title")
                    continue
                families = [
                    str(author["family"])
                    for author in message.get("author", []) or []
                    if isinstance(author, dict) and author.get("family")
                ]
                registered_year = crossref_year(message)
            records[doi] = {
                "registered": True,
                "title": cached_title,
                "authors": families,
                "year": registered_year,
                "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "source": "doi.org handle" + (" + Crossref title" if cached_title else ""),
            }
        except HTTPError as error:
            if error.code == 404:
                errors.append(f"{doi}: HTTP 404")
            else:
                transient.append(f"{doi}: HTTP {error.code}")
        except (URLError, TimeoutError, json.JSONDecodeError, OSError) as error:
            transient.append(f"{doi}: {error}")

    if not errors and not transient:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = cache_path.with_suffix(cache_path.suffix + ".tmp")
        temporary.write_text(
            json.dumps({"version": 1, "records": records}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(cache_path)
    return errors, transient


def validate_cache(citations: list[Citation], cache_path: Path) -> list[str]:
    if not cache_path.exists():
        return [f"citation cache missing: {cache_path}; run with --refresh"]
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"citation cache unreadable: {error}"]
    records = payload.get("records", {})
    if payload.get("version") != 1 or not isinstance(records, dict):
        return ["citation cache has an unsupported schema"]

    errors: list[str] = []
    stale: set[str] = set()
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_CACHE_AGE_DAYS)
    for citation in citations:
        location = f"{citation.path}:{citation.line}"
        record = records.get(citation.doi)
        if not isinstance(record, dict) or record.get("registered") is not True:
            errors.append(
                f"{location}: {citation.doi} is not in the validated cache; run with --refresh"
            )
            continue
        checked_at = record.get("checked_at")
        if not isinstance(checked_at, str):
            errors.append(f"{location}: {citation.doi} has no checked_at date; run with --refresh")
        else:
            try:
                stamped = datetime.strptime(checked_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except ValueError:
                errors.append(f"{location}: {citation.doi} has an unreadable checked_at {checked_at!r}")
            else:
                # Age is a maintenance signal, not a verdict. Failing on it would
                # break an offline, deterministic gate on a date certain, with no
                # way to refresh without live services.
                if stamped < cutoff:
                    stale.add(f"{citation.doi} last checked {checked_at}")
        # The claim the prose makes must match the registered record. Without
        # this, one registered DOI substituted for another still passed.
        if not citation.doi.startswith(TITLE_CHECK_SKIP_PREFIXES):
            registered_year = record.get("year")
            if citation.claimed_year and isinstance(registered_year, int):
                # Online-vs-print can differ by a year; more than that is a swap.
                if abs(citation.claimed_year - registered_year) > 1:
                    errors.append(
                        f"{location}: {citation.doi} is registered to {registered_year}, "
                        f"but the citation says {citation.claimed_year}"
                    )
            registered_authors = record.get("authors")
            if citation.claimed_surnames and isinstance(registered_authors, list) and registered_authors:
                registered = {str(name).casefold() for name in registered_authors}
                claimed = {name.casefold() for name in citation.claimed_surnames}
                if not (claimed & registered):
                    errors.append(
                        f"{location}: {citation.doi} is registered to "
                        f"{', '.join(sorted(registered_authors)[:3])}, but the citation names "
                        f"{', '.join(citation.claimed_surnames)}"
                    )
        if citation.title and not citation.doi.startswith(TITLE_CHECK_SKIP_PREFIXES):
            registered_title = record.get("title")
            if not isinstance(registered_title, str):
                errors.append(f"{location}: {citation.doi} has no cached Crossref title")
            elif title_overlap(citation.title, registered_title) < 0.6:
                errors.append(
                    f"{location}: title does not match Crossref for {citation.doi} "
                    f"({citation.title!r} vs {registered_title!r})"
                )
    unused = sorted(set(records) - {citation.doi for citation in citations})
    if unused:
        stale.add(
            f"{len(unused)} cached DOI(s) nothing cites any more: "
            f"{', '.join(unused[:5])}{'...' if len(unused) > 5 else ''}"
        )
    for note in sorted(stale):
        print(f"citation cache maintenance: {note}; run with --refresh", file=sys.stderr)
    return errors


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--timeout", type=float, default=20.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    citations = collect_citations(tracked_markdown(args.repo_root))
    if args.refresh:
        errors, transient = refresh_cache(citations, args.cache, args.timeout)
        for error in errors + transient:
            print(f"- {error}", file=sys.stderr)
        if transient:
            return 2
        if errors:
            return 1
    errors = validate_cache(citations, args.cache)
    if errors:
        print("Citation validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Citation validation passed ({len({item.doi for item in citations})} DOIs).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
