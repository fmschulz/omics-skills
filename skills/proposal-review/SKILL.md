---
name: proposal-review
description: Review an AI/ML, computational-biology, or bioscience research proposal for a funding decision. Use when scoring a grant or funding application against sponsor criteria, feasibility, budget, and risk.
---

# Proposal Review

Produce a decision-ready review of an AI/ML, computational biology, or bioscience proposal. Be fair, skeptical, and specific, and name missing information.

## Instructions

1. Read the proposal and identify the decision context if provided: sponsor goals, rubric, budget cap, timeline, and risk tolerance.
2. If critical information is missing, do not invent it. Flag the gap and turn it into a prioritized question for the PI.
3. A short "is this fundable" question gets a short answer: the scorecard only. For a full review, use these sections:
   - Executive summary
   - Heilmeier catechism
   - Technical merit
   - Data, compute, and experimental resources
   - Risk register
   - Team and execution capability
   - Ethics, safety, and compliance
   - Budget and schedule realism
   - Scorecard
   - Decision and funding conditions
   - Questions for the PI
4. Tailor the technical review to the proposal type:
   - AI/ML: baselines, ablations, leakage prevention, calibration, external validation, compute realism
   - Bio or wet lab: controls, replicates, statistical plan, assay feasibility, translational path
5. Include at least six risks covering technical, data or experimental, budget or timeline, and adoption or regulatory concerns when relevant.
6. If the sponsor supplies a rubric, use its categories, weights, and decision vocabulary. Otherwise use the default 1-to-5 scorecard below; do not mix sponsor and default weights.
7. Default weights: strategic fit and novelty 15%, technical rigor 25%, feasibility and resources 20%, team and execution 15%, risk, ethics, and compliance 15%, budget and schedule 10%.
8. Map the default weighted mean to `Strong Accept` (>=4.5), `Accept` (>=3.7), `Borderline` (>=2.8), or `Reject` (<2.8). A documented fatal flaw may override the numeric band.
9. Keep the review concrete and action-oriented. Reference proposal details when available and name fatal flaws plainly.
10. For a machine-checked scorecard, write the scores to JSON and run the helper:

    ```bash
    uv run --script "$HOME/.agents/skills/proposal-review/scripts/score_proposal.py" scorecard.json
    ```

    With the default rubric, `scores` must contain exactly these 1-to-5 keys: `strategic_fit_and_novelty`, `technical_rigor`, `feasibility_and_resources`, `team_and_execution`, `risk_ethics_and_compliance`, `budget_and_schedule`. For a sponsor rubric, add `"rubric": {"weights": {...}, "recommendations": [{"minimum": 4, "label": "Fund"}, ...]}`; weights must total 100 and the score keys must match them. Set `"fatal_flaw": true` (and optionally `fatal_flaw_recommendation`) to override the band. The helper rejects weights that do not total 100, category mismatches, and scores outside 1 to 5, and never mixes default bands into a sponsor rubric.

## Input Requirements

- Proposal text. Optional: sponsor context, rubric, budget cap, timeline.

## Output

- A structured review with a weighted scorecard, an explicit funding recommendation with conditions, and the PI questions that could change the decision.

## Quality Gates

- [ ] Missing information is flagged, not invented
- [ ] At least six concrete risks, each with a mitigation
- [ ] Scorecard weights total 100%, every rubric category is scored, and the recommendation follows the selected rubric's bands

## Related Skills

- `nelli-paper-review`: equivalent review for manuscripts
- `academic-writing` with `stop-slop`: draft or revise the proposal narrative
- `bio-logic`: assess methodology and evidence rigor
