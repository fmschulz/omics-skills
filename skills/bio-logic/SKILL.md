---
name: bio-logic
description: Assess a scientific claim, study design, or interpretation of project results against its evidence, and keep a hypothesis register. Use when testing causal reasoning, finding bias, weighing alternative explanations, or revising hypotheses.
---

# Bio-Logic: Scientific Reasoning Evaluation

Use structured frameworks to evaluate scientific claims, methodology, and evidence strength.

## Instructions

1. Identify the task: claim assessment, study design review, project interpretation, or hypothesis revision. Review of a whole manuscript belongs to `nelli-paper-review`.
2. Select the study-type profile before applying a checklist. Do not grade a computational benchmark, phylogenetic analysis, or evolutionary inference as if it were an intervention trial.
3. For interpretation of project results, run the Project Hypothesis Loop below. A small single-question request does not need the register: answer it and name the strongest alternative explanation.
4. Structure output using the formats below.

### Study-Type Profiles

| Profile | Main evidence checks | Rating language |
|---|---|---|
| Intervention | allocation, controls, adherence, attrition, estimand, harms | GRADE when the review question and evidence synthesis support it |
| Observational or quasi-experimental | identification assumptions, temporality, confounding, negative controls, sensitivity analyses | risk-of-bias plus causal-confidence statement |
| Computational or machine learning | data provenance, leakage, splits, baselines, calibration, external validation, reproducibility | computational evidence confidence |
| Evolutionary or comparative genomics | orthology, taxon/reference sampling, model fit, support, contamination, topology sensitivity | phylogenetic/comparative evidence confidence |
| Descriptive or exploratory omics | sampling, measurement, multiple testing, effect sizes, replication, alternative explanations | descriptive confidence; avoid causal labels |

### Project Hypothesis Loop

Use this loop when interpreting the results of an omics project or exploratory analysis, or when a result is unexpected. Keep the register until the project is no longer exploratory.

1. **Initialize**: create at least 5 working hypotheses. Include biological mechanisms, technical artifacts, null explanations, sampling/batch effects, and annotation/database artifacts where relevant.
2. **Build an analysis playbook**: search the literature (`polars-dovmed`) for the inferred organism, virus group, data type, or closest lineage. Summarize typical analyses, comparison baselines, markers/features, plots, and outlier criteria used by scientists in that literature.
3. **Reflect**: for every major intermediate result or QC gate, state the observation, QC status, strongest interpretation, remaining alternatives, and what evidence would separate them.
4. **Contextualize**: compare findings against the playbook and search again for central or unexpected findings with broad synonym-aware queries, and cite DOI/PMCID when available.
5. **Revise**: update each hypothesis as supported, weakened, ruled out, or unresolved. Keep ruled-out hypotheses visible with the evidence that changed their status.
6. **Replace**: if fewer than 5 active hypotheses remain during exploratory work, add plausible replacements or explicitly state why no additional plausible alternatives exist.

### Critique Checklist

Use the sections that fit the study-type profile. Skip items that do not apply to it.

```
## Methodology
- [ ] Design fits the claim type (descriptive, associational, causal)
- [ ] Sampling depth or sample size supports the claim
- [ ] Confounders identified and controlled
- [ ] Measurements validated and reliable

## Statistics
- [ ] Tests appropriate for data type
- [ ] Assumptions checked
- [ ] Multiple comparisons corrected
- [ ] Effect sizes + CIs reported (not just p-values)
- [ ] Missing data handled appropriately

## Interpretation
- [ ] Conclusions match evidence strength
- [ ] Limitations acknowledged
- [ ] Causal claims require an identified causal design: randomized evidence or
      a justified quasi-experimental/natural-experiment strategy with its
      assumptions and sensitivity checks
- [ ] No cherry-picking or overgeneralization

## Red Flags
- [ ] P-values clustered just below .05
- [ ] Outcomes differ from registration
- [ ] Correlation presented as causation
- [ ] Subgroups analyzed without preregistration
```

### Claim Assessment

Identify the claim type (causal, associational, descriptive), match the evidence to it, check the logical link from data to conclusion, and make the confidence match the evidence strength.

**Claim strength ladder**:
| Language | Requires |
|----------|----------|
| "Demonstrates" | Strong evidence under a design that identifies the target claim |
| "Suggests" / "Indicates" | Observational with controlled confounds |
| "Associated with" | Observational, no causal claim |
| "May" / "Might" | Preliminary or hypothesis-generating |

### Output Format

```markdown
## Summary
[1-2 sentences: what was studied, main finding]

## Strengths
[Specific methodological strengths]

## Concerns
### Critical (threaten main conclusions)
- [Issue + why it matters]

### Important (affect interpretation)
- [Issue + why it matters]

### Minor (worth noting)
- [Issue]

## Evidence Rating
[Framework for the study profile, rating, justification. GRADE only when it applies.]

## Bottom Line
[What can and cannot be concluded]
```

### Project Reasoning Output Format

```markdown
## Current Result
[Observed intermediate/final result and QC status]

## Hypothesis Register
| Rank | Hypothesis | Status | Evidence For | Evidence Against | Next Discriminating Check |
|------|------------|--------|--------------|------------------|---------------------------|
| 1 | [Hypothesis] | supported/weakened/ruled out/unresolved | [Evidence] | [Evidence] | [Test] |
| 2-5+ | [Hypothesis] | ... | ... | ... | ... |

## Literature Context
- [Paper, DOI/PMCID]: supports/contradicts/narrows [hypothesis] because [reason].

## Analysis Playbook
- [Literature-derived check and why it applies]

## Revision
[What changed since the previous register and why]

## Next Step
[Most informative analysis, control, or experiment]
```

## References

Read the one that matches the question: [evidence strength](references/evidence.md), [biases](references/biases.md), [statistical errors](references/stats.md), [logical fallacies](references/fallacies.md), [study design](references/design.md).

## Input Requirements

- The claim or study summary, with methods and results as available. If methods or statistics are missing, request them before rating evidence.

## Output

- A structured assessment (strengths, concerns, evidence rating) or a hypothesis register, ending with what can and cannot be concluded.

## Quality Gates

- [ ] Claim type matches evidence type, and the evidence framework matches the study type (no intervention-centric GRADE rules for computational or evolutionary work)
- [ ] Each rating names the concrete issues behind it
- [ ] Interpretation of exploratory project results keeps at least 5 active hypotheses, or explains why fewer are plausible
- [ ] Discovery work has a literature-derived analysis playbook before analyses are chosen
- [ ] Intermediate results update hypothesis status before the next workflow step, and central or unexpected findings are checked against the literature before final interpretation

## Related Skills

- `ai-scientist-evaluator`: rubric-scored evaluation of AI scientist outputs
- `nelli-paper-review`: multi-reviewer critique of manuscripts
- `proposal-review`: structured critique of funding proposals
- `polars-dovmed`: literature search
