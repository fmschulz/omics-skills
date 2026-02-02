# Science Writer Agent - User Guide

## Overview

The **science-writer** agent is an expert scientific writer and editor that helps you create publication-quality manuscripts for peer-reviewed journals. Whether you need to conduct literature reviews, evaluate research rigor, write manuscript sections, or manage references, this agent selects the right tools and applies evidence-based writing principles.

## Quick Start

```bash
# Invoke the agent
claude --agent /home/fschulz/dev/omics-skills/agents/science-writer.md

# Or copy to user directory
cp science-writer.md ~/.claude/agents/
claude --agent science-writer
```

## Available Skills

| Skill | Purpose | Best For |
|-------|---------|----------|
| **bio-logic** | Scientific reasoning & evaluation | Methodology critique, evidence assessment, bias detection |
| **polars-dovmed** | Literature search (2.4M PMC papers) | Comprehensive literature reviews, finding papers, trend analysis |
| **science-writing** | Manuscript writing & editing | All manuscript sections, reference management, DOI validation |
| **bio-workflow-methods-docwriter** | Methods documentation | Documenting computational pipelines with exact commands/versions |
| **agent-browser** | Web automation & scraping | Accessing databases, downloading supplements, screenshots |

## Common Use Cases

### 1. Literature Review

**Need**: Comprehensive literature review on a specific topic

**Skills Used**: `/polars-dovmed` → `/bio-logic` → `/science-writing`

**Example**:
```
You: "Write a literature review on CRISPR-Cas systems in thermophilic archaea."

Agent:
1. /polars-dovmed - Search 2.4M PMC papers for relevant literature
2. /bio-logic - Evaluate evidence quality and methodology of key papers
3. /science-writing - Synthesize into flowing prose with validated DOIs
```

### 2. Manuscript Section Writing

**Need**: Write Introduction section for research paper

**Skills Used**: `/polars-dovmed` + `/science-writing`

**Example**:
```
You: "Write the Introduction for my paper on antibiotic resistance mechanisms."

Agent:
1. /polars-dovmed - Find background literature, recent discoveries
2. /science-writing - Structure as: broad context → prior work → gap → question
3. Two-stage process: outline with citations → flowing paragraphs
```

### 3. Methods Documentation (Computational)

**Need**: Document bioinformatics pipeline for Methods section

**Skills Used**: `/bio-workflow-methods-docwriter` + `/science-writing`

**Example**:
```
You: "Document this Nextflow RNA-seq pipeline for the Methods section."

Agent:
1. /bio-workflow-methods-docwriter - Extract exact commands, versions, parameters
2. /science-writing - Polish prose, add tool citations, format for venue
```

### 4. Manuscript Review

**Need**: Critical review of manuscript for methodological rigor

**Skills Used**: `/bio-logic` + `/science-writing`

**Example**:
```
You: "Review this manuscript for methodology and writing quality."

Agent:
1. /bio-logic - Critique study design, statistics, biases, evidence strength
2. /science-writing - Assess IMRAD structure, tense, citations, reporting guidelines
```

### 5. Reference Management

**Need**: Validate and format references with DOI verification

**Skills Used**: `/science-writing`

**Example**:
```
You: "Validate all DOIs in my reference list and format in AMA style."

Agent: /science-writing
- CrossRef API validation for each DOI
- Retrieve complete metadata (authors, title, journal, year)
- Format in AMA style with superscript numbers
- Report any missing or invalid DOIs
```

## Workflow Patterns

### Pattern 1: Complete Literature Review
```
Literature Search
    ↓
/polars-dovmed
    ├─ Search 2.4M PMC papers
    ├─ Extract PMC IDs, DOIs, metadata
    └─ Identify publication trends
    ↓
Evidence Evaluation
    ↓
/bio-logic
    ├─ Assess methodology
    ├─ Rate evidence quality (GRADE)
    ├─ Identify biases
    └─ Evaluate claim strength
    ↓
Synthesis & Writing
    ↓
/science-writing
    ├─ Create outline with citations
    ├─ Convert to flowing prose
    ├─ Validate DOIs (CrossRef API)
    └─ Format for target journal
```

### Pattern 2: Manuscript Development (IMRAD)
```
Planning
    ├─ Identify target journal
    ├─ Review author guidelines
    └─ Select reporting guideline
    ↓
Literature Gathering (/polars-dovmed)
    ↓
Methods Documentation
    ├─ Computational: /bio-workflow-methods-docwriter
    └─ Experimental: /science-writing
    ↓
Results Writing (/science-writing)
    ├─ Objective description
    ├─ Figure/table integration
    └─ Past tense
    ↓
Discussion Writing
    ├─ /bio-logic (evaluate your evidence)
    ├─ /science-writing (synthesize interpretation)
    └─ Present tense for interpretation
    ↓
Introduction Writing
    ├─ /polars-dovmed (background literature)
    └─ /science-writing (broad → specific → gap → question)
    ↓
Abstract & Finalization (/science-writing)
```

### Pattern 3: Manuscript Review
```
Methodological Review
    ↓
/bio-logic
    ├─ Study design appropriateness
    ├─ Statistical methods
    ├─ Bias assessment
    ├─ Evidence-to-claim match
    └─ GRADE rating
    ↓
Writing Quality Review
    ↓
/science-writing
    ├─ IMRAD structure adherence
    ├─ Paragraph flow & transitions
    ├─ Tense consistency
    ├─ DOI validation (CrossRef)
    ├─ Citation formatting
    └─ Reporting guideline compliance
    ↓
Deliver Structured Review
    ├─ Strengths
    ├─ Concerns (critical/important/minor)
    ├─ Evidence rating
    └─ Specific recommendations
```

## Core Writing Principles

The agent follows evidence-based principles from Nature Masterclasses, ICMJE, and scientific communication research:

### 1. Clarity Over Complexity
- One idea per sentence
- Define technical terms at first use
- Logical flow with transitions
- Active voice when it improves clarity

### 2. Conciseness Respects Time
- Eliminate redundancy ("because" not "due to the fact that")
- Strong verbs ("analyzed" not "performed an analysis")
- 15-20 words per sentence average

### 3. Accuracy Builds Credibility
- Report exact values with appropriate precision
- Distinguish observations from interpretations
- Match precision to measurement capability
- Validate all citations with DOI lookup

### 4. Objectivity Maintains Integrity
- Present results without bias
- Acknowledge conflicting evidence
- Appropriate hedging based on evidence strength
- Use `/bio-logic` to ensure claims match evidence

### 5. Complete Paragraphs Only
- **Never use bullet points** in final manuscripts
- Only exception: Methods inclusion/exclusion criteria
- Two-stage process: outline → flowing prose

## Quality Checklist

Before delivery, the agent validates:

- [ ] **Structure**: IMRAD or venue-specific format adhered to
- [ ] **Evidence**: All claims supported by DOI-validated citations
- [ ] **Prose**: Complete paragraphs with transitions (no bullets)
- [ ] **Clarity**: One idea per sentence, 15-20 words average
- [ ] **Tense**: Appropriate for each section
- [ ] **Nomenclature**: Correct italicization, capitalization
- [ ] **Statistics**: Effect sizes, CIs, appropriate tests
- [ ] **Reporting**: Relevant guidelines followed (CONSORT, STROBE, etc.)

## Tips for Working with the Agent

### 1. Specify Target Venue
```
✅ "Write Introduction for Nature paper (broad significance, accessible)"
✅ "Format references for NEJM (Vancouver style, conservative)"
❌ "Write an Introduction"
```

### 2. Mention Section Type
```
✅ "Write Methods section for RNA-seq pipeline (computational workflow)"
✅ "Write Discussion interpreting these findings (past: 'we found', present: 'suggests')"
❌ "Write about the results"
```

### 3. Request Literature Search Specifics
```
✅ "Search PMC for papers on mRNA vaccines 2020-2025, focus on efficacy"
✅ "Find recent CRISPR reviews with DOIs"
❌ "Find papers on this topic"
```

### 4. Ask for Evidence Evaluation
```
✅ "Evaluate this RCT's methodology using GRADE framework"
✅ "Assess if these causal claims are justified by the study design"
❌ "Is this study good?"
```

## Venue-Specific Adaptations

| Venue | Style | Structure | Methods | Word Count |
|-------|-------|-----------|---------|------------|
| **Nature/Science** | Engaging, accessible | Story-driven | Supplement | 2,000-4,500 |
| **Medical (NEJM/Lancet)** | Conservative, precise | Strict IMRAD | Main text | 2,700-3,500 |
| **Field journals** | Technical, comprehensive | IMRAD | Main text | 3,000-6,000 |
| **ML conferences** | Direct, technical | Numbered contributions | Concise | ~6,000 (8 pages) |

The agent automatically adapts to your target venue.

## Integration with Other Skills

The science-writer can integrate with:

- `/citation-management` - Academic reference management
- `/literature-review` - Multi-database systematic reviews (PubMed, arXiv, bioRxiv, Semantic Scholar)
- `/scientific-critical-thinking` - Research rigor evaluation
- `/peer-review` - Systematic peer review toolkit
- `/statistical-analysis` - Statistical tests and interpretation
- `/matplotlib` - Publication-quality figures
- `/exploratory-data-analysis` - Analyze result files

## Troubleshooting

**Q: Agent not finding enough papers?**
A: `/polars-dovmed` searches 2.4M PMC papers (full text). Try broader terms or synonyms.

**Q: DOI validation failing?**
A: `/science-writing` uses CrossRef API. Check internet connection and DOI format (10.xxxx/xxxxx).

**Q: Claims seem too strong for the evidence?**
A: Ask agent to "evaluate evidence strength using /bio-logic" and "revise with appropriate hedging".

**Q: Methods section too vague for reproducibility?**
A: For computational work, use `/bio-workflow-methods-docwriter` with pipeline artifacts. For experimental, request "sufficient detail for replication".

**Q: Writing still has bullet points?**
A: Agent enforces "complete paragraphs only" rule. If bullets persist, explicitly request "convert all bullets to flowing prose".

## File Outputs

### Manuscripts
- `manuscript_draft.md` - Main manuscript text
- `references.bib` - Bibliography (with validated DOIs)
- `METHODS.md` - Detailed Methods (if computational workflow)
- `run_manifest.yaml` - Machine-readable workflow metadata

### Reviews
- `review_report.md` - Structured critique with evidence ratings
- `doi_validation_report.txt` - CrossRef validation results

### Literature
- `literature_search_results.csv` - PMC search results with DOIs, metadata
- `evidence_summary.md` - Synthesized findings with quality ratings

## Examples by Discipline

### Biomedical Research
```
"Write the Discussion section for my RCT on diabetes treatment.
We found 15% HbA1c reduction (p<0.001, 95% CI: 12-18%). Target: NEJM."

Agent:
1. /bio-logic - Evaluate evidence strength, check if causal claim justified
2. /polars-dovmed - Find context (prior RCTs, meta-analyses)
3. /science-writing - Write Discussion:
   - Your findings (past: "We found 15% reduction...")
   - Interpretation (present: "This suggests...")
   - Context with prior literature
   - Specific limitations (not generic)
   - Clinical implications
4. Conservative tone for NEJM, strict IMRAD
```

### Computational Biology
```
"Document this Nextflow metagenome assembly pipeline for Methods."

Agent:
1. /bio-workflow-methods-docwriter
   - Extract commands from .command.sh files
   - Capture tool versions from software_versions.yml
   - Document parameters and QC gates
   - Create workflow summary (5-12 lines)
2. /science-writing
   - Add tool citations
   - Format for target journal
   - Ensure reproducibility section
```

### Machine Learning (Conference)
```
"Write Introduction for NeurIPS paper on novel attention mechanism."

Agent: /science-writing
- Numbered contributions in Introduction (NeurIPS style)
- Mathematical notation and pseudocode
- Brief literature review (2-3 years, arXiv acceptable)
- Technical, direct tone
- ~6,000 words (8 pages)
```

## Advanced Features

### CrossRef API Integration
- Automatic DOI validation
- Metadata retrieval (authors, title, journal, year)
- Title verification
- Multiple citation style formatting
- Batch processing of bibliographies

### Evidence Evaluation (GRADE)
- High/Moderate/Low/Very Low evidence rating
- Bias assessment (selection, performance, detection, attrition)
- Risk of bias using Cochrane ROB 2.0
- Claim proportionality checking

### Literature Search
- Full-text search across 2.4M PMC papers (not just abstracts)
- Advanced pattern matching (AND/OR logic)
- Extract structured data (GenBank accessions, methods, etc.)
- Publication trend analysis by year

### Workflow Documentation
- Exact command extraction from pipeline artifacts
- Tool version pinning (software_versions.yml, conda env)
- Container digest recording
- Machine-readable run manifests

## Manuscript Development Workflow

### Phase 1: Planning
1. Identify target journal
2. Review author guidelines
3. Determine reporting guideline (CONSORT, STROBE, etc.)
4. `/polars-dovmed` - Comprehensive literature search
5. `/bio-logic` - Evaluate key papers

### Phase 2: Drafting (Two-Stage Process)

For each section:
- **Stage 1 - Outline**: Bullets with citations, data points
- **Stage 2 - Prose**: `/science-writing` converts to flowing paragraphs

Order:
1. Methods → `/bio-workflow-methods-docwriter` (computational) or `/science-writing` (experimental)
2. Results → Objective description (past tense)
3. Discussion → `/bio-logic` (evaluate evidence) → `/science-writing` (interpret)
4. Introduction → `/polars-dovmed` (literature) → `/science-writing` (synthesize)
5. Abstract → Synthesis of complete story

### Phase 3: Revision
1. `/bio-logic` - Self-critique (do conclusions match evidence?)
2. `/science-writing` - Refine (DOI validation, IMRAD, tense, flow)
3. Apply venue-specific formatting

### Phase 4: Finalization
1. Reference formatting and DOI validation
2. Reporting guideline checklist
3. Figure/table captions
4. Supplementary materials

## Support

- **Modify agent behavior**: Edit `science-writer.md`
- **Add new workflows**: Document in examples
- **Report issues**: Share feedback

---

**Remember**: The agent is a precision specialist. Always start with understanding the target venue, evidence quality, and writing conventions before drafting text.
