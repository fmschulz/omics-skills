# Contributing to Omics Skills

Thank you for your interest in contributing! This guide will help you add new skills, modify agents, or improve documentation.

---

## Table of Contents

- [Getting Started](#getting-started)
- [Adding a New Skill](#adding-a-new-skill)
- [Modifying Agents](#modifying-agents)
- [Testing Your Changes](#testing-your-changes)
- [Submitting Changes](#submitting-changes)
- [Style Guidelines](#style-guidelines)

---

## Getting Started

### Prerequisites

- Git
- Claude Code or Codex CLI
- Python 3 (for skills with dependencies)
- Basic understanding of bioinformatics or scientific workflows

### Setup Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/omics-skills.git
cd omics-skills

# Create a development branch
git checkout -b feature/your-feature-name

# Install in development mode (using symlinks)
./install.sh
```

---

## Adding a New Skill

### 1. Skill Structure

Each skill follows this structure:

```
skills/your-skill-name/
├── SKILL.md              # Required: Skill definition and instructions
├── docs/                 # Optional: Tool documentation
│   ├── tool1.md
│   └── tool2.md
├── summaries/            # Optional: Literature summaries
│   ├── README.md
│   └── 2026-paper-name.md
├── examples/             # Optional: Usage examples
│   └── example1.md
├── references/           # Optional: Reference materials
│   └── best-practices.md
└── requirements.txt      # Optional: Python dependencies
```

### 2. Create SKILL.md

The `SKILL.md` file is the core of your skill. Use this template:

```markdown
---
name: your-skill-name
description: Brief description of what this skill does. When to use it.
---

# Your Skill Name

## Instructions

Clear, step-by-step instructions for Claude to follow.

## Quick Reference

| Task | Action |
|------|--------|
| Task 1 | How to do it |
| Task 2 | How to do it |

## Input Requirements

- What files/data are needed
- What format they should be in
- Prerequisites

## Output

- What files/data are produced
- Where they are saved
- Format and structure

## Examples

### Example 1: Common Use Case

\```bash
# Commands to run
tool --option input.txt > output.txt
\```

**Expected output:**
\```
Output format example
\```

## Quality Gates

- [ ] Check 1: What to verify
- [ ] Check 2: What to verify

## Troubleshooting

**Issue**: Common problem
**Solution**: How to fix it

## References

- Tool documentation: URL
- Key papers: Citation
```

### 3. Add Documentation

Create `docs/` directory with tool-specific documentation:

```markdown
# Tool Name

## Installation

How to install the tool

## Usage

Common usage patterns

## Parameters

Key parameters explained

## Examples

Practical examples
```

### 4. Add Literature Summaries (Optional)

For bio-* skills, add literature summaries in `summaries/`:

```markdown
# Paper Title (Year)

**Journal**: Journal Name
**DOI**: 10.xxxx/xxxxx

## Key Points

- Main finding 1
- Main finding 2

## Methods

Brief method description

## Relevance

Why this paper matters for this skill
```

### 5. Update Agent Mappings

Edit the relevant agent file(s) in `agents/`:

```markdown
### Your Skill Category

**For [task type], use:**
- `/your-skill-name` - Description of what it does
  - Use for: Specific use cases
  - Outputs: What it produces
```

Add to the decision tree:

```markdown
├─ Need [something]?
│   └─> /your-skill-name
```

Add keyword triggers:

```markdown
- **"keyword1", "keyword2"** → `/your-skill-name`
```

---

## Modifying Agents

### Agent Structure

Agents are markdown files that define:
1. **Persona** - Role and expertise
2. **Core Principles** - Guiding philosophy
3. **Mandatory Skill Usage** - When to use which skills
4. **Workflow Decision Tree** - How to orchestrate skills
5. **Task Recognition Patterns** - Keyword triggers
6. **Communication Style** - How to interact with users

### Making Changes

1. **Edit agent file** in `agents/`
2. **Test with Claude Code**:
   ```bash
   claude --agent agents/your-agent.md
   ```
3. **Verify skill mappings** are correct
4. **Update documentation** in `agents/README.md`

### Best Practices

- Keep skill descriptions concise (1-2 sentences)
- Use clear keywords for pattern matching
- Provide concrete examples
- Explain the "why" not just the "what"

---

## Testing Your Changes

### 1. Test Repository Structure

```bash
./test-install.sh
```

### 2. Test Installation

```bash
# Clean install
make uninstall
make install

# Verify
make status
make validate
```

### 3. Test Agent Invocation

```bash
# Test with Claude Code
claude --agent your-agent

# Test skill loading
claude --list-skills
```

### 4. Test Skill Functionality

Create a test case:

```bash
# In a test directory
echo "Test input" > test.txt

# Invoke Claude with agent
claude --agent omics-scientist

# In Claude session, trigger your skill
# Verify expected behavior
```

### 5. Test Cross-Platform

```bash
# Test with Codex (if available)
codex --system-prompt ~/.codex/agents/your-agent.md
```

---

## Submitting Changes

### 1. Pre-submission Checklist

- [ ] `./test-install.sh` passes
- [ ] `make validate` passes
- [ ] New skill has `SKILL.md`
- [ ] Agent mappings updated
- [ ] Documentation added
- [ ] Examples provided
- [ ] Tested with Claude Code
- [ ] README.md updated (if adding new skill)

### 2. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add your-skill-name for [purpose]

- Created SKILL.md with instructions
- Added documentation in docs/
- Updated omics-scientist agent mappings
- Added keyword triggers
- Tested with Claude Code"
```

### 3. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create pull request on GitHub
# Include:
# - Description of changes
# - Why this change is needed
# - How to test it
# - Screenshots/examples if applicable
```

---

## Style Guidelines

### Markdown Style

- Use ATX-style headers (`#` not `===`)
- Use fenced code blocks with language tags
- Use tables for structured data
- Use bullet points for lists
- Include blank lines between sections

### Skill Naming

- Use lowercase with hyphens: `bio-skill-name`
- Start with category prefix: `bio-`, `viz-`, etc.
- Be descriptive: `bio-reads-qc-mapping` not `bio-reads`
- Avoid abbreviations in skill names

### Documentation Style

- Write in imperative mood ("Do this" not "You should do this")
- Be concise and precise
- Include examples for complex concepts
- Use code blocks for commands
- Provide expected outputs

### Agent Style

- Use clear section headers
- Include decision trees and flowcharts (ASCII)
- Provide keyword mappings
- Show example interactions
- Explain scientific rationale

---

## Skill Design Principles

### 1. Single Responsibility

Each skill should do one thing well:

- ✅ Good: `bio-reads-qc-mapping` - QC and mapping
- ❌ Bad: `bio-everything` - QC, assembly, annotation

### 2. Clear Boundaries

Define clear inputs and outputs:

```markdown
Input: FASTQ files
Process: Quality control and mapping
Output: BAM files, QC reports
```

### 3. Composability

Skills should work together:

```
bio-reads-qc-mapping → bio-assembly-qc → bio-gene-calling
```

### 4. Quality Gates

Include validation checks:

```markdown
## Quality Gates

- [ ] Read quality score >Q30
- [ ] Adapter contamination <5%
- [ ] Sufficient depth of coverage
```

### 5. Reproducibility

Ensure reproducible results:

- Document tool versions
- Specify exact parameters
- Use containerization when possible
- Track provenance

---

## Agent Design Principles

### 1. Domain Expertise

Agents should embody expert knowledge:

```markdown
## Persona

You are an expert computational biologist...
```

### 2. Clear Decision Logic

Provide unambiguous decision trees:

```markdown
├─ Have Raw Reads?
│   └─> /bio-reads-qc-mapping
│       ├─ Need Assembly?
│       │   └─> /bio-assembly-qc
```

### 3. Keyword Recognition

Map natural language to skills:

```markdown
- **"raw reads", "fastq", "QC"** → `/bio-reads-qc-mapping`
```

### 4. Example Interactions

Show how the agent responds:

```markdown
**User**: "I have bacterial reads"
**Agent**: "I'll use /bio-reads-qc-mapping..."
```

---

## Common Pitfalls to Avoid

### ❌ Don't

- Create skills that overlap significantly
- Hardcode file paths
- Skip documentation
- Forget to update agent mappings
- Ignore quality gates
- Write overly complex skills

### ✅ Do

- Keep skills focused and modular
- Use relative paths or parameters
- Document everything
- Update all relevant agents
- Include validation steps
- Favor simplicity

---

## Getting Help

- **Questions**: Open a GitHub issue
- **Discussion**: Use GitHub Discussions
- **Bug Reports**: Open an issue with:
  - Output of `make status`
  - Steps to reproduce
  - Expected vs actual behavior

---

## Recognition

Contributors will be acknowledged in:
- README.md contributor section
- Release notes
- Git commit history

Thank you for contributing to Omics Skills!
