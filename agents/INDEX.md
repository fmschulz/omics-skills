# Omics Scientist Agent - Complete Documentation Index

## Quick Start

**To use the agent:**
```bash
claude --agent /home/fschulz/dev/omics-skills/agents/omics-scientist.md
```

## Documentation Files

### 1. **omics-scientist.md** (411 lines)
**Main agent system prompt**
- Complete persona definition
- All 17 skills (bio-logic + 16 bio-* skills)
- Mandatory skill usage directives
- Workflow decision trees
- Keyword triggers
- Communication style
- Quality gates
- Example interactions

**Key Sections:**
- Scientific Reasoning (bio-logic) - NEW!
- Project initialization
- 16 specialized bioinformatics workflows
- Integration examples

### 2. **README.md** (228 lines)
**User guide and usage instructions**
- How to invoke the agent
- Available skills table
- Workflow examples (updated with bio-logic)
- Capabilities overview
- Tips and troubleshooting
- Integration with other skills

### 3. **EXAMPLES.md** (746 lines)
**Detailed workflow examples**
- 11 complete example scenarios
- 3 NEW bio-logic examples:
  - Example 9: Scientific reasoning & interpretation
  - Example 10: Experimental design
  - Example 11: Method selection reasoning
- Input/output examples
- Conversation templates

### 4. **QUICK_REFERENCE.md** (352 lines)
**Cheat sheet for rapid lookup**
- One-line decision guide
- Skill selection matrix
- Keyword triggers (bio-logic first)
- Common workflows
- Decision tree (if-then logic)
- Quality gates
- Resource requirements
- Common errors & fixes
- Bio-logic quick examples (NEW!)

### 5. **BIO-LOGIC_INTEGRATION.md** (374 lines)
**Detailed documentation of bio-logic integration**
- Integration locations (9 major sections)
- File growth summary (+28% total)
- Key design principles
- Usage patterns
- Trigger phrases
- Success metrics
- Before/after comparison

### 6. **ARCHITECTURE.md** (517 lines)
**System architecture documentation**
- Three-layer architecture
- Skill interaction patterns
- Data flow diagrams
- Decision matrix
- Keyword recognition system
- Quality gates flowchart
- Agent state machine
- Skill dependency graph
- Information flow

## Total Documentation

- **Files**: 6 comprehensive documents
- **Total Lines**: 2,628 lines
- **Total Size**: ~76 KB

## Key Features

### Bio-Logic Integration (NEW!)

The **bio-logic** skill is now deeply integrated for scientific reasoning:

**Triggers automatically on:**
- why, how, explain, interpret
- hypothesis, design experiment
- reasoning, mechanism, justify
- evidence, causal, confound

**Used for:**
1. Hypothesis formation
2. Experimental design
3. Method selection
4. Result interpretation
5. Causal reasoning
6. Evidence evaluation
7. Alternative explanations
8. Confound identification

### 16 Bioinformatics Skills

| Category | Skills |
|----------|--------|
| **Foundation** | bio-foundation-housekeeping, fasta-database-curator |
| **Processing** | bio-reads-qc-mapping, bb-skill |
| **Assembly** | bio-assembly-qc |
| **Binning** | bio-binning-qc |
| **Genes** | bio-gene-calling |
| **Annotation** | bio-annotation-taxonomy, bio-structure-annotation |
| **Analysis** | bio-phylogenomics, ssu-sequence-analysis, bio-protein-clustering-pangenome |
| **Specialized** | bio-viromics, hmm-mmseqs-workflow |
| **Reporting** | bio-stats-ml-reporting |
| **Debug** | pipeline-debugger |

## Workflow Patterns

All workflows now include bio-logic:

```
bio-logic (plan)
    ↓
technical skills (execute)
    ↓
bio-logic (interpret)
    ↓
reporting
```

## Usage Tips

1. **Ask "why" and "how" liberally** - Triggers bio-logic automatically
2. **Start with project setup** - bio-foundation-housekeeping
3. **Provide biological context** - Helps reasoning and parameter selection
4. **Request interpretations** - Agent explains biological significance
5. **Challenge assumptions** - Ask for alternative explanations

## Common Use Cases

### Research Questions
```
"Why am I seeing X?" → bio-logic evaluates hypotheses
"How can I prove Y?" → bio-logic designs experiment
"What does Z mean?" → bio-logic interprets biologically
```

### Method Selection
```
"Should I use X or Y?" → bio-logic evaluates trade-offs
"What's the best approach?" → bio-logic justifies recommendations
```

### Workflows
```
"I have raw reads" → Complete genome analysis workflow
"I have a metagenome" → MAG recovery workflow
"I have multiple genomes" → Comparative genomics workflow
```

## Integration Philosophy

The agent is a **scientific reasoning partner**, not just a tool executor:

- **Thinks** before executing (bio-logic)
- **Reasons** about methods (bio-logic)
- **Executes** with best practices (bio-* skills)
- **Interprets** biologically (bio-logic)
- **Generates** hypotheses (bio-logic)

## File Recommendations

| If You Want | Read This File |
|------------|----------------|
| Quick overview | README.md |
| See examples | EXAMPLES.md |
| Rapid lookup | QUICK_REFERENCE.md |
| Understand bio-logic | BIO-LOGIC_INTEGRATION.md |
| System design | ARCHITECTURE.md |
| Modify agent | omics-scientist.md |

## Version History

### v1.1 (Current)
- ✅ Added bio-logic skill integration
- ✅ Updated all workflows with reasoning steps
- ✅ Added 3 new bio-logic examples
- ✅ Created comprehensive documentation (6 files)
- ✅ +28% documentation growth
- ✅ 20+ bio-logic keyword triggers

### v1.0
- Initial release with 16 bio-* skills
- Basic workflow documentation

## Support

- **Modify agent behavior**: Edit `omics-scientist.md`
- **Add workflows**: Update `EXAMPLES.md`
- **Quick reference**: Update `QUICK_REFERENCE.md`
- **Report issues**: GitHub issues

---

**Last Updated**: 2026-02-01
**Total Documentation**: 2,628 lines across 6 files
**Agent Status**: Production-ready with comprehensive bio-logic integration
