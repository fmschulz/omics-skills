---
name: scientific-writing
description: Draft, review, and iteratively revise scientific manuscripts with a provider-agnostic multi-agent workflow for Codex and Claude Code. Use for new manuscripts, section rewrites, rebuttals, response letters, or manuscript QA when claims must stay grounded in supplied artifacts.
---

# Scientific Writing

Use this as the single scientific-writing skill for both Codex and Claude Code. It replaces the older duplicate writing skill and keeps the workflow grounded in manuscript artifacts rather than free-form background knowledge.

## State Assumptions First

Before drafting, state:

- manuscript mode: new draft, revision, rebuttal, review response, or section rewrite
- target venue or formatting target when known
- authoritative artifacts available
- missing artifacts that block specific claims

If a required input is missing, name the gap and keep the prose conservative.

## Instructions

1. Inventory the artifact bundle before writing. See `references/workflow.md`.
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
4. Draft in a fixed order: Methods, structure outline, manuscript prose, citation audit.
5. Run an explicit `review -> revise -> review` loop until one of these is true:
   - no fixable major issues remain
   - only minor edits remain
   - the remaining issues require missing evidence
   - another loop would only repeat the same findings without material improvement
6. Keep intermediate artifacts auditable: plan, methods draft, outline, manuscript draft, citation audit, review notes, and revision notes.
7. Validate citations before finalizing. Use `/crossref-lookup` when DOI or title checks are needed.
8. Return unresolved evidence gaps explicitly instead of smoothing them over.

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
- Supporting skills to invoke when available: `references/supporting-skills.md`
- Reporting and citation shortcuts: `references/reporting-shortcuts.md`
