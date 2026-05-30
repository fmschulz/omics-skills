# Routing

The router answers a practical question: which agent and which skills should handle this task, and in what order?

It is not a workflow engine. It reads Markdown metadata from agents and skills, scores a user task, and returns a compact recommendation that an agent can follow.

## Run the Router

From the repository root:

```bash
python3 scripts/skill_index.py route "assemble a metagenome and recover MAGs"
```

For an installed checkout:

```bash
python3 ~/.agents/omics-skills/skill_index.py route "find recent bioRxiv papers on giant viruses"
```

Constrain the recommendation to one agent:

```bash
python3 scripts/skill_index.py route --agent literature-expert "validate these DOIs"
```

Typical output:

```text
Agent: omics-scientist
Primary skills: bio-assembly-qc, bio-binning-qc, tracking-taxonomy-updates
Supporting skills: bio-reads-qc-mapping, bio-annotation, bio-gene-calling, bio-viromics
Suggested order: bio-reads-qc-mapping -> bio-assembly-qc -> tracking-taxonomy-updates -> bio-binning-qc
```

## Install the Hook

The hook runs the router automatically for each prompt and injects a short routing hint:

```bash
make install-hook
make hook-status
```

The hook is intentionally conservative. If routing fails, it exits without blocking the prompt. Disable it for one shell session with:

```bash
export OMICS_SKILLS_AUTOROUTE=0
```

## How the Router Scores Tasks

The router uses:

- Skill names and descriptions.
- Agent task-recognition patterns, with generic one-word overlaps suppressed for multi-word patterns.
- Agent-to-skill ownership.
- Workflow edges from each agent's decision tree.
- Skill-to-skill references from skill bodies.
- Optional filters such as `--agent` and `--platform`.

The generated catalog lives in `catalog/`:

| File | Purpose |
|---|---|
| `catalog.json` | Parsed agents, skills, metadata, and graph edges — the single source of truth the router consumes. |

Rebuild it after changing agent or skill text:

```bash
python3 scripts/skill_index.py build
```

The detailed routing model is documented in [Skill Graph](SKILL_GRAPH.md).
