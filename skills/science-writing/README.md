# Science Writing Skill

A comprehensive Claude Code skill for writing publication-quality scientific manuscripts with structured reference management, automated DOI validation via CrossRef API, and evidence-based writing principles.

## Overview

This skill provides expert guidance for scientific manuscript preparation based on:
- **Nature Masterclasses**: "How to write a first-class paper" (Gewin, 2018)
- **OSU Microbiology Writing Guide**: Scientific style standards
- **ICMJE Recommendations**: International Committee of Medical Journal Editors
- **EQUATOR Network**: Reporting guidelines (CONSORT, STROBE, PRISMA)
- **Leading style manuals**: AMA (11th ed.), APA (7th ed.), Vancouver

## Key Features

### 1. Evidence-Based Writing Principles
- **Clarity over complexity**: Precise language, logical flow, defined terms
- **Conciseness respects time**: Eliminate redundancy, use strong verbs
- **Accuracy builds credibility**: Exact values, consistent terminology
- **Objectivity maintains integrity**: Present results without bias

### 2. CrossRef API Integration
- Automated DOI validation and metadata retrieval
- Title verification against CrossRef database
- Multiple citation style formatting (APA, Vancouver, AMA, IEEE, Chicago)
- Batch processing for bibliography auditing

### 3. Structured Reference Management
- Always include DOIs for all journal articles
- Verify citations with CrossRef API before submission
- Prefer peer-reviewed sources, primary literature, recent publications
- Maintain <20% self-citations

### 4. IMRAD Structure & Venue Adaptation
- Standard IMRAD format for journal articles
- Venue-specific adaptations (Nature/Science, medical journals, ML conferences)
- Section-specific writing guidance with tense usage
- Length and emphasis appropriate to target venue

### 5. Two-Stage Writing Process
- **Stage 1**: Create structured outlines with bullet points
- **Stage 2**: Convert to flowing prose with complete paragraphs
- **Critical**: Never submit manuscripts with bullet points outside Methods

### 6. Comprehensive Citation Support
- Multiple citation styles with automated formatting
- Proper scientific nomenclature (microbial, genetic, viral, chemical)
- Field-specific terminology and conventions
- Integration with reference management tools

### 7. Reporting Guidelines
- Study-specific checklists (CONSORT, STROBE, PRISMA, STARD, ARRIVE, CARE)
- Ensures transparency and completeness
- Adherence to best practices for reproducibility

## Directory Structure

```
science-writing/
├── SKILL.md                          # Main skill documentation
├── README.md                         # This file
├── scripts/
│   ├── crossref_validator.py        # CrossRef API integration
│   └── README.md                     # Script documentation
├── references/
│   ├── imrad_structure.md           # IMRAD format guide
│   ├── citation_styles.md           # Citation style reference
│   ├── writing_principles.md        # Core writing principles
│   ├── figures_tables.md            # Data visualization guide
│   └── reporting_guidelines.md      # Study-specific guidelines
└── examples/
    └── example_manuscript_intro.md  # Example with two-stage process
```

## Quick Start

### Using the Skill

Invoke with `/science-writing` when writing manuscripts. The skill will guide you through:
1. Planning manuscript structure
2. Writing sections using two-stage process
3. Validating references with CrossRef API
4. Formatting citations in appropriate style
5. Applying reporting guidelines
6. Adapting for target venue

### Using CrossRef Validator

**Installation:**
```bash
pip install requests
```

**Validate a DOI:**
```bash
python .agents/skills/science-writing/scripts/crossref_validator.py --doi "10.1038/nature12373"
```

**Search by title:**
```bash
python .agents/skills/science-writing/scripts/crossref_validator.py --title "CRISPR genome editing"
```

**Audit bibliography:**
```bash
python .agents/skills/science-writing/scripts/crossref_validator.py \
    --audit-bibliography references.bib \
    --output audit_report.txt
```

**Format citation:**
```bash
python .agents/skills/science-writing/scripts/crossref_validator.py \
    --doi "10.1038/nature12373" \
    --style vancouver
```

## Supported Citation Styles

| Style | Primary Use | In-Text Format |
|-------|-------------|----------------|
| AMA | Medicine, health sciences | Superscript numbers¹ |
| Vancouver | Biomedical sciences | Brackets [1] |
| APA | Psychology, social sciences | Author-date (Smith, 2023) |
| Chicago | Humanities, some sciences | Notes or author-date |
| IEEE | Engineering, computer science | Brackets [1] |
| ACS | Chemistry | Superscript or numbered |
| NLM | Life sciences (PubMed) | Brackets [1] |

## Venue-Specific Adaptations

| Venue | Length | Focus | Writing Style |
|-------|--------|-------|---------------|
| **Nature/Science** | 2,000-4,500 words | Broad significance | Engaging, accessible |
| **Medical (NEJM/Lancet)** | 2,700-3,500 words | Clinical outcomes | Conservative, precise |
| **Field journals** | 3,000-6,000 words | Technical depth | Formal, comprehensive |
| **ML conferences** | ~6,000 words (8 pages) | Novel contribution | Direct, technical |

## Best Practices

### Always
- ✅ Write in complete paragraphs (never bullet points in final manuscript)
- ✅ Validate all DOIs with CrossRef API before submission
- ✅ Use two-stage writing process (outline → prose)
- ✅ Match writing style to target venue
- ✅ Apply appropriate reporting guidelines
- ✅ Use consistent terminology throughout
- ✅ Include DOIs for all journal articles

### Never
- ❌ Submit bullet points in Results or Discussion sections
- ❌ Over-interpret results or make unsupported claims
- ❌ Use citation chains (cite original sources)
- ❌ Mix tenses inappropriately within sections
- ❌ Include undefined acronyms or jargon
- ❌ Submit without validating reference completeness

## Common Pitfalls to Avoid

1. **Inappropriate statistics**: Ensure proper statistical methods and reporting
2. **Over-interpretation**: Distinguish observations from interpretations
3. **Poor methods**: Provide sufficient detail for reproducibility
4. **Writing quality**: Maintain logical flow and clear prose
5. **Inadequate literature review**: Cite recent, relevant primary sources
6. **Unclear figures**: Ensure self-explanatory captions and labels
7. **Missing reporting guidelines**: Follow CONSORT, STROBE, PRISMA as applicable

## Resources

### Reference Files
- `references/imrad_structure.md`: Complete IMRAD guide with venue variations
- `references/citation_styles.md`: All major citation styles with examples
- `references/writing_principles.md`: Evidence-based writing principles
- `references/figures_tables.md`: Data visualization best practices
- `references/reporting_guidelines.md`: Study-specific reporting standards

### External Resources
- **CrossRef API**: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- **ICMJE Recommendations**: http://www.icmje.org/
- **EQUATOR Network**: https://www.equator-network.org/
- **Nature Masterclasses**: https://masterclasses.nature.com/
- **Purdue OWL**: https://owl.purdue.edu/ (grammar and style)

### Reference Managers
- **Zotero**: Free, open-source, browser integration
- **Mendeley**: Free, PDF annotation capabilities
- **EndNote**: Commercial, comprehensive features
- **RefWorks**: Web-based, institutional subscriptions

## Changes from scientific-writing Skill

This modernized version includes:

1. **CrossRef API integration**: Automated DOI validation and metadata retrieval
2. **Updated documentation structure**: Aligned with Claude Code skills best practices
3. **Enhanced frontmatter**: Proper metadata and tool specifications
4. **Evidence-based principles**: Incorporated Nature, OSU, ICMJE guidance
5. **Venue-specific adaptations**: Detailed guidance for different publication types
6. **Practical examples**: Demonstration of two-stage writing process
7. **Executable scripts**: Working CrossRef validator with multiple features
8. **Improved organization**: Better structure for reference materials

## Version

**science-writing v1.0** - Created 2026-02-01

Based on:
- scientific-writing skill (original)
- Nature "How to write a first-class paper" (2018)
- OSU Microbiology Writing Guide
- Claude Code Skills Documentation
- CrossRef REST API (current)

## License

This skill is part of the .agents/skills collection for Claude Code.

## Contact

For issues or improvements, follow standard .agents/skills contribution guidelines.
