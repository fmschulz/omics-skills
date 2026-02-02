# Science Writer Agent - Quick Reference

## One-Line Decision Guide

```
Literature search? → polars-dovmed
Evidence evaluation? → bio-logic
Write manuscript? → science-writing (two-stage: outline → prose)
Document pipeline? → bio-workflow-methods-docwriter
Web database? → agent-browser
```

## Skill Selection Matrix

| You Need | Use This Skill |
|----------|----------------|
| **Search 2.4M PMC papers** | `/polars-dovmed` |
| **Evaluate methodology/evidence** | `/bio-logic` |
| **Write any manuscript section** | `/science-writing` |
| **Document computational workflow** | `/bio-workflow-methods-docwriter` |
| **Access web databases** | `/agent-browser` |

## Keyword Triggers

| Keywords | Auto-Trigger Skill |
|----------|-------------------|
| "search papers", "find literature", "PMC", "PubMed", "publication trends" | `/polars-dovmed` |
| "evaluate", "critique", "methodology", "bias", "evidence quality", "GRADE" | `/bio-logic` |
| "write", "manuscript", "Abstract", "Introduction", "Methods", "Results", "Discussion" | `/science-writing` |
| "document workflow", "Nextflow", "Snakemake", "pipeline", "tool versions" | `/bio-workflow-methods-docwriter` |
| "browser", "navigate", "scrape", "screenshot", "download supplement" | `/agent-browser` |

## Common Workflows

### 1. Literature Review
```
polars-dovmed (search 2.4M papers)
    ↓
bio-logic (evaluate evidence quality)
    ↓
science-writing (synthesize into prose)
```

### 2. Manuscript Section
```
polars-dovmed (find citations)
    ↓
science-writing
    ├─ Stage 1: Outline with citations
    └─ Stage 2: Convert to flowing paragraphs
```

### 3. Methods Documentation
```
bio-workflow-methods-docwriter (extract from artifacts)
    ↓
science-writing (polish, add citations, format)
```

### 4. Manuscript Review
```
bio-logic (methodology critique)
    +
science-writing (writing quality)
    ↓
Structured review
```

## IMRAD Structure

| Section | Tense | Content |
|---------|-------|---------|
| **Abstract** | Past (methods/results), Present (conclusions) | Brief summary of all sections |
| **Introduction** | Present (background), Past (prior work) | Broad → specific → gap → question |
| **Methods** | Past | Sufficient detail for replication |
| **Results** | Past | Objective description, no interpretation |
| **Discussion** | Past (findings), Present (interpretation) | Findings → mechanisms → context → limitations → implications |

## Writing Principles

### The Golden Rules
1. **Complete paragraphs only** (never bullets in final manuscripts)
2. **Two-stage process**: Outline → Prose
3. **Validate all DOIs** via CrossRef API
4. **Match claims to evidence** (observational = "associated", RCT = "reduced")
5. **15-20 words/sentence** average

### Tense Guide
- **Present**: Established facts, interpretations ("Exercise improves health")
- **Past**: Methods, results, prior studies ("We found...", "Smith et al. reported...")

### Claim Strength Ladder

| Language | Requires |
|----------|----------|
| "Proves" / "Demonstrates" | Strong experimental evidence |
| "Suggests" / "Indicates" | Observational with controls |
| "Associated with" | Observational, no causal claim |
| "May" / "Might" | Preliminary/hypothesis-generating |

## Literature Search (polars-dovmed)

### API Endpoints
- `search_literature` - Search 2.4M PMC papers
- `extract_structured_data` - Extract GenBank IDs, patterns
- `count_papers_by_year` - Publication trends
- `get_paper_details` - Full metadata + text
- `scan_literature_advanced` - Complex multi-pattern queries

### Common Patterns
```python
# Simple search
{
  "query": "CRISPR thermophilic archaea",
  "max_results": 100
}

# Advanced search (AND/OR logic)
{
  "primary_queries": {
    "crispr": [["CRISPR-Cas9"], ["Cas proteins"]],  # OR
    "organisms": [["Sulfolobus", "thermophilic"]]  # AND within
  }
}
```

## Evidence Evaluation (bio-logic)

### Quick Assessment Framework

```
1. Study design → matches research question?
2. Sample size → justified (power analysis)?
3. Confounders → identified and controlled?
4. Statistics → appropriate tests, CIs, effect sizes?
5. Claims → match evidence strength?
```

### GRADE Levels
- **HIGH**: RCT, large effect, no major limitations
- **MODERATE**: RCT with limitations, or strong observational
- **LOW**: Observational, small effect, some confounding
- **VERY LOW**: Major limitations, inconsistent, indirect

### Common Biases
- Selection bias (who was included/excluded)
- Performance bias (treatment differences beyond intervention)
- Detection bias (outcome assessment not blinded)
- Attrition bias (differential dropout)
- Reporting bias (selective outcome reporting)

## Reference Management (science-writing)

### CrossRef API Validation

```bash
# Validate DOI
python scripts/crossref_validator.py --doi "10.1038/nature12373"

# Lookup by title
python scripts/crossref_validator.py --title "CRISPR-Cas9"

# Batch validation
python scripts/crossref_validator.py --validate-file references.txt

# Format in citation style
python scripts/crossref_validator.py --doi "10.1038/..." --style vancouver
```

### Citation Styles
- **AMA**: Superscript numbers (medical)
- **Vancouver**: Brackets [1] (biomedical)
- **APA**: (Author, Year) - psychology, social sciences
- **IEEE**: Brackets [1] (engineering)
- **Chicago**: (Author Year) - humanities

## Venue Adaptations

| Venue | Tone | Length | Methods | Key Features |
|-------|------|--------|---------|--------------|
| **Nature/Science** | Engaging, accessible | 2-4.5K | Supplement | Broad significance first |
| **NEJM/Lancet** | Conservative, precise | 2.7-3.5K | Main text | Strict IMRAD, CONSORT |
| **Field journals** | Technical | 3-6K | Main text | Comprehensive |
| **ML conferences** | Direct, technical | ~6K (8 pages) | Concise | Numbered contributions |

## Quality Checklist

Before submission:
- [ ] **Complete paragraphs** (no bullets except Methods criteria)
- [ ] **All DOIs validated** via CrossRef API
- [ ] **Proper tense** for each section
- [ ] **Nomenclature correct** (*E. coli*, *gfp*)
- [ ] **Claims match evidence** (appropriate hedging)
- [ ] **IMRAD structure** (or venue-specific)
- [ ] **Reporting guideline** followed (CONSORT/STROBE/etc.)
- [ ] **Statistics complete** (effect sizes, CIs, not just p-values)

## Common Mistakes to Avoid

| Mistake | Fix |
|---------|-----|
| Bullet points in Discussion | Convert to flowing prose with transitions |
| "Due to the fact that" | "Because" (concise) |
| "Performed an analysis" | "Analyzed" (strong verb) |
| Correlation → causation | Use "associated with" for observational |
| Missing DOIs | Validate with CrossRef API |
| Generic limitations | Specific: "35% dropout" not "small sample" |
| Present tense in Results | Past tense: "showed" not "shows" |

## Nomenclature Rules

### Microbial Names
- *Escherichia coli* (full, first use)
- *E. coli* (abbreviated, subsequent)
- *E. coli* subsp. *aureus* (infrasubspecific)

### Genetic Nomenclature
- **Gene**: *lacZ*, *gfp* (italicized, lowercase)
- **Phenotype**: Lac+, GFP+ (not italicized, superscript)
- **Deletion**: Δ*lacZ*
- **Insertion**: *lacZ::Tn10*

## Reporting Guidelines

| Study Type | Guideline | Key Items |
|------------|-----------|-----------|
| RCT | CONSORT | Flow diagram, randomization, blinding |
| Observational | STROBE | Design, variables, bias |
| Systematic review | PRISMA | Search strategy, selection |
| Diagnostic | STARD | Index test, reference standard |
| Prediction model | TRIPOD | Development/validation |
| Animal research | ARRIVE | Species, procedures |

## Workflow Documentation (bio-workflow-methods-docwriter)

### Inputs
- Pipeline artifacts (Nextflow work/ dir, Snakemake logs)
- `software_versions.yml` or conda env export
- `params.json` or config files
- Run logs and QC reports

### Outputs
- Workflow summary (5-12 lines, plain language)
- METHODS.md (step-by-step with exact commands)
- `run_manifest.yaml` (machine-readable metadata)
- Reproducibility command

### Quality Gates
- Every step: purpose, inputs, outputs, command, tool+version
- No "NOT CAPTURED" for major tools
- Reproducibility section complete

## Decision Trees

### "I need to write a manuscript section"
```
IF Introduction/Results/Discussion
  THEN /science-writing
    1. Outline with citations
    2. Convert to prose
    3. Validate DOIs

IF Methods (computational)
  THEN /bio-workflow-methods-docwriter
  → /science-writing (polish)

IF Methods (experimental)
  THEN /science-writing (sufficient detail for replication)
```

### "I need to find papers"
```
IF comprehensive search (2.4M PMC papers, full text)
  THEN /polars-dovmed

IF web databases (NCBI, Uniprot, authenticated)
  THEN /agent-browser

IF specific DOI lookup
  THEN /science-writing (CrossRef API)
```

### "I need to review a manuscript"
```
ALWAYS both:
  1. /bio-logic (methodology, statistics, biases, evidence quality)
  2. /science-writing (IMRAD, tense, DOIs, reporting guidelines)
```

## Integration Examples

### Example 1: Complete Introduction
```
1. /polars-dovmed "CRISPR thermophilic archaea"
   → Get: 87 papers with PMC IDs, DOIs

2. /bio-logic (evaluate top 10 papers)
   → Get: GRADE ratings, evidence quality

3. /science-writing (two-stage)
   Stage 1: Outline with citations
   Stage 2: Flowing prose with transitions

Output: 2-3 paragraphs, DOI-validated, proper tense
```

### Example 2: Methods for Pipeline
```
1. /bio-workflow-methods-docwriter (extract from artifacts)
   → Get: Exact commands, versions, workflow summary

2. /science-writing (add tool citations, format for venue)
   → Get: Publication-ready Methods section

Output: METHODS.md with reproducibility details
```

### Example 3: Evidence-Based Discussion
```
1. /bio-logic (evaluate your own study design)
   → Get: Claim strength, appropriate language

2. /polars-dovmed (find context literature)
   → Get: Prior studies for comparison

3. /science-writing (synthesize interpretation)
   → Get: Discussion with matched claims

Output: Discussion with appropriate hedging
```

## Quick Commands

### DOI Validation
```bash
# Single DOI
python scripts/crossref_validator.py --doi "10.xxxx/xxxxx"

# Batch file
python scripts/crossref_validator.py --validate-file refs.txt

# Format in style
python scripts/crossref_validator.py --doi "10.xxxx/xxxxx" --style ama
```

### Literature Search
```python
import httpx

# Search PMC
response = httpx.post(
    "https://api.newlineages.com/api/search_literature",
    headers={"X-API-Key": "your_key"},
    json={"query": "CRISPR archaea", "max_results": 50},
    timeout=120.0
)
results = response.json()
```

## Output Files

### Manuscripts
- `manuscript_draft.md` - Main text
- `references.bib` - Bibliography
- `METHODS.md` - Computational methods
- `run_manifest.yaml` - Workflow metadata

### Reviews
- `review_report.md` - Structured critique
- `evidence_rating.md` - GRADE assessment
- `doi_validation_report.txt` - CrossRef results

### Literature
- `literature_search_results.csv` - PMC papers
- `evidence_summary.md` - Synthesis with ratings

## Tips for Success

1. **Always specify venue** - "Nature", "NEJM", "NeurIPS"
2. **Request evidence evaluation** - "Use /bio-logic to assess claim strength"
3. **Validate all DOIs** - "Check with CrossRef API"
4. **Two-stage writing** - Outline → Prose
5. **Match claims to evidence** - Observational = "associated", RCT = "reduced"

## Common Workflows by Task

| Task | Workflow |
|------|----------|
| Lit review | polars-dovmed → bio-logic → science-writing |
| Write Introduction | polars-dovmed → science-writing (outline → prose) |
| Write Methods | bio-workflow-methods-docwriter OR science-writing |
| Write Discussion | bio-logic (evaluate) → science-writing (interpret) |
| Review manuscript | bio-logic + science-writing |
| Manage references | science-writing (CrossRef validation) |

## Remember

1. **Design first** - Understand venue, evidence quality, conventions
2. **Complete paragraphs** - Never bullets in final text
3. **Validate DOIs** - Always use CrossRef API
4. **Match claims** - Evidence strength determines language
5. **Two stages** - Outline with citations → Flowing prose
6. **Appropriate tense** - Past for methods/results, present for interpretation

## Emergency Troubleshooting

**No papers found?** → Broader terms, check spelling, try synonyms
**DOI invalid?** → Verify format (10.xxxx/xxxxx), check CrossRef
**Claims too strong?** → Use /bio-logic to evaluate evidence, add hedging
**Still have bullets?** → Use /science-writing two-stage process
**Methods too vague?** → For pipelines: /bio-workflow-methods-docwriter

## Key Differences from Other Agents

| Feature | Science Writer | Omics Scientist | DataViz Artist |
|---------|---------------|-----------------|----------------|
| **Focus** | Writing & literature | Analysis workflows | Visualization |
| **Output** | Manuscripts, reviews | Analysis results | Figures, dashboards |
| **Evaluation** | Evidence quality | Data quality | Design quality |
| **Main skill** | science-writing | bio-* skills | beautiful-data-viz |
