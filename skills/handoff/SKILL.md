---
name: handoff
description: Create a session handoff document for context continuity. Captures work completed, decisions, knowledge, and next steps in docs/handoffs/.
invocation: user-only
---

# /handoff

Create a session handoff document to ensure context continuity for future sessions.

## Usage

```
/handoff [area] [description]
```

**Arguments:**
- `area`: Short identifier for the work area (e.g., `auth`, `pipeline`, `frontend`)
- `description`: Brief description slug (e.g., `refactor-login`, `add-blast-step`)

If no arguments are provided, infer the area and description from the current session context.

## Behavior

1. **Gather context** from the current session (files modified, decisions made, work done)
2. **Create file** at: `docs/handoffs/YYYY-MM-DD_[area]-[description].md`
3. **Populate** all required sections (see Template below)
4. **Confirm** creation with file path

## Quick Reference

| Task | Action |
|------|--------|
| Start handoff | Inspect git status, recent commits, current branch, and current task notes. |
| Write file | Create `docs/handoffs/YYYY-MM-DD_area-description.md`. |
| Capture decisions | Record what changed, why it changed, what remains, and current blockers. |
| Confirm | Report the handoff path and the most important next step. |

## Instructions

### Step 1: Gather Session Context

Collect information from the current session:

```bash
# Check what files were modified
git diff --name-only HEAD
git diff --staged --name-only
git status --short

# Check recent commits on this branch
git log --oneline -10
```

### Step 2: Create Handoff Directory

```bash
mkdir -p docs/handoffs
```

### Step 3: Generate Handoff File

Create the file at `docs/handoffs/YYYY-MM-DD_[area]-[description].md` using today's date.

**Filename rules:**
- Date prefix: `YYYY-MM-DD_`
- Area and description: lowercase, kebab-case
- Example: `docs/handoffs/2026-02-09_auth-jwt-migration.md`

### Step 4: Confirm

Report: `Handoff created: docs/handoffs/YYYY-MM-DD_[area]-[description].md`

## Input Requirements

- Current repository or project directory.
- Enough session context to identify work completed, decisions made, and next steps.
- Optional `area` and `description` arguments; infer them from branch or task context only when clear.

## Output

- One Markdown handoff under `docs/handoffs/`.
- A concise confirmation with the handoff path.
- A resumable summary containing status, file map, decisions, gotchas, blockers, and next steps.

## Quality Gates

- [ ] Handoff filename is date-prefixed and kebab-case.
- [ ] Work completed, outcomes, key decisions, next steps, and blockers are present.
- [ ] File paths and branch name are included when available.
- [ ] The most important next step is listed first.
- [ ] If context is unclear, ask before inventing a handoff area or status.

## Template

The handoff file MUST contain all of the following sections:

```markdown
# Handoff: [Area] - [Description]
**Date:** YYYY-MM-DD
**Branch:** [current branch name]

## Context & Status

[What you were working on and what got done. Current status of the area.]

## Technical Implementation

### Work Completed
- [Detailed item with file path] (`path/to/file.ts`)
- [Another item] (`path/to/other.py`)

### Outcomes
- **What worked:** [Specific things that succeeded]
- **What didn't:** [Issues encountered and how they were resolved]

### File Map
| File | Change | Notes |
|------|--------|-------|
| `path/to/file` | Added/Modified/Deleted | Brief note |

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| [What was decided] | [Why it was decided this way] |

## Knowledge Capture

### Lessons Learned
- [Lesson 1]

### Gotchas
- [Unexpected issue or tricky logic to watch out for]

## Moving Forward

### Next Steps
1. [Priority 1 - most important]
2. [Priority 2]
3. [Priority 3]

### Blockers
- [Current impediment, or "None"]
```

## Content Guidelines

- **Be specific**: Include file paths, function names, error messages
- **Explain why**: Decisions without rationale are useless to a future reader
- **Prioritize next steps**: The most important action goes first
- **Capture gotchas**: These save the most time in future sessions
- **Keep it concise**: Enough detail to resume without re-investigating, no more

## Examples

```text
/handoff assembly autocycler-update
```

Creates `docs/handoffs/YYYY-MM-DD_assembly-autocycler-update.md` and fills the standard handoff template.

## Troubleshooting

- **No arguments**: Infer area from branch name or recent work; ask user if unclear
- **No `docs/handoffs/` directory**: Create it automatically
- **Duplicate filename**: Append a numeric suffix (e.g., `2026-02-09_auth-refactor-2.md`)
- **No git context available**: Fill in what's known from the conversation

## Integration

Pairs with `/pickup` skill which reads and resumes from handoff documents created by this skill.
