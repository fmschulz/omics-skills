# Routing

The router answers one question: which agent and which skills fit a task, and in what order. It reads the agent and skill Markdown files, scores the task, and prints a recommendation. It does not run the skills.

## Run the router

From a checkout:

```bash
python3 scripts/skill_index.py route "assemble a metagenome and recover MAGs"
```

```text
Agent: omics-scientist
Primary skills: bio-assembly-qc, bio-binning-qc
Supporting skills: bio-reads-qc-mapping, tracking-taxonomy-updates, bio-annotation, bio-gene-calling, bio-viromics
Suggested order: bio-reads-qc-mapping -> bio-assembly-qc -> tracking-taxonomy-updates -> bio-binning-qc
```

The output continues with the paths of the agent and skill files to open. After `make install`, the same command runs as `python3 ~/.agents/omics-skills/skill_index.py route "<task>"` and reads the installed catalog.

| Option | Effect |
|---|---|
| `--agent NAME` | Recommends only skills that agent owns. |
| `--platform claude` or `--platform codex` | Drops skills that do not support that runtime. |
| `--top-k N` | Caps the primary skills (default 4). |
| `--json` | Prints scores and match reasons as JSON. |

The [routing hint hook](INSTALL.md#routing-hint-hook) runs the router on every prompt.

## Catalog

`python3 scripts/skill_index.py build` (or `make build-catalog`) parses the sources into `catalog/catalog.json`, which the installed router reads. Three sections of each agent file feed it:

| Agent section | Produces |
|---|---|
| `Mandatory Skill Usage` | `uses` edges from the agent to its skills |
| `Workflow Decision Tree` | `workflow_next` edges (forward order) and `depend_on` edges (prerequisites) |
| `Task Recognition Patterns` | Quoted trigger phrases for each skill |

A skill that names another skill with a slash, such as `/bio-annotation`, adds an advisory edge. The words around the reference set its type: `depend_on` ("requires", "prerequisite"), `belong_to` ("part of"), `similar_to` ("instead of", "alternative"), or `compose_with` for anything else. These inferred edges are hints; the agent edges take precedence.

## Scoring

The weights are named constants at the top of [`scripts/skill_index.py`](https://github.com/fmschulz/omics-skills/blob/main/scripts/skill_index.py).

1. Each skill scores 2.0 times the share of its name and description words found in the task.
2. A trigger phrase found verbatim in the task adds 4.0. Otherwise a phrase that shares at least 34% of its words adds 3.0 times that share. A multi-word phrase must share two words, one of them not generic ("review", "data", "report" and similar words do not count alone).
3. Primary skills score at least 0.75 and at least 35% of the top score.
4. The agent with the highest score for the primary skills is selected.
5. Direct prerequisites (`depend_on`, one level) and the `compose_with` partners that a primary skill cites become supporting skills.
6. `workflow_next` edges order the result.

A request to review or fix a software repository, without `--agent`, returns no recommendation: the pack has no code-review skill.

## Benchmark

`tests/routing_benchmark.yaml` lists tasks with the expected agent, required and forbidden skills. `make benchmark` runs them and compares the result with `docs/routing_baseline.json`. The run fails on a regression: a case that passed in the baseline and fails now, or a new case that fails. Add a case when a new skill or trigger phrase should be found from plain language, and refresh the baseline with `python3 scripts/routing_benchmark.py --baseline` only after reviewing the change.
