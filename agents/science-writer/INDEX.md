# Science Writer Agent - Documentation Index

Complete guide to using the science-writer agent for publication-quality manuscript preparation.

## Quick Links

- **[Agent Definition](science-writer.md)** - Core agent persona and skill integration
- **[User Guide (README)](science-writer-README.md)** - Comprehensive overview and usage guide
- **[Examples](science-writer-EXAMPLES.md)** - Detailed workflow examples with full conversations
- **[Quick Reference](science-writer-QUICK_REFERENCE.md)** - Condensed cheat sheet

## Documentation Structure

### 1. Core Agent Definition ([science-writer.md](science-writer.md))

The main agent file that defines:
- Persona (expert scientific writer and editor)
- Core principles (clarity, evidence-based, complete paragraphs)
- Mandatory skill usage (bio-logic, polars-dovmed, science-writing, bio-workflow-methods-docwriter, agent-browser)
- Workflow decision trees
- Task recognition patterns (keyword triggers)
- Communication style
- Quality gates
- Example interactions

**Use this file**: To invoke the agent in Claude Code
```bash
claude --agent /path/to/science-writer.md
```

### 2. User Guide ([science-writer-README.md](science-writer-README.md))

Comprehensive guide covering:
- Quick start instructions
- Available skills and when to use them
- Common use cases (literature reviews, manuscript sections, reviews, reference management)
- Workflow patterns (literature review, manuscript development, manuscript review)
- Core writing principles (clarity, conciseness, accuracy, objectivity)
- Quality checklist
- Venue-specific adaptations (Nature/Science, medical journals, field journals, ML conferences)
- Integration with other skills
- Troubleshooting
- File outputs
- Advanced features

**Use this**: When learning how to work with the agent or planning your workflow

### 3. Detailed Examples ([science-writer-EXAMPLES.md](science-writer-EXAMPLES.md))

Five complete workflow examples:
1. **Complete Literature Review** - CRISPR in thermophilic archaea for Nature Microbiology
2. **Methods Documentation** - Nextflow RNA-seq pipeline for Genome Research
3. **Manuscript Review** - RCT on vitamin D for depression (methodology + writing quality)
4. **Reference Management** - DOI validation and Vancouver formatting for 50 references
5. **Discussion Writing** - Mediterranean diet and CVD for AJCN

Each example includes:
- Full conversation with the agent
- Step-by-step skill usage
- Expected outputs
- Validation criteria

**Use this**: When you need a concrete template for your specific task

### 4. Quick Reference ([science-writer-QUICK_REFERENCE.md](science-writer-QUICK_REFERENCE.md))

Condensed cheat sheet with:
- One-line decision guide
- Skill selection matrix
- Keyword triggers
- Common workflows
- IMRAD structure guide
- Writing principles
- Tense guide
- Claim strength ladder
- Literature search patterns
- Evidence evaluation framework
- Reference management commands
- Venue adaptations
- Quality checklist
- Common mistakes
- Nomenclature rules
- Reporting guidelines
- Decision trees

**Use this**: When you need quick answers or reminders during active writing

## Getting Started

### 1. Choose Your Entry Point

**New to the agent?** Start with → [User Guide (README)](science-writer-README.md)

**Need a specific workflow?** Jump to → [Examples](science-writer-EXAMPLES.md)

**Want quick answers?** Check → [Quick Reference](science-writer-QUICK_REFERENCE.md)

**Ready to invoke?** Use → [Agent Definition](science-writer.md)

### 2. Understand the Skills

The science-writer agent orchestrates 5 specialized skills:

| Skill | What It Does | When to Use |
|-------|--------------|-------------|
| **polars-dovmed** | Search 2.4M PMC papers (full text) | Literature reviews, finding citations |
| **bio-logic** | Evaluate methodology and evidence quality | Assessing papers, self-critique, claim validation |
| **science-writing** | Write publication-quality prose | All manuscript sections, reference formatting |
| **bio-workflow-methods-docwriter** | Document computational pipelines | Methods sections for bioinformatics work |
| **agent-browser** | Web automation and scraping | Accessing databases, downloading supplements |

### 3. Common Tasks → Documentation Map

| Task | Start Here |
|------|------------|
| **"I need to write an Introduction"** | Quick Reference → Workflow → Example 1 |
| **"Document my Nextflow pipeline"** | Example 2 → bio-workflow-methods-docwriter section |
| **"Review this manuscript"** | Example 3 → Manuscript Review pattern |
| **"Find papers on X"** | Quick Reference → Literature Search → polars-dovmed |
| **"Validate my references"** | Example 4 → Reference Management |
| **"Write a Discussion"** | Example 5 → Discussion Writing |
| **"Is my claim too strong?"** | Quick Reference → Claim Strength Ladder + bio-logic |

## Key Concepts

### Two-Stage Writing Process
1. **Stage 1 - Outline**: Bullets with citations, data points, key arguments
2. **Stage 2 - Prose**: Convert bullets to flowing paragraphs with transitions

**Never submit Stage 1 as final text** - always convert to complete paragraphs.

### Evidence Evaluation
Use `/bio-logic` to:
- Assess study design appropriateness
- Identify biases
- Rate evidence quality (GRADE)
- Ensure claims match evidence strength

### DOI Validation
Use `/science-writing` with CrossRef API to:
- Validate all DOIs
- Retrieve complete metadata
- Format references in any citation style
- Detect retractions and errors

### Venue Adaptation
The agent automatically adapts to:
- **Nature/Science**: Broad significance, accessible, story-driven
- **Medical journals**: Conservative, strict IMRAD, CONSORT/STROBE
- **Field journals**: Technical depth, comprehensive Methods
- **ML conferences**: Numbered contributions, pseudocode, brief

## Workflow Patterns Summary

### Pattern 1: Literature Review
```
polars-dovmed (search) → bio-logic (evaluate) → science-writing (synthesize)
```

### Pattern 2: Manuscript Development
```
Plan → Literature (polars-dovmed) → Methods (bio-workflow-methods-docwriter or science-writing)
→ Results (science-writing) → Discussion (bio-logic + science-writing)
→ Introduction (polars-dovmed + science-writing) → Abstract (science-writing)
```

### Pattern 3: Manuscript Review
```
bio-logic (methodology) + science-writing (prose) → Structured review
```

## Quality Standards

Every manuscript section must pass:
- ✓ Complete paragraphs (no bullets except Methods criteria)
- ✓ All DOIs validated via CrossRef API
- ✓ Proper tense for section type
- ✓ Claims matched to evidence strength
- ✓ IMRAD or venue-specific structure
- ✓ Reporting guideline compliance
- ✓ Correct nomenclature (*E. coli*, *gfp*)
- ✓ Statistics complete (effect sizes, CIs)

## Tips for Best Results

1. **Specify target venue** - Helps agent adapt tone and structure
2. **Request evidence evaluation** - Use /bio-logic for claim validation
3. **Use two-stage process** - Outline first, then convert to prose
4. **Validate all DOIs** - Always use CrossRef API
5. **Match claims to evidence** - Observational = "associated", RCT = "reduced"
6. **Be specific with limitations** - "35% dropout" not "small sample"

## Related Documentation

### Within This Agent Collection
- [Omics Scientist Agent](omics-scientist.md) - For bioinformatics analysis workflows
- [DataViz Artist Agent](dataviz-artist.md) - For publication-quality figures

### External Skills Documentation
- `/bio-logic` skill documentation - Scientific reasoning frameworks
- `/science-writing` skill documentation - Writing principles and citation styles
- `/polars-dovmed` skill documentation - Literature search API
- `/bio-workflow-methods-docwriter` skill documentation - Pipeline documentation

## Support and Customization

### Modify Agent Behavior
Edit `science-writer.md` to:
- Add new workflow patterns
- Customize venue adaptations
- Add domain-specific nomenclature rules
- Adjust communication style

### Report Issues
Document problems and share with the community.

### Extend with New Examples
Add workflows to `science-writer-EXAMPLES.md` following the established format.

## Version History

- **v1.0** (2025-02-01) - Initial release
  - 5 core skills integrated
  - Comprehensive documentation
  - 5 detailed examples
  - Quick reference guide

---

**Quick Navigation**

- [← Back to Agent Definition](science-writer.md)
- [→ Start with User Guide](science-writer-README.md)
- [→ See Examples](science-writer-EXAMPLES.md)
- [→ Quick Reference](science-writer-QUICK_REFERENCE.md)
