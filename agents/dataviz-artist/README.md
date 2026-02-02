# DataViz Artist Agent - User Guide

## Overview

The **dataviz-artist** agent is an expert data visualization specialist that helps you create beautiful, clear, and reproducible visualizations. Whether you need publication-quality static plots, interactive dashboards, or exploratory analysis notebooks, this agent selects the right tools and applies best design practices.

## Quick Start

```bash
# Invoke the agent
claude --agent /home/fschulz/dev/omics-skills/agents/dataviz-artist.md

# Or copy to user directory
cp dataviz-artist.md ~/.claude/agents/
claude --agent dataviz-artist
```

## Available Skills

| Skill | Purpose | Best For |
|-------|---------|----------|
| **jupyter_notebook_ai_agents_skill** | Reproducible analysis notebooks | EDA, research notebooks, documented analysis |
| **beautiful-data-viz** | Publication-quality static plots | Papers, presentations, reports |
| **plotly-dashboard-skill** | Interactive dashboards | Business analytics, monitoring, data apps |
| **agent-browser** | Web scraping & automation | Data collection, screenshots, testing |

## Common Use Cases

### 1. Research Paper Figures

**Need**: Publication-quality static charts for academic papers

**Skills Used**: `/beautiful-data-viz`

**Example**:
```
You: "Create Figure 2: line plot showing temperature trends over 50 years."

Agent: Uses /beautiful-data-viz to create:
- Clean, professional line chart
- Grayscale-safe color palette
- Proper axis labels with units
- Tight layout, no chart junk
- Export as PDF (vector) and PNG (300 DPI)
```

### 2. Exploratory Data Analysis

**Need**: Interactive notebook for data exploration

**Skills Used**: `/jupyter_notebook_ai_agents_skill` + `/beautiful-data-viz`

**Example**:
```
You: "Create a notebook to explore sales data."

Agent:
1. /jupyter_notebook_ai_agents_skill - Sets up reproducible notebook
2. /beautiful-data-viz - Creates beautiful plots within notebook
3. /jupyter_notebook_ai_agents_skill - Validates (restart + run all)
```

### 3. Business Dashboard

**Need**: Interactive dashboard for KPI monitoring

**Skills Used**: `/plotly-dashboard-skill`

**Example**:
```
You: "Build a dashboard to monitor website traffic with drill-down."

Agent: Uses /plotly-dashboard-skill to create:
- Multi-page Dash app
- KPI cards + trend charts
- Interactive filters
- Drill-down capability
- Professional theming
- Comprehensive documentation
```

### 4. Web Data Collection

**Need**: Scrape data from websites for visualization

**Skills Used**: `/agent-browser` → `/beautiful-data-viz` or `/plotly-dashboard-skill`

**Example**:
```
You: "Scrape competitor pricing and create comparison chart."

Agent:
1. /agent-browser - Collects pricing data
2. /beautiful-data-viz - Creates comparison bar chart
```

## Workflow Patterns

### Pattern 1: Notebook Development
```
Create Analysis Notebook
    ↓
/jupyter_notebook_ai_agents_skill
    ├─ Set up Pixi environment
    ├─ Create narrative structure
    ├─ Load data (DuckDB)
    ├─ Analysis sections
    └─ Beautiful plots (/beautiful-data-viz)
    ↓
Validate Reproducibility
    ↓
/jupyter_notebook_ai_agents_skill (restart + run all)
```

### Pattern 2: Dashboard Development
```
Define Requirements
    ↓
/plotly-dashboard-skill
    ├─ Dashboard story (audience, goals)
    ├─ Layout design (header, filters, charts)
    ├─ Theme setup (colors, fonts)
    ├─ Build callbacks (interactivity)
    ├─ Performance optimization (caching)
    └─ Documentation (README, architecture)
    ↓
Test & Deploy
```

### Pattern 3: Publication Figure
```
Understand Data & Message
    ↓
/beautiful-data-viz
    ├─ Select chart type
    ├─ Choose appropriate palette
    ├─ Apply publication styling
    ├─ Optimize readability
    ├─ Validate accessibility
    └─ Export (PDF, SVG, PNG)
```

## Design Principles

The agent follows these core principles:

### 1. Clarity First
- Message is instantly clear (3-second test)
- Appropriate chart type for data
- Clear titles and labels
- No misleading scales or distortions

### 2. Aesthetic Excellence
- Clean, professional appearance
- Consistent typography
- Curated color palettes
- Tight whitespace, no chart junk

### 3. Accessibility
- Works in grayscale
- Colorblind-safe palettes
- Readable at target size
- High contrast

### 4. Reproducibility
- Code runs end-to-end
- Documented data sources
- Clear comments and structure
- Version-controlled environments (Pixi)

## Chart Selection Guide

| Data Type | Recommended Chart | Skill |
|-----------|------------------|-------|
| **Time series** | Line chart, area chart | beautiful-data-viz or plotly-dashboard |
| **Comparison** | Bar chart, dot plot | beautiful-data-viz or plotly-dashboard |
| **Distribution** | Histogram, density plot, violin | beautiful-data-viz |
| **Relationship** | Scatter plot, correlation matrix | beautiful-data-viz |
| **Composition** | Stacked bar, treemap | plotly-dashboard (interactive) |
| **Spatial** | Heatmap, choropleth map | plotly-dashboard |
| **Interactive exploration** | Dashboard with filters | plotly-dashboard |

## Color Palette Selection

### Categorical (Qualitative)
**Use for**: Discrete categories with no order
- **2-5 categories**: High contrast, visually distinct
- **6-10 categories**: Equidistant hue spacing
- **Examples**: colorblind, Set2, tab10

### Sequential
**Use for**: Ordered numeric data (0 to max)
- **Single hue**: Light to dark progression
- **Perceptually uniform**: viridis, magma, mako, rocket
- **Use cases**: Heatmaps, intensity maps

### Diverging
**Use for**: Data with meaningful midpoint
- **Structure**: Neutral center, distinct endpoints
- **Examples**: RdBu (red-blue), BrBG (brown-green)
- **Use cases**: Correlation, change from baseline

**Tool**: LearnUI Data Viz Color Picker - https://www.learnui.design/tools/data-color-picker.html

## Quality Checklist

Before delivery, the agent validates:

- [ ] **Clarity**: Message is instantly clear
- [ ] **Readability**: All text legible at target size
- [ ] **Color**: Works in grayscale and for colorblind users
- [ ] **Data integrity**: No misleading visualizations
- [ ] **Aesthetics**: Clean, professional, minimal chart junk
- [ ] **Reproducibility**: Code runs end-to-end
- [ ] **Documentation**: Clear comments, data sources cited

## Tips for Working with the Agent

### 1. Specify Your Audience
```
✅ "Create a figure for a research paper (academic audience)"
✅ "Build a dashboard for executives (non-technical)"
❌ "Make a chart"
```

### 2. Mention the Medium
```
✅ "Presentation slide (large fonts, high contrast)"
✅ "Notebook analysis (inline, moderate size)"
✅ "Paper figure (grayscale-safe, high resolution)"
❌ "Create a visualization"
```

### 3. Describe the Message
```
✅ "Show that sales increased 30% year-over-year"
✅ "Compare regional performance to identify underperformers"
❌ "Plot the data"
```

### 4. Request Specific Features
```
✅ "Interactive dashboard with date range filter and drill-down"
✅ "Static bar chart with error bars, grayscale-safe"
✅ "Notebook with narrative explaining each analysis step"
```

## Integration with Other Skills

The dataviz-artist can integrate with:

- `/matplotlib` - Foundational plotting (via beautiful-data-viz)
- `/exploratory-data-analysis` - Analyze complex scientific data
- `/statistical-analysis` - Statistical tests for visualization
- `/scientific-writing` - Manuscripts with embedded figures
- `/citation-management` - Reference management for figure sources

## Troubleshooting

**Q: Agent created the wrong chart type?**
A: Be specific about data characteristics (categorical vs continuous, temporal, hierarchical)

**Q: Colors don't work in grayscale?**
A: Request "grayscale-safe" or "colorblind-safe" palette explicitly

**Q: Notebook won't reproduce?**
A: Agent uses /jupyter_notebook_ai_agents_skill which validates reproducibility automatically

**Q: Dashboard is slow?**
A: Agent uses /plotly-dashboard-skill which implements caching and performance optimization

**Q: Need to scrape data first?**
A: Mention "scrape" or "browser automation" to trigger /agent-browser

## File Outputs

### Notebooks
- `.ipynb` - Jupyter notebook
- `pixi.toml` - Environment specification
- `README.md` - Usage instructions

### Static Figures
- `.pdf` - Vector (publication-quality)
- `.svg` - Vector (web/editing)
- `.png` - Raster (presentations, 300 DPI)

### Dashboards
- `app.py` - Dash application
- `requirements.txt` or `pyproject.toml` - Dependencies
- `README.md` - Run instructions, screenshots
- `assets/` - CSS, images, custom styling

## Examples by Domain

### Academic Research
```
"Create Figure 3 for my Nature paper: scatter plot showing correlation
between gene expression and protein abundance, n=500 samples."

Agent uses: /beautiful-data-viz
- Scatter plot with trend line
- Grayscale-safe palette
- Clear axis labels with units
- Export PDF (vector) + 300 DPI PNG
```

### Business Analytics
```
"Build a sales dashboard with YoY trends, regional breakdown, and
product drill-down for our quarterly review."

Agent uses: /plotly-dashboard-skill
- Multi-page Dash app
- KPI cards, trend lines, breakdowns
- Interactive filters (date, region, product)
- Professional theming (Dash Bootstrap)
- Cached callbacks for performance
```

### Exploratory Analysis
```
"Create a notebook to explore customer churn patterns in our dataset."

Agent uses: /jupyter_notebook_ai_agents_skill + /beautiful-data-viz
- Reproducible notebook with Pixi
- Narrative markdown before each section
- Beautiful plots (distributions, trends, correlations)
- DuckDB for robust data loading
- Validated reproducibility (restart + run all)
```

## Advanced Features

### Notebook Reproducibility
- Per-directory Pixi environments
- DuckDB for reliable data loading
- Markdown-first narrative structure
- Automatic validation (restart + run all)

### Dashboard Performance
- Callback caching for expensive operations
- Background jobs for long-running tasks
- Efficient data structures (dcc.Store)
- Responsive UI patterns

### Publication Quality
- High-resolution exports (300+ DPI)
- Vector formats (PDF, SVG)
- Grayscale and colorblind validation
- Tight bounding boxes

### Browser Automation
- Headless/headed modes
- Session management
- Screenshot capture
- JSON output for parsing

## Support

- **Modify agent behavior**: Edit `dataviz-artist.md`
- **Add examples**: Create new workflow patterns
- **Report issues**: Document and share

---

**Remember**: The agent is a design-first specialist. Always start with understanding the data, message, and audience before choosing visualization types.

