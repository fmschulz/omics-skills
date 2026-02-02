# Bio-Logic Skill Integration Summary

## Overview

The `bio-logic` skill has been comprehensively integrated into the omics-scientist agent as the **foundational layer for scientific reasoning**. This skill is now positioned as the first and most critical tool for hypothesis formation, experimental design, method selection, and result interpretation.

## Integration Locations

### 1. Core Principles (omics-scientist.md)
Added as **Principle #1**: "Scientific Reasoning First"
- Elevated reasoning to the top priority
- Ensures agent thinks critically before executing workflows

### 2. Mandatory Skill Usage Section
New dedicated section: **"Scientific Reasoning & Hypothesis Formation (Universal)"**

**Position**: Right after project initialization, emphasizing its universal applicability

**Key directive**: "CRITICAL: Use bio-logic for all scientific reasoning tasks"

**Comprehensive trigger scenarios:**
- Study Design: sequencing strategy, replicates, controls
- Method Selection: algorithm choice, parameter justification
- Result Interpretation: unexpected findings, pattern explanation
- Hypothesis Formation: mechanistic reasoning, predictive models
- Scientific Critique: evaluation of conclusions, confounds
- Causal Reasoning: causality vs correlation, evolutionary pressures
- Data Integration: multi-omic synthesis

### 3. Workflow Decision Tree
Added bio-logic as **first decision point**:
```
START
  ├─ Scientific Question? → /bio-logic
  ├─ Need Reasoning/Interpretation? → /bio-logic (at ANY point)
```

### 4. Keyword Mapping
**Extensive keyword triggers** (most comprehensive in the agent):
- why, how, explain, interpret
- hypothesis, design experiment
- reasoning, mechanism
- because, therefore, conclude, suggest, imply
- causal, evidence, justify, rationale
- alternative explanation, confound

**Positioned FIRST** in the keyword mapping table to ensure priority

### 5. Communication Style
Updated to **mandate bio-logic usage**:
- "Use /bio-logic to explain biological rationale"
- "Use /bio-logic to justify parameter choices"
- "Use /bio-logic to interpret results"
- "Use /bio-logic when questions involve 'why', 'how', or 'what does this mean'"

### 6. Example Interactions
Updated both examples to include bio-logic:

**Example 1**: Bacterial genome workflow
- Step 0: bio-logic (justify assembly strategy)
- Step 6: bio-logic (interpret placement, evolutionary insights)

**Example 2**: MAG recovery workflow
- Step 0: bio-logic (reason about binning strategy)
- Step 5: bio-logic (interpret ecology, metabolic roles)

### 7. New Bio-Logic Integration Examples
Added **4 detailed examples** showing bio-logic usage:

1. **Method Selection** - Reasoning through algorithm/approach trade-offs
2. **Result Interpretation** - Evaluating alternative hypotheses systematically
3. **Hypothesis Formation** - Deriving testable predictions from data
4. **Experimental Design** - Designing rigorous experiments with proper controls

### 8. Related Skills
Marked skills that **complement bio-logic**:
- `/scientific-writing` - "use with /bio-logic for biological interpretation"
- `/literature-review` - "use with /bio-logic to synthesize findings"
- `/statistical-analysis` - "use with /bio-logic for interpretation"
- `/scientific-critical-thinking` - "complements /bio-logic"
- `/peer-review` - "use with /bio-logic for critique"

### 9. Remember Section
Added as **first critical rule**:
- "Use /bio-logic to reason about the scientific problem and approach"
- "Use /bio-logic to interpret results biologically and formulate new hypotheses"
- "ALWAYS use /bio-logic for any 'why', 'how', 'explain', or interpretation questions"
- "Use /bio-logic BEFORE workflows to justify approach"
- "Use /bio-logic DURING workflows when unexpected results occur"
- "Use /bio-logic AFTER workflows to derive biological insights"

## Documentation Updates

### README.md
- Added bio-logic to skills table (first row, marked as bold)
- Updated workflow examples to include bio-logic steps
- Enhanced troubleshooting to mention interpretation keywords
- Updated tips to emphasize asking "why" and "how" questions

### EXAMPLES.md
- Added bio-logic as Step 0 in bacterial genome workflow
- Added bio-logic as Step 0 in MAG recovery workflow
- Added interpretation steps after phylogeny/annotation
- Created **3 new complete examples** (Examples 9-11):
  - Example 9: Interpreting unexpected results (E. coli with nif genes)
  - Example 10: Experimental design (plastic degradation proof)
  - Example 11: Method selection (short vs long reads)

**Total examples growth**: 545 → 746 lines (+37%)

### QUICK_REFERENCE.md
- Modified one-line decision guide to include bio-logic
- Added bio-logic as first row in skill selection matrix (bold, highlighted)
- Added bio-logic as first keyword trigger (bold, extensive keywords)
- Updated all workflow examples to include bio-logic steps
- Expanded decision tree with bio-logic conditionals
- Added bio-logic as **Remember Rule #1**
- Created new section: **"Bio-Logic Quick Examples"** with 12 scenarios

**Total growth**: 297 → 352 lines (+19%)

## File Growth Summary

| File | Before | After | Growth |
|------|--------|-------|--------|
| omics-scientist.md | 294 | 411 | +40% |
| EXAMPLES.md | 545 | 746 | +37% |
| QUICK_REFERENCE.md | 297 | 352 | +19% |
| README.md | 221 | 228 | +3% |
| **Total** | **1357** | **1737** | **+28%** |

## Key Design Principles

### 1. Universal Applicability
Bio-logic is **not optional** for reasoning tasks - it's mandatory and universal across all workflows.

### 2. Three-Phase Integration
- **BEFORE**: Justify approach, design experiments
- **DURING**: Interpret unexpected findings, guide decisions
- **AFTER**: Derive biological insights, formulate hypotheses

### 3. Forced Skill Usage
Multiple enforcement mechanisms:
- Positioned as Principle #1
- Marked as "CRITICAL" in multiple sections
- Extensive keyword mapping (20+ triggers)
- First decision point in workflow tree
- Mandatory in communication style
- Examples demonstrate consistent usage

### 4. Scientific Rigor
Bio-logic emphasizes:
- Hypothesis-driven approaches
- Evidence evaluation
- Alternative explanations
- Confound identification
- Causal reasoning (not just correlation)
- Mechanistic understanding

### 5. Integration with Bioinformatics
Bio-logic **complements** (not replaces) technical skills:
- Use bio-logic to **decide** which technical skill to use
- Use technical skills to **generate** data
- Use bio-logic to **interpret** results
- Iterate between reasoning and execution

## Usage Patterns

### Pattern 1: Method Selection
```
User question → bio-logic (evaluate options) → technical skill (execute choice)
```

### Pattern 2: Standard Workflow
```
bio-logic (plan) → technical skills (execute) → bio-logic (interpret)
```

### Pattern 3: Troubleshooting
```
Unexpected result → bio-logic (generate hypotheses) → technical skills (test) → bio-logic (evaluate)
```

### Pattern 4: Experimental Design
```
Research question → bio-logic (design study) → technical skills (analyze data) → bio-logic (conclusions)
```

## Example Trigger Phrases

Users saying these phrases will automatically trigger bio-logic:

**Questions:**
- "Why am I seeing...?"
- "How can I explain...?"
- "What does this mean...?"
- "Should I use X or Y?"

**Reasoning:**
- "Explain the mechanism..."
- "What's the biological significance...?"
- "Design an experiment to..."
- "Formulate a hypothesis..."

**Interpretation:**
- "What do these results suggest?"
- "Is this contamination or real?"
- "Why would this organism have...?"
- "What evolutionary pressures...?"

**Critique:**
- "Are these conclusions supported?"
- "What alternative explanations?"
- "What confounds exist?"
- "Evaluate this hypothesis..."

## Integration with Workflow Examples

Every major workflow now includes bio-logic:

1. **Bacterial Isolate**: Before (strategy) + After (interpretation)
2. **MAG Recovery**: Before (binning design) + After (ecological insights)
3. **Viral Metagenomics**: Before (strategy) + After (diversity interpretation)
4. **Comparative Genomics**: Before (pangenome approach) + After (evolution)
5. **Structure Prediction**: Before (method selection) + After (function inference)

## Scientific Reasoning Capabilities

Bio-logic enables the agent to:

✅ **Formulate testable hypotheses** from observations
✅ **Design rigorous experiments** with appropriate controls
✅ **Evaluate evidence** systematically and objectively
✅ **Identify confounds** and alternative explanations
✅ **Reason causally** (not just correlations)
✅ **Integrate multi-omics data** coherently
✅ **Critique methods** and conclusions
✅ **Generate mechanistic models** of biological processes
✅ **Make data-driven predictions**
✅ **Synthesize literature** into coherent frameworks

## Success Metrics

The integration is successful if the agent:
1. ✅ Uses bio-logic for ALL "why", "how", "explain" questions
2. ✅ Reasons about approach BEFORE executing technical workflows
3. ✅ Interprets results biologically AFTER technical analysis
4. ✅ Generates hypotheses from unexpected findings
5. ✅ Designs experiments with proper controls
6. ✅ Evaluates alternative explanations systematically
7. ✅ Identifies when reasoning is needed (automatic detection)
8. ✅ Integrates reasoning seamlessly with bioinformatics tools

## Comparison: Before vs After

### Before Bio-Logic Integration
```
User: "I found E. coli genes in my archaeal MAG. What do I do?"

Agent:
1. Run CheckM to check contamination
2. Re-run binning with stricter parameters
3. Check taxonomy with GTDB-Tk

[Technical response only]
```

### After Bio-Logic Integration
```
User: "I found E. coli genes in my archaeal MAG. What do I do?"

Agent:
→ /bio-logic

This requires scientific reasoning. Let me evaluate hypotheses:

**Hypothesis 1: Contamination**
- Evidence: CheckM contamination score, GC content anomaly
- Likelihood: High if bin has mixed tetranucleotide signals

**Hypothesis 2: Horizontal Gene Transfer**
- Evidence: Gene mobility elements, phylogenetic incongruence
- Likelihood: Moderate - HGT common in Archaea

**Hypothesis 3: Misclassification**
- Evidence: Re-check 16S, ANI to references
- Likelihood: Possible if classification based on few markers

**Hypothesis 4: Annotation Error**
- Evidence: E-values, alignment quality
- Likelihood: Low if using stringent cutoffs

Recommended investigation order:
1. /bio-binning-qc (check contamination metrics)
2. /bio-phylogenomics (gene phylogeny)
3. /bio-annotation-taxonomy (re-annotate with strict parameters)
4. /bio-logic (synthesize evidence, rank hypotheses)

[Reasoned, hypothesis-driven response]
```

## Conclusion

The bio-logic skill is now **deeply embedded** as the cognitive foundation of the omics-scientist agent. It ensures that the agent:
- **Thinks** before executing
- **Reasons** about methods
- **Interprets** results biologically
- **Generates** hypotheses
- **Designs** experiments rigorously
- **Evaluates** evidence critically

This transforms the agent from a technical tool executor into a **scientific reasoning partner**.

