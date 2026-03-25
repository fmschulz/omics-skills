# Skill Graph

This repository uses a generated skill graph to answer one question:

Which agent and which skills should handle a task, and in what order?

The graph is real, but it is not a standalone workflow engine. It is a routing layer built from the repository's markdown files and used to narrow context for Claude Code and Codex.

## What "Skill Graph" Means Here

The graph is assembled from three kinds of relationships:

- Agent -> skill ownership from each agent's `Mandatory Skill Usage` section.
- Skill -> skill workflow links from each agent's `Workflow Decision Tree`.
- Skill -> skill advisory links inferred from skill bodies when one skill references another.

The generated outputs are:

- `catalog.json`: full parsed view of agents, skills, and edges
- `relationships.json`: skill-to-skill relationships only
- `routing.json`: lightweight routing metadata for task matching

These files are built by [`scripts/skill_index.py`](../scripts/skill_index.py).

## Source of Truth

The graph is derived from markdown, not hand-maintained JSON.

Primary sources:

- `agents/*.md`
- `skills/*/SKILL.md`

Within agent files, these sections matter:

- `## Skill Lookup`
- `## Mandatory Skill Usage`
- `## Workflow Decision Tree`
- `## Task Recognition Patterns`

Within skill files, slash-prefixed references to other skills can produce advisory relationships such as `compose_with` or `depend_on`.

## Build Process

Build the catalog from the repository root:

```bash
python3 scripts/skill_index.py build
```

Or use:

```bash
make build-catalog
```

The builder parses every `skills/*/SKILL.md` and `agents/*.md`, then emits:

- `catalog/catalog.json`
- `catalog/relationships.json`
- `catalog/routing.json`

## Edge Types

The current graph uses these edge types:

- `uses`: an agent explicitly owns or uses a skill
- `workflow_next`: a workflow decision tree says one skill leads to another
- `depend_on`: a skill should come after another skill
- `compose_with`: two skills are commonly used together
- `similar_to`: one skill is an alternative to another
- `belong_to`: one skill is part of a larger unit of work

Two details matter:

- `workflow_next` and `depend_on` are both generated from the workflow tree. One gives forward order, the other gives prerequisite order.
- Skill-body relationships are heuristic. They are useful for routing, but they are not as strong as explicit workflow edges from an agent file.

## How Routing Works

Routing is handled by:

```bash
python3 scripts/skill_index.py route "<task>"
```

The router:

1. Loads the built catalog or rebuilds it from the repo.
2. Scores skills against the task using:
   - skill name and description overlap
   - `Task Recognition Patterns`
   - optional agent filter
   - optional platform filter such as `--platform codex`
3. Selects the best matching primary skills.
4. Pulls in prerequisite skills through `depend_on` edges.
5. Orders the final list with `workflow_next` edges.
6. Returns:
   - selected agent
   - primary skills
   - supporting skills
   - suggested order
   - referenced agent and skill file paths

Example:

```bash
python3 scripts/skill_index.py route "assemble a metagenome and recover MAGs"
```

Typical output shape:

```text
Agent: omics-scientist
Primary skills: bio-assembly-qc, bio-binning-qc
Supporting skills: bio-reads-qc-mapping
Suggested order: bio-reads-qc-mapping -> bio-assembly-qc -> bio-binning-qc
```

## How Claude Code Uses It

Claude Code is expected to use an installed agent file such as:

```bash
claude --agent omics-scientist
```

After installation, agent prompts in `~/.claude/agents/` tell Claude to:

1. Run the shared catalog router first.
2. Use the returned skill order as the default path.
3. Open only the referenced `SKILL.md` files.
4. Follow the ordered workflow unless the task clearly falls outside it.

In practice, the intended loop is:

```bash
python3 ~/.agents/omics-skills/skill_index.py route "<task>" --agent omics-scientist
```

Then Claude works from the returned subset instead of scanning the whole repository.

## How Codex Uses It

Codex is expected to load an installed agent prompt such as:

```bash
codex --system-prompt ~/.codex/agents/omics-scientist.md
```

Or set one as the default agent:

```bash
codex config set default_agent ~/.codex/agents/omics-scientist.md
```

The Codex agent prompt follows the same model as Claude:

1. Route the task with `skill_index.py route`.
2. Restrict context to the returned agent file and `SKILL.md` files.
3. Execute the task using that ordered set of skills.

For long-running coding work, the separate `codexloop` skill adds a durable task graph over a repository plan:

```bash
~/.codex/bin/codexloop init .
~/.codex/bin/codexloop plan --repo .
~/.codex/bin/codexloop run --repo .
```

That is a different graph from the skill-routing graph. `codexloop` turns a project plan into executable tasks and worktrees; the shared skill graph decides which skills and agents fit a user request.

## What This Is Not

This repository does not currently implement:

- a native skill executor that walks `relationships.json` by itself
- a strict schema-backed DAG with full validation
- direct Claude or Codex integration that automatically consumes `catalog.json`

Instead, the graph is consumed through prompt instructions plus the `route` command.

## Practical Mental Model

Use this model when working in the repo:

- Agent markdown defines policy and workflow structure.
- Skill markdown defines behavior and optional cross-skill references.
- `skill_index.py` turns those docs into a graph.
- `route` turns the graph into a recommended workflow for a task.
- Claude Code or Codex follows that recommendation by loading only the relevant prompts.

## Maintenance Rules

When adding or changing a skill, update the graph inputs, not only the prose:

1. Add or update the skill's `SKILL.md`.
2. Update the relevant agent file:
   - `Mandatory Skill Usage`
   - `Workflow Decision Tree`
   - `Task Recognition Patterns`
3. Rebuild the catalog.
4. Run tests:

```bash
python3 -m unittest tests/test_skill_index.py
```

If the workflow tree or task patterns are missing, the graph will be incomplete even if the skill documentation is otherwise good.

## Current Limitation

The graph builder uses markdown parsing and slash-prefixed token extraction. That keeps authoring simple, but it also means skill-body relationships are advisory and may include false positives if prose looks like a skill reference.

Treat explicit agent workflow edges as authoritative. Treat inferred skill-body edges as hints.
