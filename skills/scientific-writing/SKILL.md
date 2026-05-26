---
name: scientific-writing
description: Draft, review, and iteratively revise scientific manuscripts with a provider-agnostic multi-agent workflow for Codex and Claude Code. Use for new manuscripts, section rewrites, rebuttals, response letters, manuscript QA, or sentence-level writing reviews when claims must stay grounded in supplied artifacts.
---

# Scientific Writing

Use this as the single scientific-writing skill for both Codex and Claude Code. It covers two related modes of work:

- **Drafting and revision** — produce a manuscript or rebuttal from authoritative artifacts and iterate it through review-revise loops.
- **Sentence-level writing review** — audit existing prose for clarity, voice, sentence architecture, terminology consistency, and numerical integrity, without changing the underlying science.

The two modes share the same role set and the same hard rules. Pick the entry point that matches the request; the workflow then routes accordingly.

## State Assumptions First

Before drafting or reviewing, state:

- manuscript mode: new draft, revision, rebuttal, review response, section rewrite, or writing review
- review mode when this is a writing review: `full-review`, `section-review`, `targeted`, or `interactive` (see below)
- target venue or formatting target when known
- authoritative artifacts available
- missing artifacts that block specific claims

If a required input is missing, name the gap and keep the prose conservative.

## Review Modes

When the request is a writing review of existing prose, choose one mode:

| Mode | Trigger | Behavior |
|---|---|---|
| `full-review` | "review my manuscript", "writing review" | Run all five prose-quality audits on the whole document and emit a structured report. Default when ambiguous. |
| `section-review` | "review the Introduction", "check the Discussion" | Run all five audits on a single section. |
| `targeted` | "fix passive voice", "strip the clutter" | Run only the requested audit pass(es). |
| `interactive` | "walk me through improving this" | Go paragraph by paragraph: show original, show revision, explain changes, wait for confirmation. |

Both drafting and review work share the same auditable artifact set (plan, draft, citation audit, review notes, revision notes).

## Instructions

1. Inventory the artifact bundle before writing or reviewing. See `references/workflow.md`.
2. Choose a runtime pattern:
   - On Codex, use spawned subagents when available, otherwise run the same roles sequentially.
   - On Claude Code, use worker agents when available, otherwise run the same roles sequentially.
3. Split the run into these core roles:
   - planner
   - methods-writer
   - structure-writer
   - writer
   - citation-auditor
   - reviewer
   - reviser
4. **For drafting work**: produce content in a fixed order — Methods, structure outline, manuscript prose, citation audit.
5. **For writing-review work**: run the prose-quality audits described in `references/writing-quality.md`. Five passes, applied in order: clutter; voice and verbs; sentence architecture; terminology and keywords; numbers and citations. Each finding carries a severity tag (CRITICAL / MAJOR / MINOR) and a concrete revision — never a vague "consider improving" suggestion.
6. Run an explicit `review -> revise -> review` loop until one of these is true:
   - no fixable major issues remain
   - only minor edits remain
   - the remaining issues require missing evidence
   - another loop would only repeat the same findings without material improvement
7. For manuscript figures, review the figure/caption pair as evidence, not decoration:
   - keep the figure title and interpretation in the caption; remove in-plot titles/subtitles from graphics
   - make the caption state the finding, comparison context, sample size or cohort, units, uncertainty, and statistical test when relevant
   - prefer direct labels, panel labels, axis labels, and concise legends over legend-heavy graphics
   - flag 3D, pie charts, dual y-axes, heavy grids, decorative gradients, and overloaded multi-series plots as revision issues
   - recommend a sentence/table when the figure shows only one or two values, small multiples for many series, slopegraphs for before/after contrasts, and sparklines for compact trend context
8. Keep intermediate artifacts auditable: plan, methods draft, outline, manuscript draft, citation audit, review notes, and revision notes.
9. Validate citations before finalizing. Use `/crossref-lookup` when DOI or title checks are needed.
10. Return unresolved evidence gaps explicitly instead of smoothing them over.

## Prose-Quality Audits

When the reviewer pass runs, it applies five sequential audits. The full audit tables, examples, and constraints live in `references/writing-quality.md`. Summary:

1. **Clutter** — strip dead-weight phrases, dead openers, and redundancy.
2. **Voice and verb vitality** — convert obscuring passive constructions to active; resurrect smothered verbs ("provides a description of" → "describes"). Passive is acceptable when the actor is unknown or when Methods house style requires it.
3. **Sentence architecture** — flag buried predicates (>~12 words between subject and verb), use colons/dashes/semicolons for compression, vary sentence length.
4. **Terminology and keywords** — enforce the Banana Rule (don't paraphrase defined terms), audit acronym definitions at every first use (Abstract, body, every legend), reject author-convenience acronyms.
5. **Numbers and citations** — check N, percentages, and significant figures across Abstract, text, tables, and figures; flag "telephone-game" statistics cited only through reviews or textbooks.

Output: every finding includes file/section reference, original text, concrete revision, the audit pass it triggers, and a severity tag.

## Severity Tags

Used by both reviewer and reviser. Reviser addresses CRITICAL and MAJOR first.

- **CRITICAL** — actively misleads the reader (wrong number, term inconsistency implying a different variable, passive voice hiding important accountability).
- **MAJOR** — significantly impairs clarity (buried predicates, heavy nominalization, dense clutter, inconsistent acronym definitions, secondary-source statistics).
- **MINOR** — worth fixing but does not impede understanding.

## Quick Reference

| Task | Action |
|------|--------|
| Plan a writing run | audit artifacts, mode, venue, and blockers before prose |
| Draft a manuscript | follow Methods -> outline -> prose -> citation audit |
| Improve quality | run reviewer and reviser loops until quality gates pass or evidence runs out |
| Validate citations | `/crossref-lookup` |

## Input Requirements

- manuscript request, brief, or target section
- authoritative manuscript artifacts such as prior drafts, notes, protocols, code, logs, or structured results
- bibliography inputs such as `.bib` files, DOI lists, or trusted reference notes
- venue instructions when available

## Output

- manuscript draft or revised section in paragraph prose
- auditable planning, review, and revision notes
- citation audit results when citation work is in scope
- explicit unresolved evidence gaps

## Quality Gates

- [ ] claims stay within the supplied evidence
- [ ] Methods trace to real artifacts rather than inference
- [ ] numbers in prose match structured summaries or tables
- [ ] manuscript figures use captions rather than in-plot titles and captions state the finding, context, units, uncertainty, and test where relevant
- [ ] figure text calls out misleading or low-data-ink displays instead of treating them as neutral style choices
- [ ] citations are validated, inherited from trusted sources, or marked for follow-up
- [ ] reviewer findings are either fixed or carried forward as blocked gaps

## Role Set

- `planner`: audits the artifact bundle and defines the writing order
- `methods-writer`: drafts Methods from source artifacts only
- `structure-writer`: creates the section skeleton and figure/table plan
- `writer`: drafts paragraph prose from the plan and available evidence
- `citation-auditor`: checks citation correctness, placement, and bibliography safety
- `reviewer`: produces a scientific review report with revision priorities
- `reviser`: applies only evidence-backed fixes and carries forward blocked issues explicitly

## Hard Rules

- Do not invent data, experiments, citations, reviewer comments, or bibliography entries.
- Do not transcribe numbers from memory when structured tables, JSON, CSV, or prior manuscripts exist.
- Do not silently mutate `.bib` files; describe or stage citation edits explicitly.
- Final manuscript text should be paragraph prose, not bullet outlines, except for planning artifacts.
- If reviewer feedback would require new evidence, say so directly.
- **Do not alter scientific content during a writing review.** Improve delivery, not substance. Flag a claim that looks wrong rather than rewriting it.
- **Respect disciplinary and journal conventions.** Some fields require passive voice in Methods; some journals have specific style rules. Ask about the target venue when it is not stated.
- **Preserve author voice.** Aim for clarity, not homogeneity. A sentence that is clear and effective despite breaking one of the audit rules should be left alone.
- **Be specific.** Every reviewer finding must include the original text and a concrete revision. "Consider tightening the language" is not an acceptable finding.

## Examples

### Example 1: Section Rewrite With Review Loop

1. inventory the artifact bundle and identify missing evidence
2. draft the requested section in paragraph prose
3. run reviewer and reviser passes until the remaining issues are minor or evidence-blocked
4. return the revised section plus unresolved gaps

### Example 2: Citation Check

Use `/crossref-lookup` for DOI validation, title matching, and bibliography audits before finalizing the manuscript.

## Troubleshooting

**Issue**: Reviewer feedback asks for experiments, citations, or data that are not in the artifacts.
**Solution**: Mark the issue as blocked by missing evidence and keep the claim conservative.

**Issue**: The draft keeps changing wording without resolving the same major issue.
**Solution**: Stop the loop, report the repeated unresolved issue, and explain what missing artifact would be needed to fix it.

## References

- Workflow and checkpoints: `references/workflow.md`
- Role contracts: `references/agent-prompts.md`
- Prose-quality audits, severity tags, dead-weight phrase tables, banana rule, telephone-game audit: `references/writing-quality.md`
- Supporting skills to invoke when available: `references/supporting-skills.md`
- Reporting and citation shortcuts: `references/reporting-shortcuts.md`

## Related Skills

- `/manuscript-review-council` — run a multi-reviewer critique before revision
- `/proposal-review` — switch here for funding-proposal critique
- `/bio-logic` — evaluate evidence quality and rigor during revision
- `/crossref-lookup` — validate every cited DOI
