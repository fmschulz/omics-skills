# Routing

The router answers one question: which agent and which skills fit a task, and in what order. It reads the agent and skill Markdown files, scores the task, and prints a recommendation. It does not run the skills.

## Run the router

From a checkout:

```bash
python3 scripts/skill_index.py route "assemble a metagenome and recover MAGs"
```

```text
Agent: omics-scientist
Primary skills: omics-pipeline, bio-assembly-qc, bio-binning-qc
Supporting skills: bio-reads-qc-mapping, tracking-taxonomy-updates
Suggested order: omics-pipeline -> bio-reads-qc-mapping -> bio-assembly-qc -> tracking-taxonomy-updates -> bio-binning-qc
Hidden stage skills (read the file after omics-pipeline): bio-reads-qc-mapping, bio-assembly-qc, tracking-taxonomy-updates, bio-binning-qc
```

The output continues with the paths of the agent and skill files to open. After `make install`, the same command runs as `python3 ~/.agents/omics-skills/skill_index.py route "<task>"` and reads the installed catalog.

| Option | Effect |
|---|---|
| `--agent NAME` | Recommends only skills that agent owns. |
| `--platform claude` or `--platform codex` | Drops skills that do not support that runtime. |
| `--top-k N` | Caps the scored primary skills (default 4). |
| `--json` | Prints scores, match reasons and the hidden skills as JSON. |

The [routing hint hook](INSTALL.md#routing-hint-hook) runs the router on every prompt.

## Hidden pipeline stages

The pipeline stage skills are hidden from the model's skill list (see [Skills](skills.md)), so a route to one of them must also name the way in. When a hidden stage is a primary skill, the router puts `omics-pipeline` first in the primary skills and in the suggested order, and it lists every hidden skill in `hidden_skills`. The routing hint prints those as stage skills without a slash: the model loads `/omics-pipeline` and then reads the stage's `SKILL.md` by path. The router leaves `omics-pipeline` out when a pinned agent or platform cannot use it.

## Catalog

`python3 scripts/skill_index.py build` (or `make build-catalog`) parses the sources into `catalog/catalog.json`, which the installed router reads. Each agent file feeds it through one `## Skills` table:

| Column | Required | Produces |
|---|---|---|
| `Skill` | yes | The skill, in backticks, and a `uses` edge from the agent to it |
| `Use for` | yes | A short label that groups the agent's skills |
| `Phrases` | no | Quoted trigger phrases for the skill |
| `After` | no | Skills that normally run first: `workflow_next` edges (forward order) and `depend_on` edges (prerequisites) |

Only the `## Skills` table counts. A skill named elsewhere in the agent file, such as one that comes from another repository, is plain prose to the parser. The catalog also records each skill's `hidden` flag, read from `disable-model-invocation` in its frontmatter.

A skill that names another skill with a slash, such as `/bio-annotation`, adds an advisory edge. The words around the reference set its type: `depend_on` ("requires", "prerequisite"), `belong_to` ("part of"), `similar_to` ("instead of", "alternative"), or `compose_with` for anything else. These inferred edges are hints; the agent edges take precedence.

## Scoring

The weights are named constants at the top of [`scripts/skill_index.py`](https://github.com/fmschulz/omics-skills/blob/main/scripts/skill_index.py).

1. Each skill scores 2.0 times the share of its name and description words found in the task.
2. A trigger phrase found verbatim in the task adds 4.0. Otherwise a phrase that shares at least 34% of its words adds 3.0 times that share. A multi-word phrase must share two words, one of them not generic ("review", "data", "report" and similar words do not count alone).
3. Primary skills score at least 0.75 and at least 35% of the top score.
4. The agent with the highest score for the primary skills is selected.
5. When a primary skill is hidden, `omics-pipeline` joins the primary skills first.
6. Direct prerequisites (`depend_on`, one level) and the `compose_with` partners that a primary skill cites become supporting skills.
7. `workflow_next` edges order the result.

Without `--agent`, two kinds of request return no recommendation. A request to review or fix a software repository gets none, because the pack has no code-review skill. A request to draft, rewrite or revise manuscript prose (an action word such as "draft" or "revise" plus "manuscript", "paper", "abstract" or "discussion") gets none, because `academic-writing` comes from another repository. Naming a workflow engine or its artifacts (`Nextflow`, `Snakemake`, `CWL`, `pipeline`, `workflow`, `artifacts`) marks a different request, Methods generated from a run, which `bio-workflow-methods-docwriter` owns. Manuscript review, PDF conversion and claim-graph extraction also return nothing, for the same reason.

## Benchmark

`tests/routing_benchmark.yaml` lists tasks with the expected agent, required and forbidden skills. `make benchmark` runs them and compares the result with `docs/routing_baseline.json`. The run fails on a regression: a case that passed in the baseline and fails now, or a new case that fails. Add a case when a new skill or trigger phrase should be found from plain language, and refresh the baseline with `python3 scripts/routing_benchmark.py --baseline` only after reviewing the change.

A case for a hidden stage lists `omics-pipeline` and the stage in `expected_primary_skills`. A case for any other skill can list `omics-pipeline` in `forbidden_skills` to guard against the router leaking into unrelated work.
