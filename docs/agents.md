# Agent

The pack ships one agent, [`literature-expert`](https://github.com/fmschulz/omics-skills/blob/main/agents/literature-expert.md). An agent is a Markdown system prompt: it sets a role, the skills to use, and a few quality gates. Claude Code or Codex loads the prompt; the agent runs nothing by itself.

| Agent | Use it for | Skills |
|---|---|---|
| `literature-expert` | Literature search in PMC and bioRxiv full text, DOI and citation metadata, citation counts, and triage of evidence quality. It keeps a long search out of the main session's context. | `polars-dovmed`, `crossref-lookup`, `bio-logic` |

Pipeline work needs no agent. A session loads `omics-pipeline`, which holds the rules the former `omics-scientist` agent carried: discovery from the literature, the hypothesis register, the comparative axes, and the contents of the final report. See [Skills](skills.md).

Start the agent with `claude --agent literature-expert`, or ask Codex to delegate to `literature-expert`.
