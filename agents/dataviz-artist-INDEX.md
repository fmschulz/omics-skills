# DataViz Artist Agent - Documentation Index

## Quick Start

**To use the agent:**
```bash
claude --agent /home/fschulz/dev/omics-skills/agents/dataviz-artist.md
```

## Documentation Files

### 1. **dataviz-artist.md** (Main Agent File)
**Agent system prompt and configuration**
- Expert persona definition
- 4 core visualization skills
- Mandatory skill usage directives
- Workflow decision trees
- Keyword triggers
- Design principles
- Quality gates
- Integration patterns

**Key Sections:**
- Jupyter notebook development (reproducible analysis)
- Static publication-quality plots (matplotlib/seaborn)
- Interactive dashboards (Plotly Dash)
- Web scraping & browser automation
- Chart selection guide
- Color palette guide

### 2. **dataviz-artist-README.md**
**User guide and quick reference**
- Available skills overview
- Common use cases
- Workflow patterns
- Design principles
- Chart selection guide
- Color palette selection
- Quality checklist
- Tips for working with the agent

### 3. **dataviz-artist-EXAMPLES.md**
**Detailed workflow examples**
- Example 1: Research paper figure (static plot)
- Example 2: Exploratory data analysis notebook
- Example 3: Interactive business dashboard
- Example 4: Web scraping + visualization
- Example 5: Multi-panel publication figure
- Common workflow patterns summary

### 4. **dataviz-artist-QUICK_REFERENCE.md**
**Cheat sheet for rapid lookup**
- One-line decision guide
- Skill selection matrix
- Keyword triggers
- Chart selection guide
- Color palette types
- Common workflows
- Medium-specific styling
- Quality checklist
- Decision trees
- File organization

## Core Skills

### 1. Jupyter Notebook Development
**Skill**: `/jupyter_notebook_ai_agents_skill`

**Purpose**: Create reproducible analysis notebooks with narrative structure

**Key Features**:
- KISS structure (linear, no hidden dependencies)
- Markdown-first (intent before every code cell)
- Reproducibility gate (restart + run all)
- Pixi environments (per-directory dependencies)
- DuckDB data loading (robust, path-safe)
- Beautiful plots integration

**When to Use**:
- Exploratory data analysis
- Research notebooks
- Documented analysis workflows
- Reproducible reports

### 2. Publication-Quality Static Plots
**Skill**: `/beautiful-data-viz`

**Purpose**: Create matplotlib/seaborn charts with refined aesthetics

**Key Features**:
- Publication-ready styling
- Curated color palettes (categorical, sequential, diverging)
- Readable axes and labels
- Tight whitespace, no chart junk
- Export-ready (PDF, SVG, PNG at 300 DPI)
- Colorblind-safe and grayscale validation

**When to Use**:
- Research paper figures
- Presentation slides
- Reports and documentation
- Any static, high-quality visualization

### 3. Interactive Dashboards
**Skill**: `/plotly-dashboard-skill`

**Purpose**: Build production-ready Plotly Dash applications

**Key Features**:
- Intuitive layouts (header + filters + charts)
- Consistent theming (single source of truth)
- Performant callbacks (caching, background jobs)
- Multi-page support
- Professional styling (Dash Bootstrap or Mantine)
- Comprehensive documentation

**When to Use**:
- Business analytics dashboards
- KPI monitoring
- Data exploration apps
- Interactive reporting
- Real-time dashboards

### 4. Web Scraping & Automation
**Skill**: `/agent-browser`

**Purpose**: Browser automation for data collection

**Key Features**:
- Headless/headed browser control
- Element interaction (click, fill, select)
- Screenshot capture
- Session management
- JSON output for parsing

**When to Use**:
- Scraping data for visualization
- Capturing reference screenshots
- Automated data fetching
- Testing deployed dashboards
- Login/authentication flows

## Workflow Decision Matrix

| Need | Primary Skill | Secondary Skills |
|------|--------------|------------------|
| **Analysis notebook** | jupyter_notebook | beautiful-data-viz |
| **Research figure** | beautiful-data-viz | - |
| **Business dashboard** | plotly-dashboard | - |
| **Web data collection** | agent-browser | beautiful-data-viz or plotly-dashboard |
| **Presentation slides** | beautiful-data-viz | - |
| **Multi-panel figure** | beautiful-data-viz | - |

## Design Principles

### 1. Clarity First
Every visualization must communicate its message instantly (3-second test)

### 2. Aesthetic Excellence
Beauty and function are inseparable - clean, professional appearance

### 3. User-Centered Design
Understand audience needs before choosing visualization type

### 4. Reproducibility
All work must run end-to-end without errors

### 5. Accessibility
Must work in grayscale and for colorblind users

### 6. Interactivity (When Useful)
Add interactivity only when it enhances understanding

## Chart Selection Guide

| Goal | Chart Type | Skill |
|------|-----------|-------|
| Show trend over time | Line, area | beautiful-data-viz or plotly-dashboard |
| Compare values | Bar, dot plot | beautiful-data-viz or plotly-dashboard |
| Show distribution | Histogram, violin, box | beautiful-data-viz |
| Show relationship | Scatter, correlation matrix | beautiful-data-viz |
| Show composition | Stacked bar, treemap | plotly-dashboard |
| Interactive exploration | Dashboard with filters/drill-down | plotly-dashboard |

## Color Palette Guide

| Type | Use Case | Examples |
|------|----------|----------|
| **Categorical** | Unordered groups (2-10) | colorblind, Set2, tab10 |
| **Sequential** | Ordered magnitude (0 to max) | viridis, magma, mako, rocket |
| **Diverging** | Values around midpoint | RdBu (red-blue), BrBG (brown-green) |

**Tool**: LearnUI Data Viz Color Picker - https://www.learnui.design/tools/data-color-picker.html

## Quality Gates

Before delivering any visualization:
1. ✅ **Clarity**: Message instantly clear (3-second test)
2. ✅ **Readability**: Text legible at target size
3. ✅ **Grayscale**: Works without color
4. ✅ **Colorblind-safe**: Accessible palette
5. ✅ **Aesthetics**: Clean, minimal chart junk
6. ✅ **Reproducibility**: Code runs end-to-end
7. ✅ **Documentation**: Comments, sources cited

## Common Workflows

### Workflow 1: Research Publication
```
Data → beautiful-data-viz
  ├─ Select appropriate chart type
  ├─ Choose grayscale-safe palette
  ├─ Apply publication styling
  ├─ Validate accessibility
  └─ Export (PDF 300 DPI, SVG)
```

### Workflow 2: Exploratory Analysis
```
Data → jupyter_notebook
  ├─ Pixi environment setup
  ├─ DuckDB data loading
  ├─ Narrative markdown structure
  ├─ Analysis + beautiful-data-viz plots
  └─ Validate (restart + run all)
```

### Workflow 3: Business Dashboard
```
Requirements → plotly-dashboard
  ├─ Define dashboard story
  ├─ Design layout (header + filters + charts)
  ├─ Set up theme (colors, fonts)
  ├─ Build performant callbacks
  ├─ Optimize (caching, background jobs)
  └─ Document (README, architecture)
```

### Workflow 4: Web Data Visualization
```
Web source → agent-browser
  ├─ Navigate to URL
  ├─ Scrape data
  └─ Save structured format
      ↓
  beautiful-data-viz or plotly-dashboard
  └─ Visualize scraped data
```

## File Organization

### Notebook Project
```
project/
├── analysis.ipynb
├── pixi.toml
├── README.md
├── data/
└── outputs/
```

### Dashboard Project
```
dashboard/
├── app.py
├── callbacks/
├── components/
├── utils/
├── assets/
├── requirements.txt
├── README.md
└── data_dictionary.md
```

## Medium-Specific Guidelines

| Medium | Font Size | Resolution | Format | Notes |
|--------|-----------|------------|--------|-------|
| **Notebook** | 11-12pt | 100 DPI | PNG | Inline display |
| **Paper** | 10-12pt | 300 DPI | PDF, SVG | Vector, grayscale-safe |
| **Slides** | 14-18pt | 150 DPI | PNG | High contrast, simple |
| **Dashboard** | 12-14pt | N/A | HTML | Responsive, interactive |

## Integration Philosophy

The agent is a **design-first specialist**:
- **Understands** data and message first
- **Selects** appropriate visualization type and skill
- **Applies** design principles for clarity and beauty
- **Executes** with technical rigor
- **Validates** accessibility and quality

## Use Case Examples

### Academic Research
```
"Create Figure 3 for my paper: scatter plot showing correlation..."
→ beautiful-data-viz (publication-quality, grayscale-safe)
```

### Business Analytics
```
"Build a sales dashboard with KPIs and drill-down..."
→ plotly-dashboard (interactive, professional, performant)
```

### Data Exploration
```
"Analyze customer behavior in a notebook..."
→ jupyter_notebook + beautiful-data-viz (reproducible, documented)
```

### Competitive Analysis
```
"Scrape competitor pricing and compare..."
→ agent-browser (scrape) → beautiful-data-viz (comparison chart)
```

## Tips for Success

1. **Specify medium** - "for paper", "for slides", "for dashboard"
2. **Mention accessibility** - "grayscale-safe", "colorblind-safe"
3. **Describe message** - What should viewer instantly understand?
4. **Provide context** - Data type, audience, constraints
5. **Request validation** - "ensure reproducible", "validate accessibility"

## File Recommendations

| If You Want | Read This File |
|------------|----------------|
| Quick overview | dataviz-artist-README.md |
| See examples | dataviz-artist-EXAMPLES.md |
| Rapid lookup | dataviz-artist-QUICK_REFERENCE.md |
| Modify agent | dataviz-artist.md |

## Related Skills

The agent can integrate with:
- `/matplotlib` - Low-level plotting control
- `/exploratory-data-analysis` - Complex data analysis
- `/statistical-analysis` - Statistical testing
- `/scientific-writing` - Manuscript generation
- `/citation-management` - Reference management

## Support

- **Modify agent**: Edit `dataviz-artist.md`
- **Add workflows**: Update `dataviz-artist-EXAMPLES.md`
- **Quick reference**: Update `dataviz-artist-QUICK_REFERENCE.md`

---

**Last Updated**: 2026-02-01
**Agent Status**: Production-ready
**Total Skills**: 4 (jupyter_notebook, beautiful-data-viz, plotly-dashboard, agent-browser)

