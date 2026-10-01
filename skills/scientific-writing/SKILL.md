---
name: scientific-writing
description: Draft or revise scientific prose without changing its claims. Use for manuscript sections, proposal narratives, rebuttals, response letters, or a sentence-level clarity review.
---

# Scientific Writing

One scientific-writing skill for Codex and Claude Code. It has two modes that share one role set and one set of hard rules:

- **Drafting and revision**: produce a manuscript section or rebuttal from authoritative artifacts and improve it through review and revision loops.
- **Writing review**: audit existing prose for clarity, voice, sentence structure, terminology, and numerical consistency without changing the science.

## Routing Boundary

- Use this skill when the output is manuscript prose, or a prose-quality review that keeps the scientific claims as they are.
- Use `/bio-logic` when the question is whether a method, design, causal claim, or interpretation is scientifically justified.
- Use `/manuscript-review-council` for journal-style peer review or a multi-reviewer critique, then bring the evidence-backed revisions back here.
- Use `/proposal-review` to critique a funding proposal; use this skill to write or revise its narrative.
- A request that only says "write" does not establish scientific-writing intent.

## State Assumptions First

Before drafting or reviewing, state:

- manuscript mode: new draft, revision, rebuttal, review response, section rewrite, or writing review
- review mode for a writing review (see below)
- target venue or formatting target when known
- authoritative artifacts available
- missing artifacts that block specific claims

If a required input is missing, name the gap and limit the affected claim to what the evidence shows.

## Review Modes

| Mode | Trigger | Behavior |
|---|---|---|
| `full-review` | "review my manuscript", "writing review" | Run all five prose audits on the whole document. Default when the request is ambiguous. |
| `section-review` | "review the Introduction" | Run all five audits on one section. |
| `targeted` | "fix passive voice", "strip the clutter" | Run only the requested audit passes. |
| `interactive` | "walk me through improving this" | Go paragraph by paragraph: original, revision, reason; wait for confirmation. |

## Instructions

1. Inventory the artifact bundle before writing or reviewing. See [references/workflow.md](references/workflow.md).
2. Split the run into the roles in [Role Set](#role-set). Use subagents when the platform offers them; otherwise run the roles in sequence and keep their outputs separate.
3. **Drafting**: write in this order: Methods, section outline, manuscript prose, citation audit.
4. **Writing review**: run the five audits in [references/writing-quality.md](references/writing-quality.md) in order. Each finding carries a severity tag and a concrete revision.
5. Apply the [Manuscript Rules](#manuscript-rules) to every draft and every review.
6. Run a `review -> revise -> review` loop until one of these is true:
   - no fixable major issues remain
   - only minor edits remain
   - the remaining issues need evidence that is not available
   - another loop would repeat the same findings without improvement
7. Review each figure and its legend together:
   - remove in-plot titles; the legend opens with a short title that names what is shown, not the result
   - the legend states what is plotted: panels, axes and units, what colours, shapes, and lines encode, n per group, what error bars or intervals show, and the statistical test; the finding belongs in the Results text
   - plots are greyscale by default; use colour only when it encodes information (a category the reader must tell apart, the one highlighted finding, an ordered or signed quantity), use a colourblind-safe palette, and never make colour the only encoding
   - prefer direct labels and panel labels over large legends
   - flag 3D effects, pie charts, dual y-axes, heavy grids, decorative gradients, and overloaded multi-series plots
   - suggest a sentence or table when a figure shows only one or two values, small multiples for many series, and slopegraphs for before/after contrasts
8. Keep intermediate artifacts auditable: plan, Methods draft, outline, manuscript draft, citation audit, review notes, and revision notes.
9. Validate citations before finalizing. Use `/crossref-lookup` for DOI and title checks.
10. Report unresolved evidence gaps explicitly instead of smoothing them over.

## Manuscript Rules

These rules apply to drafting, revision, and review. Flag violations as MAJOR findings.

- State each supported claim once, plainly. Do not follow every claim with a caveat sentence.
- State each limitation once, where it applies (usually one limitations paragraph in the Discussion), and do not repeat it across sections.
- When the data support a comparative claim ("A recovered more genomes than B"), state it directly with the numbers. Do not soften it with stacked qualifiers.
- Never explain away a result with a reason that has not been checked. If the cause is unknown, say that it is unknown or name the analysis that would test it.
- Figure and table legends describe what is shown; they do not restate results or interpretation.
- Keep implementation details out of Results: script names, file formats, internal flags, refactors, and runtime bookkeeping. Put what a reader needs to reproduce the work in Methods.
- Do not use an em dash as the default connector. Use a period, comma, colon, semicolon, or parentheses.

## Prose-Quality Audits

The reviewer applies five audits in order. Tables, examples, and constraints are in [references/writing-quality.md](references/writing-quality.md).

1. **Clutter**: remove dead-weight phrases, empty openers, and redundancy.
2. **Voice and verbs**: change passives that hide the actor to active voice; turn nominalizations back into verbs ("provides a description of" becomes "describes"). Passive is fine when the actor is unknown or when the venue requires it in Methods.
3. **Sentence architecture**: flag subjects separated from their verb by more than about 12 words, and paragraphs of uniform sentence length.
4. **Terminology**: keep defined terms fixed (the Banana Rule), define each acronym at first use in the Abstract, main text, and each legend, and reject acronyms invented for the authors' convenience.
5. **Numbers and citations**: check N, percentages, and significant figures across Abstract, text, tables, and figures; trace statistics cited only through reviews back to the primary source.

Every finding gives the section reference, original text, concrete revision, audit pass, and severity: **CRITICAL** (misleads the reader), **MAJOR** (impairs clarity or breaks a Manuscript Rule), or **MINOR** (worth fixing, does not impede understanding). The reviser handles CRITICAL and MAJOR first.

## Input Requirements

- manuscript request, brief, or target section
- authoritative artifacts such as prior drafts, notes, protocols, code, logs, or structured results
- bibliography inputs such as `.bib` files, DOI lists, or trusted reference notes
- venue instructions when available

## Output

- manuscript draft or revised section in paragraph prose
- auditable planning, review, and revision notes
- citation audit results when citation work is in scope
- explicit unresolved evidence gaps

## Quality Gates

- [ ] claims stay within the supplied evidence, and supported claims are stated without repeated caveats
- [ ] each limitation appears once
- [ ] no result is explained by an unchecked cause
- [ ] Methods trace to real artifacts rather than inference
- [ ] numbers in prose match structured summaries or tables
- [ ] legends describe panels, axes, units, encodings, n, error bars, and tests, and do not restate results
- [ ] figures are greyscale unless colour encodes information, and colour is never the only encoding
- [ ] Results contain no implementation details that belong in Methods
- [ ] citations are validated, inherited from trusted sources, or marked for follow-up
- [ ] reviewer findings are fixed or carried forward as blocked gaps

## Role Set

Full contracts are in [references/agent-prompts.md](references/agent-prompts.md).

- `planner`: audits the artifact bundle and defines the writing order
- `methods-writer`: drafts Methods from source artifacts only
- `structure-writer`: creates the section outline and figure/table plan
- `writer`: drafts paragraph prose from the plan and the evidence
- `citation-auditor`: checks citation correctness, placement, and bibliography safety
- `reviewer`: reviews scientific content and prose quality and sets revision priorities
- `reviser`: applies evidence-backed fixes and carries blocked issues forward

## Hard Rules

- Do not invent data, experiments, citations, reviewer comments, or bibliography entries.
- Do not transcribe numbers from memory when structured tables, JSON, CSV, or prior manuscripts exist.
- Do not edit `.bib` files silently; describe or stage citation edits.
- Final manuscript text is paragraph prose; bullets belong only in planning artifacts.
- If reviewer feedback needs new evidence, say so directly.
- In a writing review, change delivery, not substance. Flag a claim that looks wrong instead of rewriting it.
- Respect field and venue conventions, such as passive voice in Methods. Ask about the venue when it is not stated.
- Preserve the author's voice. Leave a clear sentence alone even if it breaks an audit rule.

## Example

Section rewrite with a review loop:

1. inventory the artifact bundle and identify missing evidence
2. draft the section in paragraph prose
3. run reviewer and reviser passes until the remaining issues are minor or blocked by missing evidence
4. return the revised section and the unresolved gaps

## Troubleshooting

**Issue**: Reviewer feedback asks for experiments, citations, or data that are not in the artifacts.
**Solution**: Mark the issue as blocked by missing evidence and limit the claim to what the artifacts show.

**Issue**: The draft keeps changing wording without resolving the same major issue.
**Solution**: Stop the loop, report the repeated issue, and name the artifact that would resolve it.

## References

- Workflow and checkpoints: [references/workflow.md](references/workflow.md)
- Role contracts: [references/agent-prompts.md](references/agent-prompts.md)
- Prose audits, phrase tables, Banana Rule, citation tracing: [references/writing-quality.md](references/writing-quality.md)
- Supporting skills: [references/supporting-skills.md](references/supporting-skills.md)
- Reporting guidelines and citation policy: [references/reporting-shortcuts.md](references/reporting-shortcuts.md)

## Related Skills

- `/manuscript-review-council`: multi-reviewer critique before revision
- `/proposal-review`: funding-proposal critique
- `/bio-logic`: evidence quality and rigor during revision
- `/crossref-lookup`: DOI validation for every cited reference
