# Workflow

Use this workflow for both Codex and Claude Code runs. If subagents are unavailable, execute the same stages sequentially in one session.

## 1. Build the artifact bundle

Collect only the inputs that are actually authoritative for the paper:

- manuscript brief or explicit user request
- venue instructions or formatting rules
- prior draft, notes, or baseline manuscript
- source methods artifacts such as code, protocols, notebooks, or logs
- structured result summaries, tables, and figure captions
- bibliography files, DOI lists, or trusted reference notes

Record what is missing before writing. Missing evidence is a constraint, not an invitation to guess.

Treat structured summaries as authoritative when they exist:

- JSON, CSV, TSV, or TeX tables beat memory or paraphrased notes
- copy numbers from structured artifacts, not from prior prose
- if a value is missing, leave it missing and say so

## 2. Choose the runtime pattern

Use the same role contracts in both environments:

- Codex: spawn subagents when that helps isolate context; otherwise run explicit sequential role passes.
- Claude Code: use worker agents when available; otherwise run explicit sequential role passes.

The workflow must still be auditable even when executed in a single session.

## 3. Plan before prose

The planner agent should produce:

- manuscript mode
- artifact inventory
- missing artifacts
- section order
- key risks to factual support

The planner should not draft the paper beyond a short execution plan.

## 4. Draft in a stable order

Use this sequence because it reduces drift:

1. Methods from source artifacts only
2. section-level outline
3. full manuscript prose
4. related-work tightening after the main draft exists
5. citation audit

If the task is only a section rewrite, still do a short plan first and keep the rewritten section consistent with the rest of the manuscript.

## 5. Run an explicit review and revision loop

After the first full draft exists, run this cycle:

1. Reviewer pass
   - assess logic, evidence alignment, results-to-text consistency, citation safety, paragraph quality, and figure/table usefulness and caption clarity
   - separate major issues from minor issues
   - state whether another revision pass is required
2. Reviser pass
   - apply only fixes that are supported by the artifact bundle
   - answer each major revision priority directly
   - keep a short note of what was changed, deferred, or blocked by missing evidence
3. Reviewer pass again
   - confirm whether the revision improved the draft
   - either clear the draft, request another focused pass, or mark issues as blocked by missing evidence

Prefer short, focused loops over one large rewrite. If the same major issue repeats twice without new evidence, stop rewriting around it and report it as unresolved.

## 6. Stop conditions

Stop the loop when one of these is true:

- no fixable major issues remain
- the reviewer recommends keeping the current draft or using it with only minor edits
- the remaining problems require missing data, methods details, or citations that are not available
- another loop would be cosmetic churn rather than substantive improvement

Three substantive loops are usually enough, but continue if the draft is still improving and the evidence base supports another pass.

## 7. Adjust length gradually

Trim or expand after the major issues are under control. Avoid one-shot compression passes that destabilize technical details, citations, or numerical statements.

## 8. Finalize conservatively

The final response should include:

- the manuscript or revised section
- unresolved evidence gaps
- which artifacts were treated as authoritative
- what was reviewed or validated
- whether the loop stopped because quality gates passed or because evidence ran out
