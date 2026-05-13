# omics-skills

Agents and skills for bioinformatics, literature discovery, scientific writing,
and data visualization. Runs under Claude Code and the Codex CLI.

## Highlights

- **Five agent personas** (`omics-scientist`, `literature-expert`, `science-writer`, `dataviz-artist`, `codexloop`) that orchestrate skills through a deterministic router rather than ad-hoc selection.
- **2026 bioinformatics tooling**: IQ-TREE 3, VeryFastTree 4, BRAKER3, pyrodigal-gv, Infernal `cmsearch` with Rfam SSU/LSU models, vConTACT3, gvclass, metaMDBG, CheckM2 v1.1.0, OrthoFinder v3, Foldseek v9, Boltz-2.
- **GPU-accelerated alternatives wired in** where they exist: MMseqs2-GPU for sequence and profile search, NVIDIA Parabricks `fq2bam` for short-read alignment, `mm2-fast` / `mm2-gb` for minimap2, Foldseek `--gpu 1`, ColabFold with MMseqs2-GPU MSA backend, XGBoost `device=cuda`, RAPIDS cuML.
- **Comparative discovery axes** enforced when close relatives are available: genome-property frontier, marker-gene census, per-family copy-number expansion/contraction, synteny and conserved neighborhoods, and explicit non-coding RNA census — each producing persisted, side-by-side comparison artifacts.
- **Scientific project loop**: hypothesis register (≥5 working hypotheses), intermediate-result reflection, literature-derived analysis playbooks, hypothesis revision, and a final synthesis that tracks ruled-out alternatives.
- **Literature search with fallbacks**: `polars-dovmed` hosted API over PMC and bioRxiv corpora, local parquet `dovmed scan` as a fallback, then targeted `WebFetch` / `WebSearch` so endpoint outages do not silently skip the literature-context step.

## Install

```bash
git clone https://github.com/fmschulz/omics-skills.git
cd omics-skills
make install
```

`make install` builds `catalog/` and symlinks skills and agents into
`~/.claude/` and `~/.codex/`. Use `make install-claude` or `make install-codex`
for a single runtime, and `make status` to report what's installed.
`make install INSTALL_METHOD=copy` installs copies instead of symlinks.

Detailed install and troubleshooting notes: [INSTALL.md](INSTALL.md).

## Enable the routing hook

The router picks an agent and an ordered set of skills for a task. Without the
hook it is a manual command; with the hook it runs on every user prompt and
prepends a short routing hint to the model context.

```bash
make install-hook        # Claude Code + Codex CLI
make hook-status         # check install state
make uninstall-hook      # remove
```

Set `OMICS_SKILLS_AUTOROUTE=0` in the environment to suppress the hint for a
session without uninstalling.

## Using it

Invoke an agent directly:

```bash
claude --agent omics-scientist
codex --system-prompt ~/.codex/agents/omics-scientist.md
```

Query the router manually:

```bash
python3 scripts/skill_index.py route \
  "assemble a metagenome and recover MAGs"
```

Skills are invocable individually as `/<skill-name>`. Agent files list which
skills each agent exposes and how they compose.

## Agents

| Agent | Focus | Skills |
|---|---|---:|
| `omics-scientist` | Sequencing reads, assembly, binning, annotation, phylogenomics, MAG recovery, JGI access | 16 |
| `literature-expert` | PMC full text, arXiv and bioRxiv preprints, DOI metadata, citation impact | 7 |
| `science-writer` | Manuscript drafting, multi-reviewer critique, proposal review, AI-output evaluation | 7 |
| `dataviz-artist` | marimo notebooks, matplotlib/seaborn figures, Plotly Dash dashboards, widget and badge helpers | 9 |
| `codexloop` | Plan-driven implementation harness with resumable Codex runs | 2 |

Run `python3 scripts/skill_index.py route --agent <agent> "<task>"` to see how
a specific agent routes a given task.

## Scientific project discipline

For exploratory omics work, `omics-scientist` keeps reasoning visible end-to-end:

1. **Hypothesis register** — at least 5 distinct working hypotheses (biological, technical, null, batch, database) before the first analysis step.
2. **Intermediate reflection** — after each major result or QC gate, state observation, QC status, supported and weakened hypotheses, remaining alternatives, and the next discriminating check.
3. **Literature-derived analysis playbook** — before declaring what is "interesting", summarize what the literature considers diagnostic for the inferred group (markers, comparison sets, plots, outliers, tools).
4. **Comparative discovery axes** (when relatives are available) — genome-property frontier, marker-gene census, per-family copy-number, synteny and conserved neighborhoods, ncRNA census; each axis produces a persisted side-by-side artifact.
5. **Hypothesis revision** — update each hypothesis as supported / weakened / ruled out / unresolved with the evidence that changed its status.
6. **Final synthesis** — hypothesis history, literature context, revised ranking, limitations, and the next experiments that would best separate remaining alternatives.

These behaviors are encoded in `AGENTS.md`, `agents/omics-scientist.md`, `skills/bio-logic/SKILL.md`, and the bio-* skills that produce annotations, viral calls, phylogenies, pangenomes, and final reports. With the default symlink install, updates apply immediately after `git pull`; with `INSTALL_METHOD=copy`, rerun `make install INSTALL_METHOD=copy`.

## CodexLoop

`codexloop` is a separate harness for long-running coding work that needs
durable progress tracking. The agent file is `agents/codexloop.md`; the
runtime lives in `skills/codexloop/`. After `make install`, use the launcher:

```bash
codexloop init /path/to/project      # scaffolds docs/plans/, MEMORY.md, .codexloop/
codexloop plan --repo /path/to/project
codexloop run  --repo /path/to/project
codexloop resume --repo /path/to/project
```

`init` creates the project-local scaffold (implementation plan, doctor check,
runtime state, per-project agent file). Planning uses Codex structured output
to produce a task backlog; each task runs in its own Git worktree. Verification
failures retry automatically until the task passes or the retry budget runs
out.

## Repository layout

```
agents/                     5 agent definitions
skills/                     36 skill directories; each has SKILL.md
catalog/                    generated router artifacts (catalog, relationships, routing)
scripts/
  skill_index.py            router and catalog builder
  routing_benchmark.py      regression harness (37 tasks)
  emit_routing_hint.py      hook payload generator
  install_hook.py           idempotent hook installer
  install.sh                shell-script install (Makefile-free)
  uninstall.sh, test-install.sh, validate-skills.py
tests/
  test_skill_index.py       unit tests for catalog and router
  test_routing_benchmark.py harness sanity tests
  test_emit_routing_hint.py hook-script tests
  routing_benchmark.yaml    routing regression suite
docs/
  ROUTING_IMPROVEMENTS.md   per-PR router deltas
  SKILL_GRAPH.md            routing model and graph
  routing_baseline.json     benchmark baseline
  tooling-survey-2026.md    bioinformatics tooling survey (versions, GPU options, alternatives)
Makefile                    install, catalog, hook, benchmark, uninstall targets
```

## Development

```bash
python3 -m unittest discover tests              # unit tests
make benchmark                                  # routing regression vs baseline
python3 scripts/skill_index.py build            # rebuild catalog artifacts
```

Adding or modifying a skill:

1. Create or edit `skills/<name>/SKILL.md`. The YAML `name` field must match
   the directory name.
2. Add the skill to the relevant agent's `Mandatory Skill Usage` and
   `Task Recognition Patterns`.
3. Rebuild the catalog and run the test suite.
4. Add a benchmark row in `tests/routing_benchmark.yaml` if the skill is
   non-trivially discoverable by the router.

See [AGENTS.md](AGENTS.md) for structural conventions and
[docs/SKILL_GRAPH.md](docs/SKILL_GRAPH.md) for how the router scores and
composes skills.

## Compatibility

| Platform | Notes |
|---|---|
| Claude Code | Primary runtime; agents installed to `~/.claude/agents/`, skills to `~/.claude/skills/`. |
| Codex CLI | Agents installed to `~/.codex/agents/`; skills to `~/.codex/skills/`; hook uses `~/.codex/hooks.json` with `[features] codex_hooks = true` in `~/.codex/config.toml`. |
| Claude API | Agent markdown files can be loaded as system prompts. Skills remain readable as reference. |

## License

MIT. See [LICENSE](LICENSE).
