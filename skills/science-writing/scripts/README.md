# Science Writing Scripts

## CrossRef Validator

`crossref_validator.py` - Validate DOIs and retrieve citation metadata using the CrossRef REST API.

### Installation

```bash
pip install requests
```

### Usage Examples

**Validate a single DOI:**
```bash
python crossref_validator.py --doi "10.1038/nature12373"
```

**Search for articles by title:**
```bash
python crossref_validator.py --title "CRISPR-Cas9 genome editing"
```

**Validate DOIs from a file (one per line):**
```bash
python crossref_validator.py --validate-file my_references.txt
```

**Audit a bibliography file:**
```bash
python crossref_validator.py --audit-bibliography references.bib --output audit_report.txt
```

**Format citations in different styles:**
```bash
python crossref_validator.py --doi "10.1038/nature12373" --style vancouver
python crossref_validator.py --doi "10.1038/nature12373" --style apa
python crossref_validator.py --doi "10.1038/nature12373" --style ieee
```

**Use your email for CrossRef polite pool (faster rate limits):**
```bash
python crossref_validator.py --doi "10.1038/nature12373" --email your.email@institution.edu
```

### Features

- **DOI Validation**: Verify DOIs exist in CrossRef database
- **Metadata Retrieval**: Get complete citation information (authors, title, journal, year, pages)
- **Title Search**: Find articles by searching titles
- **Multiple Citation Styles**: APA, Vancouver, AMA, IEEE, Chicago
- **Batch Processing**: Validate multiple DOIs from files
- **Bibliography Auditing**: Check bibliographies for missing or incorrect DOIs
- **Rate Limiting**: Respects CrossRef API rate limits (50 req/sec for polite pool)

### API Documentation

CrossRef REST API: https://www.crossref.org/documentation/retrieve-metadata/rest-api/

### Rate Limits

- **Public pool**: 50 requests/second
- **Polite pool**: 50 requests/second with better priority (provide email in User-Agent)
- **Plus pool**: Higher limits for CrossRef members

This script uses the polite pool by including a mailto address in the User-Agent header.

### Example Output

```
✓ DOI is valid: 10.1038/nature12373

Title: Multiplex Genome Engineering Using CRISPR/Cas Systems
Authors: 7 authors
Journal: Nature
Year: 2013

Formatted citation (apa):
Cong, L., Ran, F. A., Cox, D., Lin, S., Barretto, R., Habib, N., & Hsu, P. D. (2013).
Multiplex Genome Engineering Using CRISPR/Cas Systems. Nature, 501(7468), 385-388.
https://doi.org/10.1038/nature12373
```

### Error Handling

The script handles:
- Invalid DOI formats
- DOIs not found in CrossRef database
- Network timeouts and connection errors
- Missing metadata fields
- File I/O errors

### Integration with Reference Managers

The CrossRef API can enrich reference data from:
- BibTeX (.bib) files
- EndNote libraries
- Zotero collections
- Plain text reference lists

Simply export your references to a text file (one DOI per line) and use `--validate-file` to check them.
