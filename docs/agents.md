# Agents

An agent is a Markdown system prompt. It sets a role, the skills to use, and a few quality gates. Claude Code or Codex loads the prompt; the agent runs nothing by itself. Each agent lists its skills in one `## Skills` table, which the [router](routing.md) also reads.

| Agent | Use it for | Common first skills |
|---|---|---|
| [`omics-scientist`](https://github.com/fmschulz/omics-skills/blob/main/agents/omics-scientist.md) | Reads, assemblies, MAGs, annotation, taxonomy, phylogenomics, viral discovery, public database records, project setup, biological interpretation, notebooks and figures. | `omics-pipeline`, `bioinformatics-project`, `bio-logic`, `polars-dovmed`, `beautiful-data-viz` |
| [`literature-expert`](https://github.com/fmschulz/omics-skills/blob/main/agents/literature-expert.md) | Literature and preprint search, DOI and citation metadata, and citation impact. | `polars-dovmed`, `preprint-search`, `crossref-lookup` |
| [`science-writer`](https://github.com/fmschulz/omics-skills/blob/main/agents/science-writer.md) | Proposal review, evaluation of AI-scientist output, methods sections, and evidence checks. It sends manuscript prose to `academic-writing` with `stop-slop` and manuscript review to `nelli-paper-review`, which come from other repositories. | `proposal-review`, `ai-scientist-evaluator`, `bio-workflow-methods-docwriter`, `bio-logic` |

The `omics-scientist` pipeline skills are hidden stages. The agent starts them through `omics-pipeline`, then reads the stage file; see [Skills](skills.md).

When the right agent is not obvious, ask the [router](routing.md). `--agent` limits the answer to one agent:

```bash
python3 scripts/skill_index.py route --agent omics-scientist "annotate viral contigs and compare relatives"
```
