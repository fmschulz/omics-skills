---
name: agent-collaboration
description: Coordinate cross-agent collaboration through smux/tmux-bridge for code review, plan critique, result checking, scientific writing review, and second-opinion workflows across Codex CLI and Claude Code. Prefer a different runtime when available; otherwise use a fresh same-platform instance in another tmux pane.
---

# Agent Collaboration

Use this skill when a second agent should critique or verify work instead of having one agent keep self-reviewing in place.

This skill assumes `smux` and `tmux-bridge` are available. If they are missing, read `references/smux-setup.md` first and say so explicitly if tmux collaboration is not configured.

## Most Useful Command

`tmux-bridge message <target> <text>`

Use `message` for agent-to-agent handoffs because it includes sender identity and reply routing in the typed text. It still requires the read guard: read first, then message, read again to verify, then press `Enter`.

## Peer Selection

- Prefer a different runtime for critique when available:
  - if you are in Claude Code, ask Codex CLI
  - if you are in Codex CLI, ask Claude Code
- If the other runtime is not available, start a fresh instance of the same runtime in another tmux pane and label it separately, for example `claude-review` or `codex-review`.
- Never ask the current pane to critique its own work.

## Instructions

1. Confirm the collaboration surface exists:
   - `tmux-bridge id`
   - `tmux-bridge list`
2. Label your pane and the peer pane if labels are missing. See `references/smux-setup.md`.
3. Pick the peer pane:
   - use the other runtime if it already exists
   - otherwise create a new pane and start a fresh instance of the same runtime
4. Pick the collaboration mode:
   - code review
   - plan critique
   - results critique
   - scientific writing critique
   - second-opinion debugging or design review
5. Make the ask concrete. Always name:
   - the artifact or scope
   - the review goal
   - the output format
   - what to ignore
6. Use the read-act-read-submit cycle:
   - `tmux-bridge read <target> 30`
   - `tmux-bridge message <target> "<request>"`
   - `tmux-bridge read <target> 10`
   - `tmux-bridge keys <target> Enter`
7. Do not wait or poll the peer agent pane for a reply. The reply should come back into your pane through the tmux-bridge header route.
8. When you receive a `[tmux-bridge from:...]` message, reply to the `pane:%N` value in that header.
9. For non-agent panes or shell prompts, use `type` instead of `message`, then read again to inspect the result.
10. When the task is domain-specific, combine this skill with the domain skill:
   - manuscript or rebuttal critique: `scientific-writing`
   - evidence, rigor, or claim critique: `bio-logic`

## Request Design

- Ask for findings first on reviews.
- Ask for hidden assumptions, edge cases, and missing verification on plans.
- Ask for unsupported claims, citation risk, overstatement, and missing caveats in scientific writing.
- Ask the peer agent to stay within supplied artifacts instead of inventing context.
- Prefer one bounded request per message.

## Quick Reference

| Task | Action |
|------|--------|
| Discover panes | `tmux-bridge list` |
| Label current pane | `tmux-bridge name "$(tmux-bridge id)" claude` |
| Read target pane | `tmux-bridge read codex 40` |
| Send an agent review request | `tmux-bridge message codex "review ..."` |
| Submit the typed message | `tmux-bridge keys codex Enter` |
| Resolve a label | `tmux-bridge resolve codex` |

## Input Requirements

- active tmux session
- `tmux-bridge` available in `PATH`
- a target pane running Codex CLI, Claude Code, or another shell/agent
- the artifact, diff, plan, draft, or summary to review

## Output

- peer review findings, critique, or suggested revisions returned to your pane
- a reproducible cross-agent collaboration pattern instead of ad hoc copy/paste

## Quality Gates

- [ ] panes are labeled or explicitly targetable
- [ ] read guard satisfied before every `message`, `type`, or `keys`
- [ ] request names the artifact, scope, and desired output format
- [ ] agent panes are not polled for responses after submission
- [ ] replies are sent to the sender pane from the tmux-bridge header

## Examples

### Example 1: Code Review Handoff

```bash
tmux-bridge read codex 40
tmux-bridge message codex "Review the current diff for bugs, regressions, and missing tests. Findings first, ordered by severity. Ignore style-only issues."
tmux-bridge read codex 10
tmux-bridge keys codex Enter
```

### Example 2: Scientific Writing Critique

```bash
tmux-bridge read claude 40
tmux-bridge message claude "Critique the discussion draft for unsupported claims, inflated language, missing caveats, and citation risk. Stay within the supplied manuscript artifacts."
tmux-bridge read claude 10
tmux-bridge keys claude Enter
```

### Example 3: Same-Platform Fallback

If you are already in Claude Code and no Codex pane is available, open another tmux pane, start a fresh Claude Code instance there, label it `claude-review`, and use that pane for critique instead of self-reviewing in place.

## References

- smux setup and pane labeling: `references/smux-setup.md`
- review request patterns and command idioms: `references/review-patterns.md`
