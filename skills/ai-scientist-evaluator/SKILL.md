---
name: ai-scientist-evaluator
description: Score finished AI-generated biology or bioinformatics work against its task and required artifacts. Use when auditing or ranking AI scientist submissions for task completion, scientific validity, and reproducibility.
---

# AI Scientist Evaluator

Act as a skeptical reviewer panel, not a research generator. Evaluate completed
outputs, not plans.

## Instructions

1. Confirm the request is evaluative. Use this skill to audit or compare
   existing outputs, not to perform the original research task.
2. Restate the exact task in one or two sentences so the review stays anchored
   to the real objective and required deliverables.
3. Inventory the submitted artifacts and note what is missing. Prefer primary
   artifacts over summaries:
   - notebooks, code, scripts, and workflow files
   - environment files, package versions, and runtime logs
   - figures, tables, and manuscript drafts
   - data provenance, accession lists, database versions, and citations
   - benchmark results, hardware notes, and task constraints
4. Choose the closest task profile from
   [`references/task_profiles.md`](references/task_profiles.md) and load the
   matching weights from
   [`assets/default_weight_profiles.yaml`](assets/default_weight_profiles.yaml).
   Use the primary scientific profile first for composite tasks, then add
   manuscript comments as a secondary layer. Worked profile choices for real
   benchmark tasks: [`examples/bio_task_mappings.md`](examples/bio_task_mappings.md).
5. Review with a four-person panel and synthesize a consensus:
   - scientific validity reviewer
   - computational and reproducibility reviewer
   - domain biology reviewer
   - writing and editorial reviewer, who scores `prose_quality` against these
     rules: each supported claim stated once, plainly; each limitation stated
     once, where it applies; no stacked qualifiers on a comparative claim that
     the numbers support; no explanation of a result that was not checked;
     legends describe what is shown and do not restate results; no script
     names, internal flags or runtime bookkeeping in Results. For rewriting
     prose, point the user to `academic-writing` with `stop-slop`.
6. Apply hard gates before generous scoring. A submission is not
   publication-ready if required deliverables are missing, claims are not
   supported by visible outputs, provenance is untraceable, the core method is
   not rerunnable, or the submission solves an easier adjacent problem.
7. Interrogate the submission with the relevant sections of
   [`references/question_bank.md`](references/question_bank.md). Always include
   the universal questions, then add the profile-specific and multi-submission
   questions when needed.
8. Scan for integrity, rigor, and validity problems using
   [`references/red_flags.md`](references/red_flags.md). Penalize missing
   evidence, task drift, unsupported biological claims, fabricated identifiers,
   and unverifiable citations more than polished narrative.
9. Score each category on the anchored 0 to 5 scale in
   [`references/score_scale.md`](references/score_scale.md). Use
   [`references/category_definitions.md`](references/category_definitions.md) if
   category meaning is unclear. A score of 5 earns the full category weight.
10. Convert the category scores to a weighted total out of 100. Do not trust
    submitted `weight` or `weighted_points` values. The bundled aggregator
    validates the review against `evaluation_schema.json`, loads the selected
    weight profile, and recomputes each weighted value. It accepts
    `overall.total_score_100` only as a downward penalty. It ignores any score
    above the recomputed total. Apply penalties sparingly and explain them when
    category scores do not already capture the issue.
11. For multiple submissions, score each one independently before ranking. Use
    tie-breaks in this order:
    - fewer integrity or reproducibility problems
    - better satisfaction of the task's main objective
    - stronger validation or benchmarking
    - clearer limitation handling
    - better writing only after science and evidence are settled
12. Produce a concise consensus verdict with actionable revisions. Ground the
    review in concrete evidence from files, notebook cells, figure numbers,
    accessions, parameters, and versioned tools whenever possible.
13. When a structured artifact is useful, start from
    [`assets/evaluation_template.json`](assets/evaluation_template.json) and
    validate the shape against
    [`assets/evaluation_schema.json`](assets/evaluation_schema.json). Use
    [`assets/report_template.md`](assets/report_template.md) for markdown
    reports. For completed JSON reviews, aggregate rankings with
    `uv run --script "$HOME/.agents/skills/ai-scientist-evaluator/scripts/aggregate_reviews.py" review1.json review2.json --out_md leaderboard.md`.

## Input Requirements

- The original task statement, success criteria and constraints
- One or more completed submissions, with the artifacts listed in step 3
- Submission names or IDs when comparing several

If key artifacts are missing, continue and mark the evidence gap explicitly.

## Output

- One submission: verdict paragraph, gate-check table, weighted score table, panel comments by category, answers to the key questions, required revisions, recommendation label.
- Several submissions: consensus ranking table, per-submission totals and category scores, pairwise notes, best-in-class awards (science, reproducibility, writing, engineering), a winner with justification, and a merge recommendation when combining strengths would beat any one entry.

Use these recommendation labels:

- `90-100`: Outstanding / near publication-ready
- `75-89`: Strong but needs minor to moderate revision
- `60-74`: Promising but major revision needed
- `40-59`: Weak / unreliable in important respects
- `<40`: Not trustworthy for scientific use

## Quality Gates

- [ ] The review is anchored to the exact task, not an easier adjacent one
- [ ] Artifact inventory, missing evidence, task profile and hard gates are stated
- [ ] Scores follow the anchored 0 to 5 scale and sum to a weighted total out of 100
- [ ] Rankings come only after independent scoring
- [ ] Recommendations distinguish absent, flawed, weakly validated and well-supported work

## Related Skills

- `bio-logic`: general scientific reasoning beyond AI evaluation
- `nelli-paper-review`: equivalent review for human-authored manuscripts
- `academic-writing` with `stop-slop`: draft the evaluation writeup
