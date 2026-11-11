---
name: bio-logic
description: Assess a scientific claim, study design, or interpretation of project results against its evidence, and keep a hypothesis register. Use when testing causal reasoning, finding bias, weighing alternative explanations, or revising hypotheses.
---

# Bio-Logic: Scientific Reasoning Evaluation

Use structured frameworks to evaluate scientific claims, methodology, and evidence strength. Review of a whole manuscript belongs to `nelli-paper-review`.

## Instructions

1. Identify the task: claim assessment, study design review, project interpretation, or hypothesis revision.
2. Select the study-type profile before applying a checklist. Do not grade a computational benchmark, phylogenetic analysis, or evolutionary inference as if it were an intervention trial.
3. For interpretation of project results, keep the hypothesis register below. A small single-question request does not need the register: answer it and name the strongest alternative explanation.

### Study-Type Profiles

| Profile | Main evidence checks | Rating language |
|---|---|---|
| Intervention | allocation, controls, adherence, attrition, estimand, harms | GRADE when the review question and evidence synthesis support it |
| Observational or quasi-experimental | identification assumptions, temporality, confounding, negative controls, sensitivity analyses | risk-of-bias plus causal-confidence statement |
| Computational or machine learning | data provenance, leakage, splits, baselines, calibration, external validation, reproducibility | computational evidence confidence |
| Evolutionary or comparative genomics | orthology, taxon/reference sampling, model fit, support, contamination, topology sensitivity | phylogenetic/comparative evidence confidence |
| Descriptive or exploratory omics | sampling, measurement, multiple testing, effect sizes, replication, alternative explanations | descriptive confidence; avoid causal labels |

Do not assign a GRADE level to a single phylogeny, computational benchmark, genome comparison, or exploratory omics analysis. Report confidence from domain-relevant validity checks.

### Hypothesis register

Use it when interpreting the results of an omics project or exploratory analysis, or when a result is unexpected. Keep it until the project is no longer exploratory.

1. **Initialize**: create at least 5 working hypotheses. Include biological mechanisms, technical artifacts, null explanations, sampling/batch effects, and annotation/database artifacts where relevant.
2. **Build an analysis playbook**: search the literature (`polars-dovmed`) for the inferred organism, virus group, data type, or closest lineage. Summarize typical analyses, comparison baselines, markers/features, plots, and outlier criteria used in that literature.
3. **Reflect**: for every major intermediate result or QC gate, state the observation, QC status, strongest interpretation, remaining alternatives, and what evidence would separate them.
4. **Contextualize**: compare findings against the playbook and search again for central or unexpected findings with broad synonym-aware queries. Cite DOI/PMCID when available.
5. **Revise**: update each hypothesis as supported, weakened, ruled out, or unresolved. Keep ruled-out hypotheses visible with the evidence that changed their status.
6. **Replace**: if fewer than 5 active hypotheses remain during exploratory work, add plausible replacements or state why no additional plausible alternatives exist.

### Claim, design and interpretation check

- Name the claim type: causal, associational, or descriptive.
- Match the evidence to the claim type, and check the logical link from data to conclusion.
- Methodology: the design fits the claim type; sample size or sampling depth supports it; confounders are identified and controlled; measurements are validated.
- Statistics: tests fit the data type and their assumptions were checked; multiple comparisons are corrected; effect sizes and CIs are reported, not only p-values; missing data are handled.
- Interpretation: conclusions match evidence strength; limitations are acknowledged; no cherry-picking or overgeneralization.
- A causal claim needs randomized evidence or a justified quasi-experimental or natural-experiment strategy with its assumptions and sensitivity checks.
- Red flags: p-values clustered just below .05, outcomes that differ from registration, correlation presented as causation, subgroups analyzed without preregistration.
- Make the wording match the evidence:

| Language | Requires |
|----------|----------|
| "Demonstrates" | Strong evidence under a design that identifies the target claim |
| "Suggests" / "Indicates" | Observational with controlled confounds |
| "Associated with" | Observational, no causal claim |
| "May" / "Might" | Preliminary or hypothesis-generating |

## Input Requirements

- The claim or study summary, with methods and results as available. If methods or statistics are missing, request them before rating evidence.
- For project interpretation: the current result and its QC status, and the previous register if one exists.

## Output

Claim or design assessment:

```markdown
## Summary
[1-2 sentences: what was studied, main finding]
## Strengths
## Concerns
### Critical (threaten main conclusions)
### Important (affect interpretation)
### Minor (worth noting)
## Evidence Rating
[Framework for the study profile, rating, justification. GRADE only when it applies.]
## Bottom Line
[What can and cannot be concluded]
```

Project interpretation:

```markdown
## Current Result
[Observed intermediate/final result and QC status]
## Hypothesis Register
| Rank | Hypothesis | Status | Evidence For | Evidence Against | Next Discriminating Check |
## Literature Context
- [Paper, DOI/PMCID]: supports/contradicts/narrows [hypothesis] because [reason].
## Analysis Playbook
- [Literature-derived check and why it applies]
## Revision
[What changed since the previous register and why]
## Next Step
[Most informative analysis, control, or experiment]
```

## Quality Gates

- [ ] Claim type matches evidence type, and the evidence framework matches the study type (no intervention-centric GRADE rules for computational or evolutionary work)
- [ ] Each rating names the concrete issues behind it
- [ ] Interpretation of exploratory project results keeps at least 5 active hypotheses, or explains why fewer are plausible
- [ ] Discovery work has a literature-derived analysis playbook before analyses are chosen
- [ ] Intermediate results update hypothesis status before the next workflow step, and central or unexpected findings are checked against the literature before final interpretation

## Related Skills

- `ai-scientist-evaluator` (separate install): rubric-scored evaluation of AI scientist outputs
- `nelli-paper-review`: multi-reviewer critique of manuscripts
- `proposal-review` (separate install): structured critique of funding proposals
- `polars-dovmed`: literature search
