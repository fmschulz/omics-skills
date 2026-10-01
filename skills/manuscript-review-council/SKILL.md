---
name: manuscript-review-council
description: Journal-style manuscript peer review with specialist reviewer reports and an editor decision. Use when judging publication readiness or whether a revision or author response resolves scientific objections.
---

# Manuscript Review Council

Run a journal-style review council instead of a single blended opinion. The skill is self-contained and works in Codex and Claude Code.

The council is defined in local files:
- role roster and activation rules: [references/reviewer-roles.md](references/reviewer-roles.md)
- stage flow and artifact bundle: [references/council-workflow.md](references/council-workflow.md)
- per-reviewer brief: [templates/reviewer-brief.md](templates/reviewer-brief.md)
- editor synthesis: [templates/editor-meta-review.md](templates/editor-meta-review.md)
- bundle contract: [schemas/review-bundle.schema.json](schemas/review-bundle.schema.json)

## Instructions

1. Confirm the review context: manuscript or revision stage, target venue if known, decision scale, and whether the user wants a full review, triage, version comparison, or rebuttal assessment. Requests to rewrite manuscript prose or draft a rebuttal go to `/scientific-writing`; start a council only when the user also wants scientific critique or a resolution assessment.
2. Gather the review packet: manuscript text (convert a PDF or DOCX to sectioned text first, for example with `/pdf-to-md`), title, abstract, main claims, methods snapshot, figure and table list, user priorities, and prior reviews or author response for a revision. Every reviewer gets the same packet; keep section boundaries, figure references, and the claims under test.
3. Read the council files above before delegating.
4. Delegate with the platform's native primitive (Codex sub-agents, Claude Code Task agents). If delegation is unavailable, run the same roles in sequence and keep their outputs separate.
5. Launch the three default reviewers in parallel:
   - `domain`: novelty, significance, positioning against prior work, and overclaiming
   - `methods-statistics`: design, controls, benchmarks, sample size, figure interpretation, and analysis validity
   - `skeptic`: weakest links, alternative explanations, unsupported causal claims, results explained by unchecked causes, and missing controls
6. Add support reviewers only when the manuscript calls for them:
   - `reproducibility`: computational papers, code or data availability, workflow clarity, and parameter transparency
   - `ethics-compliance`: human subjects, animal work, privacy, conflicts, dual use, or citation bias
   - `translational`: clinical, ecological, or deployment claims that need a reality check
7. Every reviewer returns the contract in `templates/reviewer-brief.md`: summary, strengths, major concerns, minor concerns, must-fix analyses, confidence (0 to 1), and a provisional recommendation (`accept`, `minor_revision`, `major_revision`, or `reject`), each concern anchored to a section, figure, table, or explicitly missing information. Reviewers do not invent citations, datasets, reviewer expectations, or experiments the manuscript does not motivate.
8. Run a cross-review pass: compare disagreements, merge duplicate concerns, find the few issues that drive the decision, and separate fatal flaws from fixable items.
9. Save the artifact bundle even when the user asked only for prose, under `reviews/<manuscript-slug>/<YYYYMMDDTHHMMSSZ>/` as described in `references/council-workflow.md`, and validate the bundle index:

   ```bash
   uv run --script "$HOME/.agents/skills/manuscript-review-council/scripts/validate_review_bundle.py" bundle.json
   ```

   The validator rejects non-deterministic paths, duplicate roles or issue IDs, an issue whose `source_roles` names a reviewer absent from `reviewer_reports`, and a council without all three default reviewers unless `reduced_council_reason` explains why.
10. Write the editor meta-review with `templates/editor-meta-review.md`: recommendation, rationale across novelty, rigor, evidence strength, clarity, reproducibility, and significance, ranked major and minor revisions, questions for the authors, and a short decision letter.
11. For outside validation, run targeted spot-checks, not a broad literature review: `/polars-dovmed` for claim-specific literature and `/bio-logic` for evidence strength and causal claims. Never fabricate supporting papers.
12. For polished review prose or a cleaned-up decision letter, use `/scientific-writing` after the council has fixed the factual review content.
13. Preserve provenance: keep per-reviewer notes separate from the editor synthesis, point to sections, figures, or tables, and mark inference apart from what the manuscript states.

## Quick Reference

| Task | Action |
|------|--------|
| Full manuscript review | Run the 3-reviewer council plus editor synthesis |
| Computational manuscript | Add a reproducibility reviewer |
| Human, animal, or clinical manuscript | Add an ethics or compliance reviewer |
| Revision assessment | Compare prior critiques to the new draft and label each issue resolved, partial, or unresolved |
| Fast triage | Use `domain` plus `skeptic`, set `reduced_council_reason`, then write a short editor recommendation |
| Rebuttal check | Judge whether the author response closes the decision-driving issues |

## Input Requirements

- Manuscript text or an accessible PDF/DOCX
- Optional journal rubric, scorecard, or decision scale
- Optional prior reviews, decision letter, rebuttal, or previous manuscript version
- Optional focus areas such as novelty, methods, statistics, reproducibility, or clarity

## Output

- Role-separated reviewer notes
- A short disagreement or adjudication log
- An editor meta-review with a clear recommendation
- A prioritized major and minor revision list
- Specific questions for the authors
- Optional decision letter, rebuttal assessment, or version-delta summary
- A validated review bundle under `reviews/<manuscript-slug>/<run-id>/`

## Quality Gates

- [ ] At least three distinct reviewer roles are used, or the reduced scope is justified explicitly
- [ ] Reviewer outputs stay role-separated until synthesis
- [ ] Major concerns are grounded in manuscript text or explicit missing information
- [ ] Reviewer disagreements are adjudicated explicitly instead of silently averaged
- [ ] The final recommendation matches the ranked issues
- [ ] No citations, datasets, experiments, or venue rules are invented
- [ ] Reproducibility and ethics checks are added when the manuscript warrants them
- [ ] Artifacts use `reviews/<manuscript-slug>/<UTC-run-id>/...` and the bundle passes `validate_review_bundle.py`
- [ ] Prose editing and rebuttal drafting stay with `/scientific-writing`

## Examples

### Example 1: Full journal-style review

```text
Review this microbiome manuscript with a multi-agent council. Use domain,
methods/statistics, skeptic, and reproducibility reviewers. End with an editor
meta-review, a recommendation, and ranked major/minor revisions.
```

### Example 2: Revision comparison

```text
Compare this revised manuscript against the prior decision letter. Tell me
which major issues are resolved, partially resolved, or still open, then write
an editor recommendation.
```

### Example 3: Fast triage

```text
Give me a fast desk-review style assessment of this preprint. Use only a domain
reviewer and a skeptic, record the reduced council on the bundle, then summarize
whether it is promising, immature, or fatally flawed.
```

## Troubleshooting

**Issue**: The manuscript is too long for every reviewer to read in full.
**Solution**: Build a shared review packet first, then route only the relevant sections, claims, and figures to each reviewer while keeping a common abstract and methods snapshot.

**Issue**: Reviewers disagree sharply.
**Solution**: Make the disagreement explicit, identify the evidence each reviewer is using, and let the editor resolve the conflict instead of averaging positions.

**Issue**: No journal rubric or venue is provided.
**Solution**: State the default criteria being applied: novelty, rigor, evidence strength, clarity, reproducibility, and significance.

**Issue**: Only one agent can run.
**Solution**: Emulate the council sequentially with role-scoped passes and keep the notes separated until the editor synthesis step.

## Related Skills

- `/scientific-writing`: apply the reviewer feedback to the manuscript
- `/bio-logic`: deeper reasoning about evidence strength
- `/ai-scientist-evaluator`: equivalent review for AI scientist outputs
