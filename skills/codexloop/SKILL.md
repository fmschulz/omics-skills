---
name: codexloop
description: Run a Codex-native planning and implementation loop with docs/plans progress tracking, MEMORY.md failure memory, per-task git worktrees, and iterative verification until tasks pass or need human intervention. Use when you want Mycelium-like orchestration for Codex without the Mycelium stack.
---

# CodexLoop

Use `codexloop` when a task needs a durable execution harness rather than a single Codex turn.

## Instructions

1. Confirm the global launcher exists at `~/.codex/bin/codexloop`.
2. In the target repository, initialize the scaffold yourself. Do not ask the user to pre-create plan or memory files. `init` is responsible for generating them:

```bash
~/.codex/bin/codexloop init .
```

3. `init` generates these project-local files automatically:
- `.codexloop/config.json`
- `.codexloop/doctor.sh`
- `docs/plans/implementation-plan.md`
- `docs/plans/CODEXLOOP_AGENT.md`
- `MEMORY.md`

4. Fill in or refine the generated plan/doctor content as needed for the project, then generate or refresh the task backlog:

```bash
~/.codex/bin/codexloop plan --repo .
```

5. Execute the plan:

```bash
~/.codex/bin/codexloop run --repo .
```

6. Inspect or continue a run:

```bash
~/.codex/bin/codexloop status --repo .
~/.codex/bin/codexloop resume --repo .
```

## What It Maintains

- `docs/plans/active/*.md` for the live plan and progress log
- `docs/plans/completed/*.md` for finished runs
- `MEMORY.md` for resolved failures and lessons
- `.codexloop/` for runtime state, task worktrees, event logs, and config

## Quick Reference

| Task | Action |
|------|--------|
| Initialize harness | `~/.codex/bin/codexloop init .` |
| Generate backlog | `~/.codex/bin/codexloop plan --repo .` |
| Execute plan | `~/.codex/bin/codexloop run --repo .` |
| Check progress | `~/.codex/bin/codexloop status --repo .` |
| Continue stopped run | `~/.codex/bin/codexloop resume --repo .` |

## Input Requirements

- A Git repository
- Codex CLI installed and authenticated
- `~/.codex/bin/codexloop` installed via `make install`
- Permission to create project-local harness files with `~/.codex/bin/codexloop init .`
- A concrete implementation plan in `docs/plans/implementation-plan.md` after initialization
- A repo-specific verification command in `.codexloop/doctor.sh` after initialization

## Output

- Planned backlog in `.codexloop/tasks/`
- Live progress in `docs/plans/active/`
- Finished plan records in `docs/plans/completed/`
- Reusable failure memory in `MEMORY.md`
- Runtime state, worktrees, and Codex event logs in `.codexloop/`

## Quality Gates

- [ ] The plan exists in `docs/plans/implementation-plan.md`
- [ ] The repo-specific doctor command is configured
- [ ] `run` completes with all tasks merged, or `status` explains what still needs intervention
- [ ] `MEMORY.md` is updated when failures are solved after retries

## Examples

### Example 1: Start a New CodexLoop Run

```bash
~/.codex/bin/codexloop init .
# edit docs/plans/implementation-plan.md and .codexloop/doctor.sh
~/.codex/bin/codexloop plan --repo .
~/.codex/bin/codexloop run --repo .
```

### Example 2: Resume a Stopped Run

```bash
~/.codex/bin/codexloop status --repo .
~/.codex/bin/codexloop resume --repo .
```

## Troubleshooting

**Issue**: `codexloop` is not found
**Solution**: Run `make install` and either add `~/.codex/bin` to `PATH` or call `~/.codex/bin/codexloop` directly.

**Issue**: The run stops after retries
**Solution**: Inspect `docs/plans/active/*.md`, `MEMORY.md`, and `.codexloop/runs/*/tasks/*` to see the last failing verification or Codex event log, then run `~/.codex/bin/codexloop resume --repo .`.
