# Omics Skills

> **Specialized AI agents and skills for bioinformatics, scientific writing, and data visualization**

A curated collection of domain-expert agents and battle-tested skills for computational biology workflows. Compatible with **Claude Code** and **Codex CLI**.

[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-Compatible-blue)](https://agentskills.io)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-green)](https://code.claude.com)
[![Codex CLI](https://img.shields.io/badge/Codex%20CLI-Compatible-green)](https://developers.openai.com/codex)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agents](https://img.shields.io/badge/Agents-3-blue)](#the-three-agents)
[![Skills](https://img.shields.io/badge/Skills-24-blue)](#agent--skills-mapping)

**Quick Links:** [Installation](#installation) • [Agents](#the-three-agents) • [Skills Mapping](#agent--skills-mapping) • [Examples](#example-workflows) • [Distribution](DISTRIBUTION.md)

---

## What This Repository Provides

**3 Expert Agents** that orchestrate **24 specialized skills** for end-to-end omics analysis, scientific communication, data visualization, and agent tooling.

```
Raw Reads → Assembly → Annotation → Analysis → Manuscript → Publication
    └─────────────────────────────────────────────────────────┘
              Fully automated with quality gates
```

---

## The Three Agents

### 🧬 Omics Scientist
**Expert computational biologist** for genomics, metagenomics, and phylogenomics workflows.

**Use when you need to:**
- Process sequencing data (Illumina, Nanopore, PacBio)
- Assemble genomes or metagenomes
- Recover MAGs from metagenomic assemblies
- Perform functional annotation and taxonomy
- Build phylogenetic trees
- Conduct comparative genomics
- Analyze viral sequences or protein structures
- Query JGI databases for metadata discovery and data retrieval (GOLD, IMG, Mycocosm, Phytozome)

**Core Skills (16):**
- `bio-logic` — Scientific reasoning and hypothesis formation
- `bio-foundation-housekeeping` — Project scaffolding with reproducible environments
- `bio-reads-qc-mapping` — Read QC, trimming, and mapping
- `bio-assembly-qc` — Genome/metagenome assembly
- `bio-binning-qc` — MAG recovery and quality assessment
- `bio-gene-calling` — Gene prediction for prokaryotes/eukaryotes/viruses
- `bio-annotation` — Functional annotation via BLAST/DIAMOND/hmmer
- `bio-phylogenomics` — Phylogenetic tree construction
- `bio-protein-clustering-pangenome` — Pangenome analysis
- `bio-structure-annotation` — AlphaFold/ESMFold structure prediction
- `bio-viromics` — Viral contig detection and classification
- `bio-stats-ml-reporting` — Statistical analysis and ML model training
- `bio-workflow-methods-docwriter` — Generate Methods sections from pipelines
- `bio-prefect-dask-nextflow` — Workflow orchestration
- `jgi-lakehouse` — Metadata discovery and data retrieval from JGI's GOLD, IMG, Mycocosm, and Phytozome databases via Dremio SQL
- `tracking-taxonomy-updates` — Track and reconcile taxonomy updates across NCBI/GTDB/ICTV

---

### ✍️ Science Writer
**Expert scientific writer** for publication-quality manuscripts and literature reviews.

**Use when you need to:**
- Write or edit manuscript sections (Abstract, Intro, Methods, Results, Discussion)
- Conduct comprehensive literature reviews
- Evaluate research methodology and evidence quality
- Validate citations and format references
- Document computational workflows for Methods sections
- Review manuscripts for rigor and clarity

**Core Skills (4):**
- `bio-logic` — Evaluate methodology, assess evidence, critique claims
- `polars-dovmed` — Search 2.4M+ PubMed Central papers
- `science-writing` — Publication-quality manuscripts with DOI validation
- `bio-workflow-methods-docwriter` — Reproducible Methods from workflow artifacts
- `agent-browser` — Web scraping for databases and supplementary materials

---

### 📊 DataViz Artist
**Expert data visualization specialist** for publication-quality figures and interactive dashboards.

**Use when you need to:**
- Create publication-ready figures for papers
- Build interactive dashboards for data exploration
- Generate exploratory data analysis notebooks
- Design beautiful, accessible visualizations
- Ensure reproducibility with documented workflows

**Core Skills (5):**
- `notebook-ai-agents-skill` — Marimo-first analysis notebooks with KISS structure
- `beautiful-data-viz` — Publication-quality matplotlib/seaborn plots
- `plotly-dashboard-skill` — Production-ready Plotly Dash dashboards
- `agent-browser` — Web scraping and screenshot capture

---

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/omics-skills.git
cd omics-skills

# Install agents and skills (creates symlinks)
make install

# Check installation status
make status
```

**Common commands:**
- `make install` - Install for both Claude Code and Codex
- `make install-claude` - Install for Claude Code only
- `make install-codex` - Install for Codex only
- `make status` - Check what's installed
- `make help` - View all options

**Installation options:**
- **Method**: Use `INSTALL_METHOD=copy` for copies instead of symlinks (default: symlink)
- **Verbosity**: Use `VERBOSE=1` to show each file being installed (default: compact progress)
- **Color**: Use `NO_COLOR=1` to disable colors (auto-detected for non-TTY)

**What gets installed:**
- **Agents** → `~/.claude/agents/` and `~/.codex/agents/` (3 files)
- **Skills** → `~/.agents/skills/` (24 directories)
- **Claude skills link** → `~/.claude/skills` → `~/.agents/skills`

**Examples:**
```bash
make install                           # Default: symlinks, compact output
make install VERBOSE=1                 # Show each file being installed
make install INSTALL_METHOD=copy       # Copy files instead of symlinks
make install NO_COLOR=1                # Disable colors
```

> 📖 **[Complete Installation Guide](INSTALL.md)** - Detailed instructions, troubleshooting, manual installation, and advanced options. Shell scripts available in `scripts/` for Makefile-free installation.

---

## Quick Start

### Using with Claude Code

```bash
# After installation, invoke an agent
claude --agent omics-scientist

# Or specify other agents
claude --agent science-writer
claude --agent dataviz-artist

# For project-specific work
cd /path/to/your/project
claude --agent omics-scientist
```

### Using with Codex CLI

```bash
# Use agent as system prompt
codex --system-prompt ~/.codex/agents/omics-scientist.md

# Or add to Codex config
codex config set default_agent ~/.codex/agents/omics-scientist.md
```

**Verify installation:**
```bash
make status
make test  # Run validation tests
```

---

## Agent → Skills Mapping

```
┌────────────────────────┐
│   Omics Scientist      │
├────────────────────────┤
│ 16 skills (14 bio-*)   │
│ Focus: Workflows       │
└────────────────────────┘
         │
         ├──> bio-logic (reasoning)
         ├──> bio-foundation-housekeeping
         ├──> bio-reads-qc-mapping
         ├──> bio-assembly-qc
         ├──> bio-binning-qc
         ├──> bio-gene-calling
         ├──> bio-annotation
         ├──> bio-phylogenomics
         ├──> bio-protein-clustering-pangenome
         ├──> bio-structure-annotation
         ├──> bio-viromics
         ├──> bio-stats-ml-reporting
         ├──> bio-workflow-methods-docwriter
         ├──> bio-prefect-dask-nextflow
         ├──> jgi-lakehouse (GOLD/IMG/Phytozome)
         └──> tracking-taxonomy-updates

┌────────────────────────┐
│   Science Writer       │
├────────────────────────┤
│ 5 writing skills       │
│ Focus: Communication   │
└────────────────────────┘
         │
         ├──> bio-logic (evidence evaluation)
         ├──> polars-dovmed (literature search)
         ├──> science-writing (manuscripts)
         ├──> bio-workflow-methods-docwriter
         └──> agent-browser (web research)

┌────────────────────────┐
│   DataViz Artist       │
├────────────────────────┤
│ 4 visualization skills │
│ Focus: Presentation    │
└────────────────────────┘
         │
         ├──> notebook-ai-agents-skill
         ├──> beautiful-data-viz
         ├──> plotly-dashboard-skill
         └──> agent-browser
```

---

## Example Workflows

### Bacterial Genome Analysis
```
Omics Scientist Agent
  1. bio-foundation-housekeeping → Set up project
  2. bio-reads-qc-mapping → QC raw reads
  3. bio-assembly-qc → Assemble genome
  4. bio-gene-calling → Predict genes
  5. bio-annotation → Functional annotation
  6. bio-phylogenomics → Phylogenetic placement
  7. bio-stats-ml-reporting → Generate report

Science Writer Agent
  8. bio-workflow-methods-docwriter → Document pipeline
  9. science-writing → Write manuscript sections
  10. polars-dovmed → Find supporting literature

DataViz Artist Agent
  11. notebook-ai-agents-skill → Create Marimo notebook
  12. beautiful-data-viz → Publication figures
```

### Literature Review & Meta-Analysis
```
Science Writer Agent
  1. polars-dovmed → Comprehensive literature search
  2. bio-logic → Evaluate evidence quality
  3. science-writing → Synthesize review manuscript

DataViz Artist Agent
  4. beautiful-data-viz → Create summary figures
  5. notebook-ai-agents-skill → Document analysis (Marimo)
```

### Interactive Dashboard for MAG Explorer
```
Omics Scientist Agent
  1. bio-binning-qc → Recover MAGs
  2. bio-annotation → Annotate genomes
  3. bio-stats-ml-reporting → Statistical summaries

DataViz Artist Agent
  4. plotly-dashboard-skill → Build interactive dashboard
  5. beautiful-data-viz → Static exports for presentations
```

---

## Repository Structure

```
omics-skills/
├── agents/                          # 3 expert agent personas
│   ├── omics-scientist.md          # Bioinformatics workflows
│   ├── science-writer.md           # Manuscript writing
│   ├── dataviz-artist.md           # Visualization design
│   └── docs/                        # Shared agent documentation
│       ├── ARCHITECTURE.md         # Agent design principles
│       ├── BIO-LOGIC_INTEGRATION.md
│       ├── EXAMPLES.md
│       ├── INDEX.md
│       ├── QUICK_REFERENCE.md
│       └── README.md
│
└── skills/                          # 24 specialized skills
    ├── bio-logic/                  # Scientific reasoning (shared)
    ├── bio-foundation-housekeeping/
    ├── bio-reads-qc-mapping/
    ├── bio-assembly-qc/
    ├── bio-binning-qc/
    ├── bio-gene-calling/
    ├── bio-annotation/
    ├── bio-phylogenomics/
    ├── bio-protein-clustering-pangenome/
    ├── bio-structure-annotation/
    ├── bio-viromics/
    ├── bio-stats-ml-reporting/
    ├── bio-workflow-methods-docwriter/
    ├── bio-prefect-dask-nextflow/
    ├── jgi-lakehouse/              # Query JGI GOLD/IMG/Phytozome
    ├── polars-dovmed/              # PubMed Central search
    ├── proposal-review/            # Decision-ready proposal review
    ├── science-writing/            # Manuscript generation
    ├── agent-browser/              # Web automation
    ├── get-api-docs/               # Current API docs via chub
    ├── notebook-ai-agents-skill/
    ├── beautiful-data-viz/
    ├── plotly-dashboard-skill/
    └── tracking-taxonomy-updates/
```

---

## Key Features

### Quality Gates
All workflows enforce validation checkpoints:
- **Read QC**: >Q30, <5% adapter contamination
- **Assembly**: N50, misassemblies, completeness
- **MAG QC**: >50% completeness, <10% contamination
- **Annotation**: >70% genes with functional assignments

### Reproducibility
- Containerized environments (Docker/Singularity)
- Parameter logging and provenance tracking
- Version-controlled workflows
- Pixi-managed Python environments

### Scientific Rigor
- Evidence-based decision making via `bio-logic`
- DOI validation for all citations
- Statistical best practices
- Reporting guideline compliance (CONSORT, STROBE, PRISMA)

### Design Excellence
- Publication-quality aesthetics
- Colorblind-safe palettes
- Accessibility compliance
- Export-ready formats (PDF, SVG, PNG)

---

## Compatibility

| Platform | Status | Notes |
|----------|--------|-------|
| **Claude Code** | ✅ Full support | Primary platform, use `--agent` flag |
| **Codex CLI** | ✅ Full support | Use `--system-prompt` or config integration |
| **Claude API** | ✅ Compatible | Load agents as system prompts |
| **Standalone** | ✅ Reference docs | Skills contain full documentation |

---

## Maintenance

### Updating

**With symlinks (default):**
```bash
git pull  # Done! Symlinks auto-update
```

**With copies:**
```bash
git pull
make install INSTALL_METHOD=copy
```

### Uninstalling

```bash
make uninstall              # Remove from both platforms
make uninstall-claude       # Claude Code only
make uninstall-codex        # Codex only
```

See [INSTALL.md](INSTALL.md) for detailed troubleshooting.

---

## Documentation

Each skill includes:
- `SKILL.md` — Skill definition and system prompts
- `docs/` — Tool documentation and usage guides
- `summaries/` — Literature summaries for best practices
- `examples/` — Example usage and outputs

Each agent includes:
- Complete skill mapping and decision trees
- Keyword recognition patterns
- Quality gate definitions
- Example workflows and interactions

---

## Contributing

> 🤖 **[AGENTS.md](AGENTS.md)** - Guidance for AI coding agents working with this repository

To add skills or modify agents:
1. Read **[AGENTS.md](AGENTS.md)** for detailed guidance
2. Follow existing skill structure (SKILL.md + docs/ + summaries/)
3. Update agent mappings in `agents/*.md`
4. Add keyword triggers to agent decision trees
5. Test with `make test` and `make install`
6. See **[CONTRIBUTING.md](CONTRIBUTING.md)** for full guidelines

---

## Support

**Agent Issues**: Edit agent files in `agents/`
**Skill Issues**: Refer to skill-specific `SKILL.md`
**Claude Code**: https://github.com/anthropics/claude-code
**Codex CLI**: https://codex.anthropic.com

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

Skills and agents are provided as reference implementations. Individual bioinformatics tools referenced in skills have their own licenses.

---

**Built for researchers, by researchers** • Emphasizes reproducibility, quality, and scientific rigor

---

## Distribution

Want to share these skills with the community? See **[DISTRIBUTION.md](DISTRIBUTION.md)** for:
- How to submit to Anthropic and OpenAI official repositories
- Auto-indexing by SkillsMP and SkillHub marketplaces
- Community outreach strategies
- Making your repository discoverable

## Troubleshooting

### Colors Not Showing

If ANSI colors don't display on your system:

```bash
# Disable colors explicitly
make install NO_COLOR=1

# Colors are automatically disabled for non-TTY (pipes, redirects)
make install > install.log  # Colors disabled automatically
```

### Progress Display

Installation shows progress counters:
```
Progress: 0/24 skills
  [1/24] ✓ agent-browser
  [2/24] ✓ beautiful-data-viz
  ...
  [24/24] ✓ tracking-taxonomy-updates
Completed: 24/24 skills installed
```
