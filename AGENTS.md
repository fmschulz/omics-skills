# AGENTS.md

This file provides guidance to AI coding agents (Claude Code, Cursor, Copilot, etc.) when working with code in this repository.

---

## Repository Overview

A curated collection of **3 expert agents** and **20 specialized skills** for bioinformatics, scientific writing, and data visualization. Compatible with **Claude Code** and **Codex CLI**.

**Structure:**
- `agents/` - 3 agent personas that orchestrate skills
- `skills/` - 20 specialized skills for omics workflows
- `scripts/` - Installation and testing utilities
- `Makefile` - Primary installation interface

**Installation:** Users run `make install` to symlink agents and skills to `~/.claude/` and `~/.codex/`

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

- **Skill directory**: kebab-case with prefix (e.g., `bio-reads-qc-mapping`, `science-writing`)
- **Skill prefixes**:
  - `bio-*` - Bioinformatics workflows
  - `science-writing`, `polars-dovmed`, `agent-browser` - Writing/research
  - `beautiful-data-viz`, `plotly-dashboard-skill`, `jupyter_notebook_ai_agents_skill` - Visualization
- **SKILL.md**: Always uppercase, always this exact filename
- **Documentation**: markdown files in `docs/`, lowercase with hyphens

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

- **Keep SKILL.md under 800 lines** - put detailed docs in `docs/` directory
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
3. **Mandatory Skill Usage** - When to use which skills
4. **Workflow Decision Tree** - Skill orchestration logic
5. **Task Recognition Patterns** - Keyword → skill mappings
6. **Communication Style** - How to interact with users

### Agent File Structure

```markdown
# Agent Name

## Persona

You are an expert [domain] specializing in [specific areas]...

## Core Principles

1. Principle 1
2. Principle 2

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
- **Three agents**:
  - `omics-scientist.md` - Bioinformatics workflows (14 bio-* skills)
  - `science-writer.md` - Scientific writing (5 writing skills)
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
- `science-writer.md` - Manuscript writing, literature review
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

- **Agents** → `~/.claude/agents/` and `~/.codex/agents/` (3 files)
- **Skills** → `~/.claude/skills/` and `~/.codex/skills/` (20 directories)
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
- [ ] Keyword mappings comprehensive
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

- `bio-logic` - Scientific reasoning (used by all 3 agents)

### Pattern 3: Terminal Skills

Skills that produce final deliverables:

- `bio-stats-ml-reporting` - Generate final reports
- `science-writing` - Produce manuscripts
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
| Documentation | lowercase, .md | `docs/tool-name.md` |
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

**Note**: This repository emphasizes reproducibility, quality gates, and modular composition. When adding skills or modifying agents, maintain these principles.
