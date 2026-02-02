#!/usr/bin/env python3
"""
CrossRef API Validator for Scientific References

Validates DOIs, retrieves complete citation metadata, checks title accuracy,
and formats references in multiple citation styles.

Usage:
    python crossref_validator.py --doi "10.1038/nature12373"
    python crossref_validator.py --title "CRISPR-Cas9 genome editing"
    python crossref_validator.py --validate-file references.txt
    python crossref_validator.py --audit-bibliography refs.bib --output report.txt

Requirements:
    pip install requests

CrossRef API Documentation: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
"""

import argparse
import json
import re
import sys
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote

try:
    import requests
except ImportError:
    print("Error: requests library not installed. Run: pip install requests")
    sys.exit(1)

# CrossRef API configuration
CROSSREF_API_BASE = "https://api.crossref.org"
USER_AGENT = "science-writing-skill/1.0 (mailto:your-email@example.com)"  # Polite pool
RATE_LIMIT_DELAY = 0.05  # 50 requests/second for polite pool


class CrossRefValidator:
    """Validates and enriches scientific references using CrossRef API."""

    def __init__(self, user_agent: str = USER_AGENT):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting to stay within CrossRef polite pool limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()

    def validate_doi(self, doi: str) -> Tuple[bool, Optional[Dict]]:
        """
        Validate a DOI and retrieve metadata.

        Args:
            doi: Digital Object Identifier (with or without doi: prefix or URL)

        Returns:
            Tuple of (is_valid, metadata_dict)
        """
        # Clean DOI
        doi_clean = self._clean_doi(doi)
        if not doi_clean:
            return False, None

        self._rate_limit()

        try:
            url = f"{CROSSREF_API_BASE}/works/{doi_clean}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data["status"] == "ok":
                    return True, data["message"]
            elif response.status_code == 404:
                return False, {"error": "DOI not found in CrossRef database"}
            else:
                return False, {"error": f"HTTP {response.status_code}"}

        except requests.RequestException as e:
            return False, {"error": f"Request failed: {str(e)}"}

        return False, None

    def search_by_title(
        self, title: str, max_results: int = 5
    ) -> List[Dict]:
        """
        Search for works by title.

        Args:
            title: Article title to search for
            max_results: Maximum number of results to return

        Returns:
            List of matching works with metadata
        """
        self._rate_limit()

        try:
            url = f"{CROSSREF_API_BASE}/works"
            params = {"query.title": title, "rows": max_results}
            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data["status"] == "ok":
                    return data["message"]["items"]

        except requests.RequestException as e:
            print(f"Error searching by title: {e}", file=sys.stderr)

        return []

    def format_citation(
        self, metadata: Dict, style: str = "apa"
    ) -> str:
        """
        Format citation in specified style.

        Args:
            metadata: CrossRef metadata dictionary
            style: Citation style (apa, vancouver, ama, ieee, chicago)

        Returns:
            Formatted citation string
        """
        # Extract fields
        authors = self._format_authors(metadata.get("author", []), style)
        title = metadata.get("title", [""])[0]
        year = self._extract_year(metadata)
        journal = metadata.get("container-title", [""])[0]
        volume = metadata.get("volume", "")
        issue = metadata.get("issue", "")
        pages = metadata.get("page", "")
        doi = metadata.get("DOI", "")

        # Format based on style
        if style.lower() == "apa":
            citation = f"{authors} ({year}). {title}. {journal}"
            if volume:
                citation += f", {volume}"
            if issue:
                citation += f"({issue})"
            if pages:
                citation += f", {pages}"
            if doi:
                citation += f". https://doi.org/{doi}"

        elif style.lower() == "vancouver":
            citation = f"{authors} {title}. {journal}. {year}"
            if volume:
                citation += f";{volume}"
            if issue:
                citation += f"({issue})"
            if pages:
                citation += f":{pages}"
            if doi:
                citation += f". doi:{doi}"

        elif style.lower() == "ama":
            citation = f"{authors} {title}. {journal}. {year}"
            if volume:
                citation += f";{volume}"
            if issue:
                citation += f"({issue})"
            if pages:
                citation += f":{pages}"
            if doi:
                citation += f". doi:{doi}"

        elif style.lower() == "ieee":
            citation = f"{authors}, \"{title},\" {journal}"
            if volume:
                citation += f", vol. {volume}"
            if issue:
                citation += f", no. {issue}"
            if pages:
                citation += f", pp. {pages}"
            if year:
                citation += f", {year}"
            if doi:
                citation += f". doi: {doi}"

        elif style.lower() == "chicago":
            citation = f"{authors} {year}. \"{title}.\" {journal}"
            if volume:
                citation += f" {volume}"
            if issue:
                citation += f" ({issue})"
            if pages:
                citation += f": {pages}"
            if doi:
                citation += f". https://doi.org/{doi}"

        else:
            citation = f"{authors} ({year}). {title}. {journal} {volume}({issue}): {pages}. DOI: {doi}"

        return citation.strip()

    def _format_authors(self, authors: List[Dict], style: str) -> str:
        """Format author list according to citation style."""
        if not authors:
            return "Unknown"

        formatted = []

        for i, author in enumerate(authors[:6]):  # Limit to first 6
            family = author.get("family", "")
            given = author.get("given", "")

            if style.lower() in ["apa", "chicago"]:
                # Last, F. M.
                initials = " ".join([f"{g[0]}." for g in given.split()])
                formatted.append(f"{family}, {initials}")
            elif style.lower() in ["vancouver", "ama", "ieee"]:
                # Last FM
                initials = "".join([g[0] for g in given.split()])
                formatted.append(f"{family} {initials}")
            else:
                formatted.append(f"{family} {given}")

        # Handle "et al" for multiple authors
        if len(authors) > 6:
            formatted.append("et al")
        elif len(formatted) > 1:
            if style.lower() in ["apa", "chicago"]:
                # Use & for last author
                formatted[-1] = f"& {formatted[-1]}"
            else:
                # Use "and" for IEEE
                if style.lower() == "ieee":
                    formatted[-1] = f"and {formatted[-1]}"

        # Join with appropriate separator
        if style.lower() in ["apa", "chicago"]:
            return ", ".join(formatted)
        else:
            return ", ".join(formatted)

    def _extract_year(self, metadata: Dict) -> str:
        """Extract publication year from metadata."""
        if "published-print" in metadata:
            date_parts = metadata["published-print"].get("date-parts", [[]])
            if date_parts and date_parts[0]:
                return str(date_parts[0][0])
        elif "published-online" in metadata:
            date_parts = metadata["published-online"].get("date-parts", [[]])
            if date_parts and date_parts[0]:
                return str(date_parts[0][0])
        return "n.d."

    def _clean_doi(self, doi: str) -> Optional[str]:
        """
        Clean and normalize DOI.

        Accepts:
            - Raw DOI: 10.1038/nature12373
            - DOI with prefix: doi:10.1038/nature12373
            - DOI URL: https://doi.org/10.1038/nature12373
        """
        if not doi:
            return None

        # Remove common prefixes
        doi = doi.strip()
        doi = re.sub(r"^doi:\s*", "", doi, flags=re.IGNORECASE)
        doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)

        # Validate format
        if re.match(r"^10\.\d{4,}/\S+$", doi):
            return doi

        return None

    def validate_file(self, filepath: str) -> Dict[str, List]:
        """
        Validate DOIs from a file (one per line).

        Args:
            filepath: Path to file containing DOIs

        Returns:
            Dictionary with 'valid', 'invalid', and 'errors' lists
        """
        results = {"valid": [], "invalid": [], "errors": []}

        try:
            with open(filepath, "r") as f:
                dois = [line.strip() for line in f if line.strip()]

            for doi in dois:
                is_valid, metadata = self.validate_doi(doi)
                if is_valid:
                    results["valid"].append({"doi": doi, "metadata": metadata})
                elif metadata and "error" in metadata:
                    results["errors"].append({"doi": doi, "error": metadata["error"]})
                else:
                    results["invalid"].append(doi)

        except FileNotFoundError:
            print(f"Error: File '{filepath}' not found", file=sys.stderr)
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)

        return results

    def audit_bibliography(self, bib_file: str) -> Dict[str, any]:
        """
        Audit a bibliography file for missing or incorrect DOIs.

        Args:
            bib_file: Path to bibliography file (.bib, .txt, or plain text)

        Returns:
            Dictionary with audit results
        """
        # Extract DOIs from file
        dois = []
        titles = []

        try:
            with open(bib_file, "r") as f:
                content = f.read()

            # Find DOIs
            doi_pattern = r"(?:doi:|https?://(?:dx\.)?doi\.org/)?(10\.\d{4,}/\S+)"
            dois = re.findall(doi_pattern, content, re.IGNORECASE)

            # Find titles (simple heuristic - lines with title markers)
            title_pattern = r'title\s*=\s*["{]([^"}]+)["}]'
            titles = re.findall(title_pattern, content, re.IGNORECASE)

        except FileNotFoundError:
            print(f"Error: File '{bib_file}' not found", file=sys.stderr)
            return {}
        except Exception as e:
            print(f"Error reading bibliography: {e}", file=sys.stderr)
            return {}

        # Validate DOIs
        valid_dois = []
        invalid_dois = []

        for doi in set(dois):  # Remove duplicates
            is_valid, metadata = self.validate_doi(doi)
            if is_valid:
                valid_dois.append({"doi": doi, "title": metadata.get("title", [""])[0]})
            else:
                invalid_dois.append(doi)

        return {
            "total_dois": len(set(dois)),
            "valid_dois": len(valid_dois),
            "invalid_dois": len(invalid_dois),
            "valid_list": valid_dois,
            "invalid_list": invalid_dois,
            "total_titles": len(titles),
            "missing_dois": len(titles) - len(set(dois)),
        }


def main():
    parser = argparse.ArgumentParser(
        description="Validate DOIs and retrieve citation metadata using CrossRef API"
    )
    parser.add_argument("--doi", help="Validate a single DOI")
    parser.add_argument("--title", help="Search for works by title")
    parser.add_argument("--validate-file", help="Validate DOIs from file (one per line)")
    parser.add_argument("--audit-bibliography", help="Audit bibliography file for DOIs")
    parser.add_argument(
        "--style",
        default="apa",
        choices=["apa", "vancouver", "ama", "ieee", "chicago"],
        help="Citation style for formatting",
    )
    parser.add_argument("--output", help="Output file for results (default: stdout)")
    parser.add_argument(
        "--email",
        help="Email for CrossRef polite pool (faster rate limit)",
        default="your-email@example.com",
    )

    args = parser.parse_args()

    # Update user agent with email if provided
    user_agent = f"science-writing-skill/1.0 (mailto:{args.email})"
    validator = CrossRefValidator(user_agent=user_agent)

    # Output stream
    output = open(args.output, "w") if args.output else sys.stdout

    try:
        if args.doi:
            # Validate single DOI
            is_valid, metadata = validator.validate_doi(args.doi)
            if is_valid:
                print(f"✓ DOI is valid: {args.doi}", file=output)
                print(f"\nTitle: {metadata.get('title', [''])[0]}", file=output)
                print(f"Authors: {len(metadata.get('author', []))} authors", file=output)
                print(
                    f"Journal: {metadata.get('container-title', [''])[0]}", file=output
                )
                print(f"Year: {validator._extract_year(metadata)}", file=output)
                print(f"\nFormatted citation ({args.style}):", file=output)
                print(validator.format_citation(metadata, args.style), file=output)
            else:
                print(f"✗ DOI is invalid or not found: {args.doi}", file=output)
                if metadata and "error" in metadata:
                    print(f"Error: {metadata['error']}", file=output)

        elif args.title:
            # Search by title
            results = validator.search_by_title(args.title)
            if results:
                print(f"Found {len(results)} matching works:\n", file=output)
                for i, work in enumerate(results, 1):
                    print(f"{i}. {work.get('title', [''])[0]}", file=output)
                    print(f"   DOI: {work.get('DOI', 'N/A')}", file=output)
                    print(
                        f"   Year: {validator._extract_year(work)}", file=output
                    )
                    print(
                        f"   Journal: {work.get('container-title', [''])[0]}\n",
                        file=output,
                    )
            else:
                print("No matching works found", file=output)

        elif args.validate_file:
            # Validate file of DOIs
            results = validator.validate_file(args.validate_file)
            print(f"Validation Results:", file=output)
            print(f"  Valid DOIs: {len(results['valid'])}", file=output)
            print(f"  Invalid DOIs: {len(results['invalid'])}", file=output)
            print(f"  Errors: {len(results['errors'])}\n", file=output)

            if results["valid"]:
                print("Valid DOIs:", file=output)
                for item in results["valid"]:
                    print(
                        f"  ✓ {item['doi']}: {item['metadata'].get('title', [''])[0]}",
                        file=output,
                    )

            if results["invalid"]:
                print("\nInvalid DOIs:", file=output)
                for doi in results["invalid"]:
                    print(f"  ✗ {doi}", file=output)

            if results["errors"]:
                print("\nErrors:", file=output)
                for item in results["errors"]:
                    print(f"  ⚠ {item['doi']}: {item['error']}", file=output)

        elif args.audit_bibliography:
            # Audit bibliography
            results = validator.audit_bibliography(args.audit_bibliography)
            print("Bibliography Audit Report\n" + "=" * 50, file=output)
            print(f"Total DOIs found: {results.get('total_dois', 0)}", file=output)
            print(f"Valid DOIs: {results.get('valid_dois', 0)}", file=output)
            print(f"Invalid DOIs: {results.get('invalid_dois', 0)}", file=output)
            print(f"Total titles: {results.get('total_titles', 0)}", file=output)
            print(
                f"Potentially missing DOIs: {results.get('missing_dois', 0)}",
                file=output,
            )

            if results.get("invalid_list"):
                print("\nInvalid DOIs:", file=output)
                for doi in results["invalid_list"]:
                    print(f"  ✗ {doi}", file=output)

        else:
            parser.print_help()

    finally:
        if args.output:
            output.close()


if __name__ == "__main__":
    main()
