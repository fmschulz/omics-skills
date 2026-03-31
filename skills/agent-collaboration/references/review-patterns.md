# Review Patterns

Read this file when you need concrete command idioms or review prompts for another agent pane.

## Most Useful Commands for AI

| Goal | Command | Why |
|------|---------|-----|
| Discover peers | `tmux-bridge list` | Shows pane IDs, labels, process names, and working directories |
| Satisfy the read guard | `tmux-bridge read <target> 40` | Required before every interaction |
| Best review handoff | `tmux-bridge message <target> "<request>"` | Adds sender identity and reply routing automatically |
| Submit the request | `tmux-bridge keys <target> Enter` | Executes the typed request |
| Reply to sender | use the `pane:%N` value from the header | Sends the answer back to the requesting pane |

`message` is the highest-value command for agent collaboration. Use `type` only when you need raw literal input without the reply header.

If no cross-platform peer exists, send the request to a fresh same-platform pane such as `claude-review` or `codex-review`.

## Code Review Prompt

```text
Review the current diff for bugs, behavioral regressions, missing tests, and risky assumptions. Findings first, ordered by severity. Ignore pure style issues unless they hide a real defect.
```

## Plan Critique Prompt

```text
Critique this plan for hidden assumptions, edge cases, missing validation, and places where the implementation could drift from the stated goal. Be concrete and propose tighter verification where needed.
```

## Scientific Writing Critique Prompt

```text
Review this manuscript section for unsupported claims, inflated language, missing caveats, citation risk, and places where the prose outruns the supplied evidence. Stay within the provided artifacts.
```

## Results Critique Prompt

```text
Stress-test these conclusions against the actual tables, figures, and summaries. Identify overclaiming, mismatched numbers, missing uncertainty, and alternative interpretations that should be acknowledged.
```

## Read-Act-Read Pattern

```bash
tmux-bridge read codex 40
tmux-bridge message codex "Critique this plan for hidden assumptions and missing verification."
tmux-bridge read codex 10
tmux-bridge keys codex Enter
```

Do not keep reading the target pane after submission when it is another agent. Wait for the reply in your own pane.
