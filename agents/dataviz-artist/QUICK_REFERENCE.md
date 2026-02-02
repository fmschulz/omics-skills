# DataViz Artist Agent - Quick Reference

## One-Line Decision Guide

```
Notebook? → jupyter_notebook + beautiful-data-viz
Static figure? → beautiful-data-viz
Interactive dashboard? → plotly-dashboard
Web data? → agent-browser → visualize
```

## Skill Selection Matrix

| You Need | Use This Skill |
|----------|---------------|
| **Analysis notebook (reproducible)** | `/jupyter_notebook_ai_agents_skill` |
| **Static plot (publication)** | `/beautiful-data-viz` |
| **Interactive dashboard** | `/plotly-dashboard-skill` |
| **Web scraping/automation** | `/agent-browser` |

## Keyword Triggers

| Keywords | Auto-Trigger Skill |
|----------|-------------------|
| "notebook", "jupyter", "EDA", "analysis", "reproducible" | `/jupyter_notebook_ai_agents_skill` |
| "plot", "chart", "figure", "publication", "matplotlib", "static" | `/beautiful-data-viz` |
| "dashboard", "interactive", "plotly", "dash", "KPI", "filters" | `/plotly-dashboard-skill` |
| "scrape", "browser", "screenshot", "web data", "automate" | `/agent-browser` |

## Chart Selection Guide

| Data Type | Chart Type | Skill |
|-----------|-----------|-------|
| Time series | Line, area | beautiful-data-viz or plotly-dashboard |
| Comparison | Bar, dot plot | beautiful-data-viz or plotly-dashboard |
| Distribution | Histogram, violin, box | beautiful-data-viz |
| Relationship | Scatter, correlation | beautiful-data-viz |
| Part-to-whole | Stacked bar, treemap | plotly-dashboard |
| Interactive | Dashboard with filters | plotly-dashboard |

## Color Palette Types

| Palette Type | Use For | Examples |
|-------------|---------|----------|
| **Categorical** | Unordered groups | colorblind, Set2, tab10 |
| **Sequential** | Ordered magnitude | viridis, magma, mako, rocket |
| **Diverging** | Values around midpoint | RdBu, BrBG, PiYG |

**Tool**: LearnUI Color Picker - https://www.learnui.design/tools/data-color-picker.html

## Common Workflows

### 1. Publication Figure
```
beautiful-data-viz
  ├─ Select chart type (based on data)
  ├─ Choose palette (categorical/sequential/diverging)
  ├─ Apply publication styling
  ├─ Validate accessibility (grayscale, colorblind)
  └─ Export (PDF, SVG, PNG @ 300 DPI)
```

### 2. Analysis Notebook
```
jupyter_notebook_ai_agents_skill
  ├─ Set up Pixi environment
  ├─ Create narrative structure (markdown-first)
  ├─ Load data (DuckDB)
  ├─ Analysis sections
  │   └─ beautiful-data-viz (plots)
  └─ Validate (restart + run all)
```

### 3. Interactive Dashboard
```
plotly-dashboard-skill
  ├─ Define dashboard story (who, what, why)
  ├─ Choose layout pattern
  ├─ Set up theme (colors, fonts)
  ├─ Build callbacks (filters, interactions)
  ├─ Optimize performance (caching)
  └─ Document (README, architecture)
```

### 4. Web Scraping → Viz
```
agent-browser
  ├─ Navigate to target site
  ├─ Extract data
  └─ Save structured (CSV, JSON)
      ↓
beautiful-data-viz or plotly-dashboard
  └─ Visualize scraped data
```

## Medium-Specific Styling

| Medium | Font Size | DPI | Format | Notes |
|--------|-----------|-----|--------|-------|
| **Notebook** | 11-12pt | 100 | PNG | Inline display |
| **Paper** | 10-12pt | 300 | PDF, SVG | Vector, grayscale-safe |
| **Slides** | 14-18pt | 150 | PNG | High contrast, simple |
| **Dashboard** | 12-14pt | N/A | HTML | Responsive, interactive |

## Quality Checklist

Before delivery, verify:
- [ ] **Message is clear** (3-second test)
- [ ] **Text readable** (at target size)
- [ ] **Works in grayscale**
- [ ] **Colorblind-safe palette**
- [ ] **No chart junk** (minimal whitespace)
- [ ] **Reproducible** (runs end-to-end)
- [ ] **Documented** (comments, sources)

## Jupyter Notebook Best Practices

From `/jupyter_notebook_ai_agents_skill`:

### KISS Structure
- Short, linear, top-to-bottom
- No hidden dependencies between cells
- Markdown above every code cell

### Markdown Requirements
Every code cell must have markdown that states:
- Intent (what you're doing)
- Expected output (what will appear)
- Assumptions (paths, schema, shapes)

### Reproducibility Gate
Never claim "done" until:
1. Restart kernel (clean state)
2. Run all cells in order
3. Inspect outputs for correctness
4. Fix any warnings/errors

### Data Loading
- Use DuckDB for robust data access
- Validate file existence before reading
- Anchor paths to PROJECT_ROOT
- No hard-coded home directories

## Dashboard Performance Tips

From `/plotly-dashboard-skill`:

### Callback Optimization
- One callback = one user intent
- Keep callbacks small
- Extract transforms to utils/
- Use dcc.Store for shared results
- Use prevent_initial_call=True
- Use PreventUpdate when inputs incomplete

### Caching Strategies
- Memoize expensive data loads
- Cache aggregations in dcc.Store
- Use background callbacks for long-running jobs
- Pre-compute heavy calculations

### Layout Patterns
| Pattern | Best For |
|---------|----------|
| Header + filter bar + grid | Default, general purpose |
| Left rail + main content | Many filters |
| Tabbed sections | Few filters, many views |
| Overview → drilldown pages | Complex multi-page apps |

## Static Plot Styling

From `/beautiful-data-viz`:

### Typography
- Font family: 'Helvetica Neue', sans-serif (or consistent choice)
- Font size: 10-12pt for paper, 14-18pt for slides
- Weights: Regular for body, bold for emphasis

### Whitespace
- Use `constrained_layout=True` or `fig.tight_layout()`
- Export with `bbox_inches='tight'`
- Minimize outer padding
- Remove top/right spines

### Grid
- Subtle, y-axis only (usually)
- Never compete with data
- Light gray (#E5E5E5)

### Axes
- Label with units
- Sensible limits + small margin
- Prevent tick overlap
- Format numbers (K, M, %)

## Browser Automation Commands

From `/agent-browser`:

```bash
# Open URL
agent-browser open <url>

# Take snapshot
agent-browser snapshot -i --json

# Interact with elements
agent-browser click @eN
agent-browser fill @eN "text"
agent-browser get text @eN --json

# Screenshot
agent-browser screenshot [path]

# Sessions
agent-browser open <url> --session <name>
```

## Export Formats

| Format | Type | Best For | Command |
|--------|------|----------|---------|
| **PDF** | Vector | Publications, print | `plt.savefig('fig.pdf', dpi=300, bbox_inches='tight')` |
| **SVG** | Vector | Web, editing | `plt.savefig('fig.svg', bbox_inches='tight')` |
| **PNG** | Raster | Presentations, web | `plt.savefig('fig.png', dpi=300, bbox_inches='tight')` |

## Decision Trees

### "I need a visualization"
```
IF for publication
  THEN use /beautiful-data-viz

IF for interactive exploration
  THEN use /plotly-dashboard-skill

IF part of analysis workflow
  THEN use /jupyter_notebook_ai_agents_skill + /beautiful-data-viz
```

### "I have data to visualize"
```
IF data is online
  THEN /agent-browser (scrape) → visualize

IF data is local CSV/TSV/Parquet
  THEN /jupyter_notebook_ai_agents_skill (load + analyze)
```

### "I'm making a dashboard"
```
IF simple report (few filters, static layout)
  THEN single-page Dash app

IF complex app (many views, drill-downs)
  THEN multi-page Dash app

IF real-time monitoring
  THEN Dash with background callbacks + dcc.Interval
```

## Accessibility Rules

### Colorblind-Safe
- Use distinct markers (o, s, ^) in addition to color
- Test with grayscale conversion
- Prefer colorblind-safe palettes (colorblind, Set2)

### Contrast
- Minimum 4.5:1 for text vs background
- Use high contrast for emphasis
- Avoid light colors on light backgrounds

### Readability
- Minimum 10pt font for print
- Minimum 12pt font for screens
- Avoid text rotation (except y-axis labels)

## Common Mistakes to Avoid

| Mistake | Fix |
|---------|-----|
| Rainbow gradient for categories | Use categorical palette (distinct hues) |
| Tiny fonts | 10pt minimum (12pt for presentations) |
| Truncated y-axis (misleading) | Start at 0 or show break clearly |
| Too many colors | Limit to 5-7 categories |
| 3D effects | Use 2D, encode with color/size instead |
| Excessive chart junk | Remove unnecessary elements |
| Hard-coded paths | Use relative paths from PROJECT_ROOT |
| No validation | Always restart + run all cells |

## File Organization

### Notebook Project
```
project/
├── analysis.ipynb        (main notebook)
├── pixi.toml            (environment)
├── README.md            (instructions)
├── data/
│   └── input_data.csv
└── outputs/
    ├── figure1.pdf
    └── figure2.png
```

### Dashboard Project
```
dashboard/
├── app.py               (entry point)
├── callbacks/           (callback functions)
├── components/          (UI components)
├── utils/              (data loading, transforms)
├── assets/             (CSS, images)
│   └── custom.css
├── requirements.txt    (dependencies)
├── README.md           (documentation)
└── data_dictionary.md  (metric definitions)
```

## Integration with Other Skills

| Skill | Integration |
|-------|-------------|
| `/exploratory-data-analysis` | Load complex data → visualize |
| `/statistical-analysis` | Run tests → visualize results |
| `/scientific-writing` | Generate manuscript → embed figures |
| `/matplotlib` | Low-level control (via beautiful-data-viz) |

## Performance Benchmarks

| Operation | Target Time | Optimization |
|-----------|-------------|--------------|
| Dashboard page load | < 1s | Pre-compute aggregations |
| Callback response | < 300ms | Cache, use dcc.Store |
| Plot rendering (static) | < 1s | Downsample if > 10K points |
| Notebook execution | < 5 min | Use DuckDB for large data |

## Validation Commands

### Notebook
```bash
# Run notebook end-to-end
jupyter nbconvert --to notebook --execute analysis.ipynb

# Or use provided script
python scripts/execute_notebook.py analysis.ipynb
```

### Dashboard
```bash
# Development
python app.py

# Production
gunicorn app:server --workers 4 --bind 0.0.0.0:8050
```

### Grayscale Test
```python
# Convert figure to grayscale
from PIL import Image
img = Image.open('figure.png').convert('L')
img.save('figure_grayscale.png')
```

## Remember

1. **Design first** - Understand message before choosing chart
2. **Accessibility** - Must work in grayscale and for colorblind
3. **Reproducibility** - Code must run end-to-end
4. **Documentation** - Clear comments, data sources cited
5. **Simplicity** - Remove chart junk, maximize data-ink ratio

## Quick Examples

### Static Plot (Paper)
```python
from beautiful_style import set_beautiful_style, finalize_axes

set_beautiful_style(medium='paper', background='light')
fig, ax = plt.subplots(figsize=(5, 4), dpi=300)
ax.plot(x, y, color='#2C3E50')
finalize_axes(ax, title='Title', tight=True)
plt.savefig('figure.pdf', dpi=300, bbox_inches='tight')
```

### Dashboard Layout
```python
import dash_bootstrap_components as dbc
from dash import dcc, html

layout = dbc.Container([
    dbc.Row([dbc.Col(html.H1("Dashboard Title"))]),
    dbc.Row([dbc.Col(dcc.Dropdown(id="filter"))]),
    dbc.Row([dbc.Col(dcc.Graph(id="chart"))]),
])
```

### Notebook Data Loading
```python
import duckdb
from pathlib import Path

DATA_FILE = Path('data/input.csv')
assert DATA_FILE.exists()

con = duckdb.connect(':memory:')
df = con.execute(f"SELECT * FROM read_csv_auto('{DATA_FILE}')").df()
```

### Web Scraping
```bash
agent-browser open https://example.com/pricing
agent-browser snapshot -i --json
agent-browser screenshot pricing.png
agent-browser get text @e5 --json > data.json
```

