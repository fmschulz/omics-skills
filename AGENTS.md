# AGENTS.md

Guidance for AI coding agents (Claude Code, Cursor, Copilot) working in this repository.

---

## Repository overview

5 agents and 36 skills covering bioinformatics, literature discovery, scientific writing, and data visualization. Runs under Claude Code and the Codex CLI.

Layout:
- `agents/` — 5 agent definitions (markdown)
- `skills/` — skill directories; each has a `SKILL.md`
- `scripts/` — router, catalog builder, hook, installer, benchmark
- `tests/` — unit tests + routing benchmark
- `catalog/` — generated routing artifacts (`catalog.json`, `relationships.json`, `routing.json`)
- `docs/` — routing model, PR-by-PR deltas, benchmark baseline
- `Makefile` — install, catalog, hook, benchmark, uninstall targets

Install: `make install` symlinks agents and skills into `~/.claude/` and `~/.codex/`.

---

## Default Workflow Selection

When working in this repository without a specialized agent prompt, do not choose skills ad hoc.

Start with the catalog:

```bash
python3 scripts/skill_index.py route "<task>"
```

Use the returned agent, primary skills, and suggested order as the default workflow. Then open the referenced agent file in `agents/` and the referenced `SKILL.md` files before proceeding. Only deviate from the returned path when the request clearly falls outside the suggested workflow.

For installed environments outside the repository checkout, use:

```bash
python3 ~/.agents/omics-skills/skill_index.py route "<task>"
```

---

## Scientific Workflow Guardrails

For omics or scientific project work, agents must maintain an explicit reasoning loop instead of treating analysis steps as a linear pipeline.

1. **Hypothesis register**: before the first analysis step, create at least 5 distinct working hypotheses or explanations. Include technical artifacts and null explanations alongside biological mechanisms. If fewer than 5 are plausible, state why and add discriminating negative controls or failure modes.
2. **Intermediate reflection**: after each major intermediate result or QC gate, write a short reflection covering what was observed, whether the result passed QC, which hypotheses gained or lost support, what alternative explanations remain, and the next discriminating check.
3. **Literature context**: after the initial hypothesis register and after any unexpected, central, or final finding, run an additional literature search using `polars-dovmed` or another appropriate literature-search skill. Use broad synonym-aware queries, summarize the relevant evidence with DOI/PMCID when available, and state whether the literature supports, contradicts, or narrows each leading hypothesis.
4. **Hypothesis revision**: revise and rank the hypothesis register as evidence accumulates. Do not silently discard hypotheses; mark them as supported, weakened, ruled out, or unresolved with the evidence that changed the status. Keep at least 5 active hypotheses while the project is exploratory; generate replacements when hypotheses are ruled out.
5. **Final synthesis**: final reports must include hypotheses considered, intermediate reflections, literature context, revised hypothesis ranking, and the next experiments or analyses that would best separate remaining alternatives.

These guardrails apply to agent prompts, skill instructions, examples, and documentation added or edited in this repository.

---

## Literature-Derived Discovery Guardrails

Omics agents must actively ask what is biologically interesting in the data. Do not stop at "workflow completed", "annotation complete", or "QC passed" when the user has provided genomes, contigs, MAGs, viral genomes, proteins, or annotations.

1. **Infer the biological context first**: use the available taxonomy, marker genes, genome statistics, sequence similarity, and QC evidence to infer the likely organism, virus group, sample context, and closest plausible references.
2. **Build a literature-derived analysis playbook**: before deciding what is "interesting", search the relevant literature for that inferred group and summarize what scientists typically analyze, which comparison sets they use, which features/outliers they report, and which tools or markers are considered appropriate. Prefer review papers, recent primary studies, and benchmark/tool papers for the same clade or data type.
3. **Choose methods from that playbook**: select comparative, phylogenetic, annotation, structural, statistical, and visualization analyses because they match the literature and the data, not because a fixed global checklist says so. Document why each chosen analysis is appropriate and which plausible analyses were skipped.
4. **Compare like with like**: identify close relatives or relevant reference sets using literature-supported methods for the inferred group. For example, do not apply a phage-oriented clustering workflow to NCLDV-style giant viruses unless the literature supports it for that case.
5. **Search for outliers and candidate discoveries**: compare query results to the literature-derived expectations and reference set. Report candidate discoveries, unusual absences, expansions, contractions, compositional outliers, topology outliers, annotation conflicts, and high-value unknowns only after separating them from conserved lineage features and likely artifacts.
6. **Interesting-findings table**: every exploratory analysis report must include a table of candidate discoveries with evidence, confidence, comparison baseline, literature context, and follow-up tests. If nothing interesting is found, state the negative finding and the checks that make it credible.

These requirements apply to `omics-scientist` and to bioinformatics skills that produce annotations, viral calls, phylogenies, pangenomes, or final reports.

---

## Comparative Discovery Axes

When close relatives or a literature-supported reference set are available, agents must run the query against ALL of the following structural axes before declaring the analysis complete. The *categories* within each axis (which markers count, which families matter, which neighborhoods are diagnostic) are inferred from the literature for the inferred group — they are not hardcoded. The axes themselves are mandatory; skipping one requires a written reason.

1. **Genome-property frontier**: place each query along the distribution of close relatives and group-level extremes reported in the literature for genome size, gene count, coding density, GC content, and any other group-relevant property. State where each query sits (median, tail, record-class) and cite the literature that defines the group's known range.
2. **Marker-gene census**: for the inferred group, enumerate the marker and machinery categories the literature treats as diagnostic (e.g., for nucleocytoplasmic large DNA viruses: replication, transcription, translation-related, packaging, capsid, chromatin/structural; for prokaryotes: ribosomal proteins, RNA polymerase, single-copy core). For each query and each relative, report presence/absence and copy number per category in a side-by-side table. Negative findings (expected marker absent) are first-class results.
3. **Per-family copy-number (expansion / contraction)**: build a Pfam/InterPro/orthogroup × genome matrix covering queries and relatives. Flag query-specific families, missing-expected families, expansions (query copies >> relative median), and contractions. Rank by absolute and fold differences.
4. **Synteny and conserved neighborhoods**: identify conserved gene neighborhoods (≥2 collinear orthologs in ≥2 relatives) and compare intergenic spacing, gene order, and local copy number between query and relatives. Flag conserved pairs, broken synteny, and unusual spacing or expansions.
5. **Non-coding RNA census**: explicitly screen each assembly for tRNA, rRNA, and other ncRNA classes appropriate to the inferred group, using `tRNAscan-SE` for tRNAs and Infernal `cmsearch` against domain-appropriate Rfam covariance models for rRNAs (bacterial RF00177/RF02541/RF00001; archaeal RF01959/RF02540/RF00001; eukaryotic RF01960/RF02543/RF00002/RF00001). Report counts per class per genome and per relative. A credible negative (e.g., "Infernal `cmsearch --cut_ga` finds no rRNA at default thresholds; relaxed thresholds also fail") is a required result when nothing is found — silence is not acceptable.

Each axis must yield (a) a persisted comparison artifact (TSV/parquet) and (b) a short interpretation linking the result to the hypothesis register and the literature-derived playbook. The interesting-findings table must roll up signals across these axes and identify the comparison baseline used.

---

## Scientific Workflow Guardrails

For omics or scientific project work, agents must maintain an explicit reasoning loop instead of treating analysis steps as a linear pipeline.

1. **Hypothesis register**: before the first analysis step, create at least 5 distinct working hypotheses or explanations. Include technical artifacts and null explanations alongside biological mechanisms. If fewer than 5 are plausible, state why and add discriminating negative controls or failure modes.
2. **Intermediate reflection**: after each major intermediate result or QC gate, write a short reflection covering what was observed, whether the result passed QC, which hypotheses gained or lost support, what alternative explanations remain, and the next discriminating check.
3. **Literature context**: after the initial hypothesis register and after any unexpected, central, or final finding, run an additional literature search using `polars-dovmed` or another appropriate literature-search skill. Use broad synonym-aware queries, summarize the relevant evidence with DOI/PMCID when available, and state whether the literature supports, contradicts, or narrows each leading hypothesis.
4. **Hypothesis revision**: revise and rank the hypothesis register as evidence accumulates. Do not silently discard hypotheses; mark them as supported, weakened, ruled out, or unresolved with the evidence that changed the status. Keep at least 5 active hypotheses while the project is exploratory; generate replacements when hypotheses are ruled out.
5. **Final synthesis**: final reports must include hypotheses considered, intermediate reflections, literature context, revised hypothesis ranking, and the next experiments or analyses that would best separate remaining alternatives.

These guardrails apply to agent prompts, skill instructions, examples, and documentation added or edited in this repository.

---

## Literature-Derived Discovery Guardrails

Omics agents must actively ask what is biologically interesting in the data. Do not stop at "workflow completed", "annotation complete", or "QC passed" when the user has provided genomes, contigs, MAGs, viral genomes, proteins, or annotations.

1. **Infer the biological context first**: use the available taxonomy, marker genes, genome statistics, sequence similarity, and QC evidence to infer the likely organism, virus group, sample context, and closest plausible references.
2. **Build a literature-derived analysis playbook**: before deciding what is "interesting", search the relevant literature for that inferred group and summarize what scientists typically analyze, which comparison sets they use, which features/outliers they report, and which tools or markers are considered appropriate. Prefer review papers, recent primary studies, and benchmark/tool papers for the same clade or data type.
3. **Choose methods from that playbook**: select comparative, phylogenetic, annotation, structural, statistical, and visualization analyses because they match the literature and the data, not because a fixed global checklist says so. Document why each chosen analysis is appropriate and which plausible analyses were skipped.
4. **Compare like with like**: identify close relatives or relevant reference sets using literature-supported methods for the inferred group. For example, do not apply a phage-oriented clustering workflow to NCLDV-style giant viruses unless the literature supports it for that case.
5. **Search for outliers and candidate discoveries**: compare query results to the literature-derived expectations and reference set. Report candidate discoveries, unusual absences, expansions, contractions, compositional outliers, topology outliers, annotation conflicts, and high-value unknowns only after separating them from conserved lineage features and likely artifacts.
6. **Interesting-findings table**: every exploratory analysis report must include a table of candidate discoveries with evidence, confidence, comparison baseline, literature context, and follow-up tests. If nothing interesting is found, state the negative finding and the checks that make it credible.

These requirements apply to `omics-scientist` and to bioinformatics skills that produce annotations, viral calls, phylogenies, pangenomes, or final reports.

---

## Comparative Discovery Axes

When close relatives or a literature-supported reference set are available, agents must run the query against ALL of the following structural axes before declaring the analysis complete. The *categories* within each axis (which markers count, which families matter, which neighborhoods are diagnostic) are inferred from the literature for the inferred group — they are not hardcoded. The axes themselves are mandatory; skipping one requires a written reason.

1. **Genome-property frontier**: place each query along the distribution of close relatives and group-level extremes reported in the literature for genome size, gene count, coding density, GC content, and any other group-relevant property. State where each query sits (median, tail, record-class) and cite the literature that defines the group's known range.
2. **Marker-gene census**: for the inferred group, enumerate the marker and machinery categories the literature treats as diagnostic (e.g., for nucleocytoplasmic large DNA viruses: replication, transcription, translation-related, packaging, capsid, chromatin/structural; for prokaryotes: ribosomal proteins, RNA polymerase, single-copy core). For each query and each relative, report presence/absence and copy number per category in a side-by-side table. Negative findings (expected marker absent) are first-class results.
3. **Per-family copy-number (expansion / contraction)**: build a Pfam/InterPro/orthogroup × genome matrix covering queries and relatives. Flag query-specific families, missing-expected families, expansions (query copies >> relative median), and contractions. Rank by absolute and fold differences.
4. **Synteny and conserved neighborhoods**: identify conserved gene neighborhoods (≥2 collinear orthologs in ≥2 relatives) and compare intergenic spacing, gene order, and local copy number between query and relatives. Flag conserved pairs, broken synteny, and unusual spacing or expansions.
5. **Non-coding RNA census**: explicitly screen each assembly for tRNA, rRNA, and other ncRNA classes appropriate to the inferred group, using `tRNAscan-SE` for tRNAs and Infernal `cmsearch` against domain-appropriate Rfam covariance models for rRNAs (bacterial RF00177/RF02541/RF00001; archaeal RF01959/RF02540/RF00001; eukaryotic RF01960/RF02543/RF00002/RF00001). Report counts per class per genome and per relative. A credible negative (e.g., "Infernal `cmsearch --cut_ga` finds no rRNA at default thresholds; relaxed thresholds also fail") is a required result when nothing is found — silence is not acceptable.

Each axis must yield (a) a persisted comparison artifact (TSV/parquet) and (b) a short interpretation linking the result to the hypothesis register and the literature-derived playbook. The interesting-findings table must roll up signals across these axes and identify the comparison baseline used.

---

## Working with Skills

### Skill Directory Structure

```
skills/
  {skill-name}/           # kebab-case directory name
    SKILL.md              # Required: skill definition with YAML frontmatter
    docs/                 # Optional: tool documentation
      {tool-name}.md
    summaries/            # Optional: literature summaries (bio-* skills)
      README.md
      YYYY-paper-title.md
    examples/             # Optional: usage examples
    references/           # Optional: reference materials
    requirements.txt      # Optional: Python dependencies
```

### Naming Conventions

- **Skill directory**: kebab-case with prefix (e.g., `bio-reads-qc-mapping`, `scientific-writing`)
- **Skill prefixes**:
  - `bio-*` - Bioinformatics workflows
  - `scientific-writing`, `polars-dovmed`, `agent-browser` - Writing/research
- `beautiful-data-viz`, `plotly-dashboard-skill`, `notebooks` - Visualization (marimo-first notebooks; Jupyter supported)
- **SKILL.md**: Always uppercase, always this exact filename
- **SKILL frontmatter `name`**: lowercase letters/numbers and hyphens only, no consecutive hyphens, <=64 chars, and must match the directory name
- **Documentation**: markdown files in `docs/`; prefer lowercase with hyphens, `README.md` acceptable for overviews

### SKILL.md Format

```markdown
---
name: skill-name
description: One sentence describing what this skill does. Include when to use it (e.g., "Use when processing raw sequencing reads").
---

# Skill Title

Brief overview of what the skill does.

## Instructions

Clear, step-by-step instructions for Claude to follow.

## Quick Reference

| Task | Action |
|------|--------|
| Task 1 | How to do it |

## Input Requirements

- What files/data are needed
- Format requirements

## Output

- What gets produced
- Where it's saved

## Quality Gates

- [ ] Validation check 1
- [ ] Validation check 2

## Examples

### Example 1: Common Use Case

\```bash
command --option input.txt > output.txt
\```

## Troubleshooting

**Issue**: Common problem
**Solution**: How to fix it
```

### Best Practices for Context Efficiency

Skills are loaded on-demand. To minimize context usage:

- **Keep SKILL.md under 500 lines** - put detailed docs in `docs/` directory
- **Write specific descriptions** - helps agents know when to activate the skill
- **Use progressive disclosure** - reference `docs/`, `summaries/`, `references/` files
- **Separate concerns** - tool docs in `docs/`, literature in `summaries/`, examples in `examples/`
- **Link explicitly** - include full relative paths (e.g., `[Tool Docs](docs/tool-name.md)`)

### Documentation Structure

**docs/** - Tool-specific documentation
```markdown
# Tool Name

## Installation
## Usage
## Parameters
## Examples
```

**summaries/** - Literature summaries (bio-* skills only)
```markdown
# Paper Title (Year)

**Journal**: Journal Name
**DOI**: 10.xxxx/xxxxx

## Key Points
## Methods
## Relevance
```

**examples/** - Usage examples
```markdown
# Example: Use Case Name

## Scenario
## Commands
## Expected Output
```

---

## Working with Agents

### Agent Structure

Agents are markdown files that define:
1. **Persona** - Expert role and domain
2. **Core Principles** - Guiding philosophy
3. **Skill Lookup** - Short catalog-first lookup step before manual skill selection
4. **Mandatory Skill Usage** - When to use which skills
5. **Workflow Decision Tree** - Skill orchestration logic
6. **Task Recognition Patterns** - Keyword → skill mappings
7. **Communication Style** - How to interact with users

### Agent File Structure

```markdown
# Agent Name

## Persona

You are an expert [domain] specializing in [specific areas]...

## Core Principles

1. Principle 1
2. Principle 2

## Skill Lookup

Run the shared catalog first:
`python3 ~/.agents/omics-skills/skill_index.py route "<task>" --agent <agent-name>`

## Mandatory Skill Usage

### Category 1

**When working with X, use:**
- `/skill-name` - Description
  - Use for: Specific scenarios
  - Outputs: What it produces

### Category 2

...

## Workflow Decision Tree

\```
START
  │
  ├─ Condition?
  │   └─> /skill-name
  │       └─> /next-skill
\```

## Task Recognition Patterns

- **"keyword1", "keyword2"** → `/skill-name`

## Communication Style

Guidelines for how to communicate with users

## Example Interactions

**User**: Example request
**Agent**: Example response with skill invocation
```

### Naming Conventions

- **Agent files**: kebab-case (e.g., `omics-scientist.md`, `science-writer.md`)
- **Four agents**:
  - `omics-scientist.md` - Bioinformatics workflows (14 bio-* skills)
  - `literature-expert.md` - Literature discovery, preprints, and citation lookup
  - `science-writer.md` - Scientific writing, revision, and peer review
  - `dataviz-artist.md` - Visualization (5 viz skills)

### Agent Design Principles

1. **Single Responsibility** - Each agent has a clear domain
2. **Skill Orchestration** - Agents compose skills into workflows
3. **Decision Logic** - Clear decision trees for skill selection
4. **Keyword Mapping** - Natural language → skill activation
5. **Quality Gates** - Validation at each workflow step
6. **Example Driven** - Show concrete interaction patterns

---

## Creating a New Skill

### 1. Create Directory Structure

```bash
mkdir -p skills/your-skill-name/{docs,summaries,examples,references}
touch skills/your-skill-name/SKILL.md
```

### 2. Write SKILL.md

Use the template above. Key sections:
- YAML frontmatter with `name` and `description`
- Clear instructions for Claude
- Input/output specifications
- Quality gates for validation
- Examples and troubleshooting

### 3. Add Documentation (Optional)

- `docs/` - Tool-specific documentation
- `summaries/` - Literature summaries (for bio-* skills)
- `examples/` - Usage examples
- `references/` - Reference materials

### 4. Update Agent Mappings

Edit relevant agent file(s) in `agents/`:
- Add skill to "Mandatory Skill Usage" section
- Add to workflow decision tree
- Add keyword triggers in "Task Recognition Patterns"

### 5. Update README.md

Add skill to the agent → skills mapping section.

### 6. Test

```bash
# Test repository structure
make test

# Test installation
make install
make status

# Test agent invocation
claude --agent omics-scientist
# Try triggering your new skill
```

---

## Modifying an Existing Skill

### 1. Read Current Implementation

```bash
cat skills/{skill-name}/SKILL.md
ls -la skills/{skill-name}/
```

### 2. Make Changes

- **SKILL.md** - Update instructions, add examples
- **docs/** - Add/update tool documentation
- **summaries/** - Add literature references (bio-* skills)

### 3. Maintain Structure

- Keep YAML frontmatter intact
- Preserve section headers
- Update quality gates if logic changes
- Add troubleshooting for new edge cases

### 4. Test Changes

```bash
# Symlinks auto-update (default install method)
# Test by invoking agent and using the skill

# If installed via copies:
make install INSTALL_METHOD=copy
```

---

## Modifying an Agent

### 1. Identify Which Agent

- `omics-scientist.md` - Bioinformatics workflows
- `literature-expert.md` - Literature discovery, preprints, and DOI lookup
- `science-writer.md` - Manuscript writing, revision, and review
- `dataviz-artist.md` - Visualization, notebooks, dashboards

### 2. Edit Agent File

```bash
vim agents/{agent-name}.md
```

### 3. Key Sections to Update

- **Mandatory Skill Usage** - When adding/removing skills
- **Workflow Decision Tree** - When changing orchestration logic
- **Task Recognition Patterns** - When adding new keywords
- **Example Interactions** - When adding new workflows

### 4. Test Changes

```bash
# Symlinks auto-update
claude --agent {agent-name}

# Try various triggers to test keyword mappings
```

---

## Installation for End Users

Document these methods in README.md:

### Method 1: Makefile (Recommended)

```bash
git clone https://github.com/user/omics-skills.git
cd omics-skills
make install        # Installs to ~/.claude/ and ~/.codex/
make status         # Verify installation
```

### Method 2: Shell Scripts

```bash
scripts/install.sh  # Alternative to Makefile
```

### What Gets Installed

- **Agents** → `~/.claude/agents/` and `~/.codex/agents/` (5 files)
- **Skills** → `~/.agents/skills/` (31 directories)
- **Claude skills link** → `~/.claude/skills` → `~/.agents/skills`
- **Codex skills link** → `~/.codex/skills` → `~/.agents/skills`
- **Symlinks** by default (auto-updates with `git pull`)

---

## Testing Procedures

### Repository Structure Test

```bash
make test
# Or: scripts/test-install.sh
```

**Validates:**
- Repository directory structure
- All agents present
- Critical skills present
- Installation scripts executable
- Installation status

### Installation Test

```bash
make install
make status
make validate
```

### Agent Invocation Test

```bash
claude --agent omics-scientist
# Test skill triggering
# Verify workflow orchestration
```

---

## Code Quality Standards

### Skill Requirements

- [ ] SKILL.md has valid YAML frontmatter
- [ ] Description includes "when to use" guidance
- [ ] Instructions are clear and step-by-step
- [ ] Quality gates defined
- [ ] Examples provided
- [ ] Troubleshooting section present
- [ ] Documentation links work (if using docs/)

### Agent Requirements

- [ ] Persona clearly defined
- [ ] All used skills documented in "Mandatory Skill Usage"
- [ ] Decision tree covers all skill paths
- [ ] Keyword mappings cover the skill's expected triggers
- [ ] Example interactions show real workflows
- [ ] Quality gates specified for workflows

### Documentation Standards

- Use markdown format
- Include code examples with language tags
- Provide both simple and complex examples
- Document edge cases
- Link to external resources with full URLs

---

## Common Patterns

### Pattern 1: Bio-* Workflow Skills

Bio-* skills form sequential workflows:

```
bio-reads-qc-mapping → bio-assembly-qc → bio-gene-calling → bio-annotation
```

**Structure:**
- Input: Previous step's output
- Process: Single bioinformatics tool/workflow
- Output: Files + QC reports
- Quality gates: Validation thresholds

### Pattern 2: Universal Skills

Some skills are used across all agents:

- `bio-logic` - Scientific reasoning (used by the science agents)

### Pattern 3: Terminal Skills

Skills that produce final deliverables:

- `bio-stats-ml-reporting` - Generate final reports
- `scientific-writing` - Produce manuscripts
- `beautiful-data-viz` - Create publication figures

---

## Troubleshooting

### Skill Not Loading

**Issue**: Claude doesn't recognize the skill
**Check:**
1. SKILL.md has valid YAML frontmatter
2. `name` in frontmatter matches directory name
3. Skill installed via `make install`
4. Agent mapping includes the skill

### Agent Not Using Skill

**Issue**: Agent doesn't invoke skill when expected
**Check:**
1. Keywords in "Task Recognition Patterns"
2. Skill in "Mandatory Skill Usage" section
3. Skill in workflow decision tree
4. Test with explicit skill name mention

### Symlinks Broken

**Issue**: Symlinks don't point to correct location
**Fix:**
```bash
make uninstall
cd /correct/path/to/omics-skills
make install
```

---

## File Naming Reference

| Type | Convention | Example |
|------|-----------|---------|
| Skill directory | kebab-case with prefix | `bio-reads-qc-mapping` |
| Agent file | kebab-case | `omics-scientist.md` |
| SKILL.md | UPPERCASE | `SKILL.md` |
| Documentation | lowercase-hyphen .md preferred; `README.md` allowed | `docs/tool-name.md` |
| Summaries | YYYY-title.md | `summaries/2024-paper-name.md` |
| Scripts | kebab-case.sh | `scripts/install.sh` |
| Root docs | UPPERCASE | `README.md`, `INSTALL.md` |

---

## Quick Reference

### Adding a Skill
1. Create `skills/skill-name/SKILL.md`
2. Add docs/ and examples/ if needed
3. Update agent mapping in `agents/`
4. Run `make test`

### Modifying an Agent
1. Edit `agents/agent-name.md`
2. Update skill mappings, decision tree, keywords
3. Test with `claude --agent agent-name`

### Testing Changes
```bash
make test      # Validate structure
make install   # Install/update
make status    # Check installation
```

### Installation for Users
```bash
make install   # Primary method
make status    # Verify
```

---

When adding skills or modifying agents, preserve the YAML frontmatter shape, the `Mandatory Skill Usage` / `Task Recognition Patterns` / `Workflow Decision Tree` sections the router parses, and the `name`-matches-directory invariant enforced by `tests/test_skill_index.py`.
