---
name: pickup
description: Read and resume from the latest session handoff. Queries memd first when project memory is configured and available, then falls back to docs/handoffs/ for filesystem handoffs. Summarizes both and auto-archives filesystem handoffs.
invocation: user-only
---

# /pickup

Read and resume from the latest session handoff. **Queries memd first** (structured task/artifact state is authoritative), then scans `docs/handoffs/` for narrative context.

## Usage

```
/pickup [--keep] [--no-memd]
```

## Flags

| Flag | Description |
|------|-------------|
| `--keep` | Don't archive the filesystem handoff after reading (useful to reference it again) |
| `--no-memd` | Skip the memd query, use only `docs/handoffs/` |

## Quick Reference

| Task | Action |
|------|--------|
| Resume work | Read memd project state when configured, then scan active handoff files. |
| Filesystem-only resume | Use `--no-memd` or continue automatically when memd is unavailable. |
| Preserve handoff | Use `--keep` when the handoff should remain active. |
| Archive handoff | Move only current-repo handoffs to `docs/handoffs/_archive/` after reading. |

## Instructions

### Step 0: Resolve memd tenant / project

Resolve the repo / worktree root first with `git rev-parse --show-toplevel`, then look for `.memd/config.json` at or above that root. Git treats a worktree's `.git` as a plain file (not a directory), so presence-based checks like `[ -d "$dir/.git" ]` would miss worktree roots; `rev-parse` handles both.

```bash
# Find the repo or worktree root — works for both plain repos and worktrees.
repo_root="$(git rev-parse --show-toplevel)"

# Nearest-ancestor lookup for .memd/config.json. Start at CWD, stop at the
# repo root (or at filesystem root, when not in a repo).
dir="$PWD"
config=""
while :; do
  if [ -f "$dir/.memd/config.json" ]; then
    config="$dir/.memd/config.json"
    break
  fi
  if [ -n "$repo_root" ] && [ "$dir" = "$repo_root" ]; then
    break
  fi
  parent="$(dirname "$dir")"
  if [ "$parent" = "$dir" ]; then
    break  # reached filesystem root
  fi
  dir="$parent"
done
```

Expected shape of the file:

```json
{
  "tenant_id": "example-tenant",
  "project_id": "example-project"
}
```

Classify the outcome:

- **found & valid** — parsed JSON with both `tenant_id` and `project_id` → proceed to Step 0.1.
- **found but malformed** — log explicitly and skip memd; suggest configuring project memory in the output.
- **not found** — skip memd. If `--no-memd` is NOT set, suggest configuring project memory in the output.
- **`--no-memd` set** — skip memd unconditionally; do not suggest memory configuration.

### Step 0.1: Query memd (when tenant/project resolved)

Run these in parallel. Argument shapes below are the actual tool signatures — use them exactly, with the `mcp__memd__` prefix:

1. `mcp__memd__task_search({ tenant_id, filters: { project_id }, mode: "resume_task", k: 8 })` — ranked recent tasks with progress/evidence projections.
2. `mcp__memd__context_brief_project({ tenant_id, project_id, k: 10 })` — persisted project brief digest.
3. `mcp__memd__artifact_find_decisions({ tenant_id, project_id, k: 5 })` — **top-level `project_id`, not inside `filters`**.
4. `mcp__memd__artifact_find_failures({ tenant_id, project_id, k: 5 })` — **top-level `project_id`**.

Classify each call's outcome independently — don't collapse all to one fallback:

- **tool missing** (not exposed in session) → report once and mark memd blocked; proceed to Step 1.
- **daemon unreachable / connection refused** → report the error surface; proceed to Step 1.
- **permissions / validation error** → report; proceed to Step 1.
- **empty result** → note it; continue with whatever the other memd calls returned.
- **partial success** (some calls returned, some errored) → use what you have and note which failed.

### Step 1: Scan filesystem handoffs

Primary scan: `docs/handoffs/*.md` (excluding `_archive/`) in the current repo root.

```bash
ls docs/handoffs/*.md | sort
```

Worktree scan: if the current checkout has sibling worktrees (a feature branch in isolation), the previous session may have written its handoff inside a worktree. Use git, not hardcoded paths:

```bash
git worktree list --porcelain \
  | awk '/^worktree /{print $2}'
```

For each worktree path that is NOT the current CWD, check `WORKTREE/docs/handoffs/*.md` and surface any active handoffs found. **Never archive a worktree handoff** — only the owning worktree's session should close it out.

For each handoff file, extract:

- **Area**: from filename (e.g., `2026-02-09_auth-refactor.md` → `auth-refactor`)
- **Status**: from `## Context & Status`
- **Work Completed**: from `## Technical Implementation` > `Work Completed`
- **Key Decisions**: from `## Key Decisions`
- **Next Steps**: from `## Moving Forward` > `Next Steps`
- **Blockers**: from `## Moving Forward` > `Blockers`

### Step 2: Synthesize a unified summary

Present memd state first (structured), filesystem handoffs second (narrative).

**Flag a discrepancy only when both of these hold**:

1. A memd task and a filesystem handoff appear to describe the same work. Heuristic: the handoff's area slug overlaps the task's title/subject keywords (case-insensitive token intersection ≥ 2), OR both were last modified within 24 hours of each other.
2. Their terminal state materially disagrees — one says `completed`/`done` while the other lists outstanding `Next Steps` or `Blockers`, OR their next-step lists contradict (one says "A is next", the other "B is next").

Vague overlap without state conflict is noise — don't flag it. When in doubt, present both and let the user decide.

### Step 3: Archive filesystem handoffs (unless --keep)

Only archive handoffs that live under the **current repo root's** `docs/handoffs/`. Never archive from a sibling worktree discovered in Step 1.

```bash
mkdir -p docs/handoffs/_archive
mv docs/handoffs/YYYY-MM-DD_area-desc.md \
   docs/handoffs/_archive/YYYY-MM-DD-archived_area-desc.md
```

### Step 4: Check learning review queue

```bash
cat docs/learning-tracker/queue.json
```

If present, parse for items where `dueDate <= today` and include them in the output.

## Input Requirements

- Current repository or project directory.
- Optional `.memd/config.json` or equivalent project memory configuration.
- Optional active handoff files under `docs/handoffs/`.
- Git available when worktree discovery is needed.

## Output

```
Session Resume

[Memd — tenant=X project=Y]
Recent tasks:
- [task subject] — status=[status], last update=[ts]
  Next step: [next_step from latest progress]

Recent decisions:
- [decision summary]

Recent failures / blockers:
- [failure summary]

(Or: "memd unavailable: <reason>" with a per-call breakdown if partial.)

[Filesystem handoffs]
Found [N] active handoff(s) in this repo + [M] in sibling worktrees.

### [Handoff Title / Area] (main repo | worktree: <path>)

**Status:** [status] | **Area:** [area]

**Completed:**
- [Key accomplishment 1]

**Next Steps:**
1. [Priority action 1]

**Blockers:**
- [Blocker or "None"]

[Discrepancies]
- memd task "X" is in_progress but handoff Y says "completed" — reconcile?

Handoff(s) archived to docs/handoffs/_archive/.
Worktree handoffs surfaced but not archived.

[If review items due:]
Review Queue: [N] item(s) due for review.

[If config missing and --no-memd not set:]
No .memd/config.json found. Configure project memory to enable memd-first pickup next time.
```

## Quality Gates

- [ ] Report whether memd was used, unavailable, skipped, or partially successful.
- [ ] Include active filesystem handoffs from the current repo before archiving them.
- [ ] Surface sibling-worktree handoffs without archiving them.
- [ ] Flag only material memd-vs-handoff status conflicts.
- [ ] Do not delete handoffs; archive them under `_archive/` unless `--keep` is set.

## Examples

```text
/pickup
/pickup --keep
/pickup --no-memd
```

## Troubleshooting

- **No memd config AND no handoffs**: Report cleanly. Suggest project memory configuration unless `--no-memd`.
- **Malformed memd config**: Call out the parse error specifically; suggest re-running project memory configuration.
- **memd daemon down**: Report connection error; continue.
- **memd tool not exposed**: Report missing-tool; continue.
- **Partial memd success**: Use what returned, note which failed.
- **Handoff in sibling worktree**: Surface it with the worktree path, don't archive it.
- **Conflicting memd vs handoff state**: Flag only with the heuristic above.
- **`--keep`**: Skip archiving; note that handoffs were kept active.
- **`--no-memd`**: Don't attempt memd; don't suggest memory configuration.

## Integration

- Pairs with `/handoff` which writes filesystem handoffs.
- Project memory configuration writes `.memd/config.json`.
- The installed memd workflow establishes the broader memd-first contract for substantive work; `/pickup` is the read side of that contract at session start.
