# DataViz Artist Agent - Example Workflows

This document provides detailed examples of using the dataviz-artist agent across various scenarios.

## Example 1: Research Paper Figure (Static Plot)

### Scenario
You need Figure 2 for a research paper: a scatter plot showing the relationship between two variables with color-coded categories.

### Input Requirements
```
- Dataset: CSV with columns [variable_A, variable_B, category]
- Target: Publication in Nature journal
- Format: PDF (vector) + 300 DPI PNG
- Requirements: Grayscale-safe, colorblind-safe
```

### Conversation

```
You: I need Figure 2 for my Nature paper. Show correlation between metabolic rate
     and body mass across 120 species, color-coded by habitat (aquatic, terrestrial, aerial).
     Must be publication-quality, grayscale-safe.

DataViz Artist:
I'll create a publication-quality scatter plot with appropriate styling:

→ /beautiful-data-viz

Design decisions:
1. Chart type: Scatter plot (bivariate relationship)
2. Color palette: Categorical, 3 colors (aquatic, terrestrial, aerial)
   - Using colorblind-safe palette (orange, blue, green)
   - Verified works in grayscale (different markers per category)
3. Styling:
   - Publication fonts (10-12pt, sans-serif)
   - Clear axis labels with units ("Body Mass (kg)", "Metabolic Rate (kcal/day)")
   - Legend with 3 categories, positioned to avoid data occlusion
   - Tight layout, minimal whitespace
   - No unnecessary grid lines
4. Exports:
   - PDF (vector, for publication submission)
   - SVG (vector, for editing if needed)
   - PNG (300 DPI, for presentations)

Code execution:
```python
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from beautiful_style import set_beautiful_style, finalize_axes

# Load data
df = pd.read_csv('species_data.csv')

# Set publication style
set_beautiful_style(medium='paper', background='light')

# Create figure
fig, ax = plt.subplots(figsize=(5, 4), dpi=300)

# Colorblind-safe palette
palette = {'aquatic': '#0173B2', 'terrestrial': '#DE8F05', 'aerial': '#029E73'}
markers = {'aquatic': 'o', 'terrestrial': 's', 'aerial': '^'}

# Plot each category
for habitat in ['aquatic', 'terrestrial', 'aerial']:
    data = df[df['category'] == habitat]
    ax.scatter(data['body_mass'], data['metabolic_rate'],
               c=palette[habitat], marker=markers[habitat],
               s=50, alpha=0.7, edgecolors='white', linewidths=0.5,
               label=habitat.capitalize())

# Styling
ax.set_xlabel('Body Mass (kg)', fontsize=11)
ax.set_ylabel('Metabolic Rate (kcal/day)', fontsize=11)
ax.legend(frameon=False, fontsize=10)
finalize_axes(ax, title='', tight=True)

# Export
plt.savefig('figure2_vector.pdf', dpi=300, bbox_inches='tight')
plt.savefig('figure2_vector.svg', bbox_inches='tight')
plt.savefig('figure2_raster.png', dpi=300, bbox_inches='tight')
```

Validation:
✓ Works in grayscale (different markers)
✓ Colorblind-safe (verified with color picker)
✓ Text readable at target size
✓ No data distortion or misleading scales
✓ Exported in required formats

Suggested caption:
"Figure 2. Relationship between body mass and metabolic rate across 120 species.
Colors and markers indicate habitat type (aquatic: blue circles, terrestrial: orange
squares, aerial: green triangles). Spearman's ρ = 0.87, p < 0.001."
```

### Expected Outputs
```
outputs/
├── figure2_vector.pdf    (for submission)
├── figure2_vector.svg    (for editing)
└── figure2_raster.png    (for presentations)
```

---

## Example 2: Exploratory Data Analysis Notebook

### Scenario
Create a reproducible notebook to explore customer churn patterns in a telecommunications dataset.

### Input Requirements
```
- Dataset: customer_data.csv (10K rows, 20 columns)
- Analysis: Univariate distributions, bivariate relationships, temporal trends
- Requirements: Reproducible, documented, beautiful plots
```

### Conversation

```
You: Create an exploratory analysis notebook for customer churn data. Include
     distributions, correlations, and temporal trends. Make it reproducible.

DataViz Artist:
I'll create a KISS (Keep It Simple, Structured) notebook with narrative documentation:

→ /jupyter_notebook_ai_agents_skill

Notebook structure:
1. Setup & Environment
   - Pixi environment (pandas, matplotlib, seaborn, duckdb)
   - Data loading with DuckDB (robust, path-safe)
   - Markdown: Purpose, data source, analysis goals

2. Data Overview
   - Markdown: "Examine dataset structure, types, and completeness"
   - Code: Load data, display head, info, describe
   - Code: Check for nulls, duplicates, data types

3. Univariate Distributions
   - Markdown: "Understand individual variable distributions"
   - Code: Histograms for numeric features
   - Code: Bar charts for categorical features
   → /beautiful-data-viz for styling

4. Churn Rate Analysis
   - Markdown: "Calculate overall churn rate and by segment"
   - Code: Aggregate churn by category (contract type, tenure, service)
   - Code: Bar plot showing churn rates

5. Bivariate Relationships
   - Markdown: "Explore relationships between features and churn"
   - Code: Correlation heatmap
   - Code: Box plots (tenure vs churn, charges vs churn)

6. Temporal Trends
   - Markdown: "Examine churn patterns over time"
   - Code: Monthly churn rates (line plot)
   - Code: Cohort analysis (heatmap)

7. Key Findings & Next Steps
   - Markdown: Summary of insights
   - Markdown: Recommendations for predictive modeling

Pixi environment (pixi.toml):
```toml
[project]
name = "churn-analysis"
channels = ["conda-forge"]

[dependencies]
python = "3.11.*"
pandas = ">=2.0"
matplotlib = ">=3.7"
seaborn = ">=0.12"
duckdb = ">=0.9"
jupyterlab = "*"
pixi-kernel = "*"
```

Data loading (DuckDB for robustness):
```python
import duckdb
from pathlib import Path

PROJECT_ROOT = Path().absolute()
DATA_DIR = PROJECT_ROOT / 'data'
DATA_FILE = DATA_DIR / 'customer_data.csv'

# Validate file exists
assert DATA_FILE.exists(), f"Data file not found: {DATA_FILE}"

# Load with DuckDB
con = duckdb.connect(':memory:')
df = con.execute(f"SELECT * FROM read_csv_auto('{DATA_FILE}')").df()
```

Plot styling (/beautiful-data-viz):
- Consistent color palette (categorical: colorblind-safe)
- Tight layouts, no excess whitespace
- Clear titles and axis labels
- Readable fonts (11-12pt)

Validation gate:
1. Restart kernel
2. Run all cells sequentially
3. Verify outputs:
   - Data loads correctly
   - All plots render
   - No warnings/errors
4. Check reproducibility:
   - Same results on each run
   - No hard-coded paths

Proceeding with notebook creation...
```

### Expected Outputs
```
project/
├── churn_analysis.ipynb     (analysis notebook)
├── pixi.toml                (environment specification)
├── README.md                (usage instructions)
└── data/
    └── customer_data.csv    (input data)
```

---

## Example 3: Interactive Business Dashboard

### Scenario
Build an executive sales dashboard with KPIs, trends, regional breakdowns, and drill-down capability.

### Input Requirements
```
- Data: sales_data.csv (daily sales, regional, product categories)
- Users: Executive team (non-technical)
- Features: KPIs, trends, filters (date, region, product), drill-down
- Deployment: Internal server (Flask/Gunicorn)
```

### Conversation

```
You: Build an executive sales dashboard. Show KPIs (revenue, orders, AOV),
     trends over time, regional performance, and allow drill-down to product level.
     Needs to be polished and intuitive for non-technical users.

DataViz Artist:
I'll build a production-ready Plotly Dash dashboard with professional styling:

→ /plotly-dashboard-skill

Step 1: Dashboard story
- Audience: Executive team (CEO, VP Sales, Regional Managers)
- Decisions: Resource allocation, regional strategy, product focus
- Key questions:
  1. Are we on track to hit quarterly targets?
  2. Which regions are over/under-performing?
  3. Which products drive revenue?

Step 2: Layout pattern
- Pattern: Header + filters + KPI cards + trend charts + drill-down table
- Structure:
  ```
  ┌─────────────────────────────────────────┐
  │ Header: Sales Dashboard | Last Updated  │
  ├─────────────────────────────────────────┤
  │ Filters: Date Range | Region | Product  │
  ├─────────────────────────────────────────┤
  │ KPI Cards: Revenue | Orders | AOV       │
  ├─────────────────────────────────────────┤
  │ Trends: Revenue Over Time (line chart)  │
  ├─────────────────────────────────────────┤
  │ Breakdown: Regional Performance (bar)   │
  ├─────────────────────────────────────────┤
  │ Details: Product-level Table (sortable) │
  └─────────────────────────────────────────┘
  ```

Step 3: Theme setup (Dash Bootstrap Components)
- UI library: dash-bootstrap-components
- Theme: FLATLY (professional, clean)
- Typography:
  - Headings: 'Helvetica Neue', sans-serif
  - Body: 'Helvetica Neue', sans-serif
- Color palette:
  - Primary: #2C3E50 (dark blue-gray)
  - Success: #18BC9C (green, for positive metrics)
  - Warning: #F39C12 (orange, for alerts)
  - Categories: colorblind-safe palette

Step 4: Plotly figure template
```python
import plotly.graph_objects as go
import plotly.io as pio

# Create template
template = go.layout.Template()
template.layout = go.Layout(
    font=dict(family='Helvetica Neue, sans-serif', size=12, color='#2C3E50'),
    plot_bgcolor='white',
    paper_bgcolor='white',
    xaxis=dict(showgrid=True, gridcolor='#E5E5E5', showline=True, linecolor='#CCCCCC'),
    yaxis=dict(showgrid=True, gridcolor='#E5E5E5', showline=True, linecolor='#CCCCCC'),
    hovermode='closest'
)

# Register template
pio.templates['sales_dashboard'] = template
pio.templates.default = 'sales_dashboard'
```

Step 5: Layout skeleton
```python
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col(html.H1("Sales Dashboard", className="text-primary"), width=8),
        dbc.Col(html.P(id="last-updated", className="text-muted text-end"), width=4)
    ], className="mb-4"),

    # Filters
    dbc.Row([
        dbc.Col([dcc.DatePickerRange(id="date-filter")], width=4),
        dbc.Col([dcc.Dropdown(id="region-filter", multi=True)], width=4),
        dbc.Col([dcc.Dropdown(id="product-filter", multi=True)], width=4),
    ], className="mb-4"),

    # KPI Cards
    dbc.Row([
        dbc.Col(dbc.Card([html.H3(id="kpi-revenue"), html.P("Revenue")]), width=4),
        dbc.Col(dbc.Card([html.H3(id="kpi-orders"), html.P("Orders")]), width=4),
        dbc.Col(dbc.Card([html.H3(id="kpi-aov"), html.P("Avg Order Value")]), width=4),
    ], className="mb-4"),

    # Trends
    dbc.Row([
        dbc.Col([dcc.Graph(id="trend-chart")], width=12)
    ], className="mb-4"),

    # Regional Breakdown
    dbc.Row([
        dbc.Col([dcc.Graph(id="regional-chart")], width=12)
    ], className="mb-4"),

    # Product Table
    dbc.Row([
        dbc.Col([html.Div(id="product-table")], width=12)
    ]),

    # Data store (for caching)
    dcc.Store(id="filtered-data")
], fluid=True)
```

Step 6: Performant callbacks
```python
from dash import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd

# Callback 1: Filter data (cached in Store)
@app.callback(
    Output("filtered-data", "data"),
    Input("date-filter", "start_date"),
    Input("date-filter", "end_date"),
    Input("region-filter", "value"),
    Input("product-filter", "value")
)
def filter_data(start, end, regions, products):
    # Load and filter data
    df = load_sales_data()  # Could be cached with @functools.lru_cache

    # Apply filters
    if start and end:
        df = df[(df['date'] >= start) & (df['date'] <= end)]
    if regions:
        df = df[df['region'].isin(regions)]
    if products:
        df = df[df['product'].isin(products)]

    return df.to_json(date_format='iso', orient='split')

# Callback 2: Update KPIs
@app.callback(
    Output("kpi-revenue", "children"),
    Output("kpi-orders", "children"),
    Output("kpi-aov", "children"),
    Input("filtered-data", "data")
)
def update_kpis(data_json):
    df = pd.read_json(data_json, orient='split')

    revenue = df['amount'].sum()
    orders = len(df)
    aov = revenue / orders if orders > 0 else 0

    return f"${revenue:,.0f}", f"{orders:,}", f"${aov:.2f}"

# Callback 3: Update trend chart
@app.callback(
    Output("trend-chart", "figure"),
    Input("filtered-data", "data")
)
def update_trend(data_json):
    df = pd.read_json(data_json, orient='split')

    # Aggregate by date
    daily = df.groupby('date')['amount'].sum().reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily['date'], y=daily['amount'],
        mode='lines+markers', name='Revenue',
        line=dict(color='#2C3E50', width=2)
    ))

    fig.update_layout(
        title="Revenue Over Time",
        xaxis_title="Date",
        yaxis_title="Revenue ($)",
        hovermode='x unified'
    )

    return fig
```

Step 7: Performance optimization
- Cache expensive data loads with @functools.lru_cache
- Use dcc.Store for intermediate results (avoids recomputation)
- Implement prevent_initial_call=True where appropriate
- Consider background callbacks for long-running aggregations

Step 8: UX polish
- Loading states (dcc.Loading) for expensive updates
- Empty-state messaging ("No data for this filter")
- "Last updated" timestamp
- Tooltips on KPI cards explaining metrics
- Responsive design (works on tablets)

Step 9: Documentation
Deliverables:
1. README.md - Purpose, run instructions, screenshots
2. data_dictionary.md - Metric definitions
3. architecture.md - File structure, callback flow
4. requirements.txt - Dependencies

Step 10: Deployment
```bash
# Development
python app.py

# Production
gunicorn app:server --workers 4 --bind 0.0.0.0:8050
```

Proceeding with dashboard build...
```

### Expected Outputs
```
sales-dashboard/
├── app.py                   (main application)
├── callbacks/
│   ├── filters.py
│   ├── kpis.py
│   └── charts.py
├── components/
│   ├── header.py
│   ├── filters.py
│   └── kpi_cards.py
├── utils/
│   ├── data_loader.py
│   └── aggregations.py
├── assets/
│   ├── custom.css
│   └── logo.png
├── requirements.txt
├── README.md
├── data_dictionary.md
└── architecture.md
```

---

## Example 4: Web Scraping + Visualization

### Scenario
Scrape competitor pricing from multiple websites and create a comparison visualization.

### Input Requirements
```
- Target: 3 competitor websites with pricing tables
- Goal: Compare pricing tiers across competitors
- Output: Bar chart showing price comparison
```

### Conversation

```
You: Scrape pricing from these 3 competitor sites and create a comparison chart:
     - competitor-a.com/pricing
     - competitor-b.com/pricing
     - competitor-c.com/pricing

DataViz Artist:
I'll automate data collection and create a comparison visualization:

Step 1: Web scraping
→ /agent-browser

For each competitor site:
```bash
# Open site
agent-browser open https://competitor-a.com/pricing --session comp-a

# Take screenshot for reference
agent-browser screenshot reference-comp-a.png

# Find pricing table and extract data
agent-browser snapshot -i --json > snapshot.json
agent-browser get text @e12 --json  # Extract price text from elements
```

Scraping strategy:
1. Navigate to pricing page
2. Identify pricing table elements
3. Extract tier names and prices
4. Save to structured format (CSV/JSON)
5. Repeat for all 3 competitors

Output: pricing_data.csv
```csv
competitor,tier,price,features
Competitor A,Basic,29,Feature set A
Competitor A,Pro,79,Feature set B
Competitor A,Enterprise,199,Feature set C
Competitor B,Starter,19,Feature set A
...
```

Step 2: Visualization
→ /beautiful-data-viz

Chart type: Grouped bar chart (tiers on x-axis, prices on y-axis, grouped by competitor)

```python
import pandas as df
import matplotlib.pyplot as plt
from beautiful_style import set_beautiful_style, finalize_axes

# Load scraped data
df = pd.read_csv('pricing_data.csv')

# Pivot for grouped bar chart
pivot = df.pivot(index='tier', columns='competitor', values='price')

# Set style
set_beautiful_style(medium='slides', background='light')

# Create chart
fig, ax = plt.subplots(figsize=(10, 6))

pivot.plot(kind='bar', ax=ax, color=['#0173B2', '#DE8F05', '#029E73'], width=0.8)

ax.set_xlabel('Pricing Tier', fontsize=14)
ax.set_ylabel('Price ($/month)', fontsize=14)
ax.set_title('Competitor Pricing Comparison', fontsize=16, fontweight='bold')
ax.legend(title='Competitor', frameon=False, fontsize=12)
ax.set_xticklabels(ax.get_xticklabels(), rotation=0)

finalize_axes(ax, tight=True)

plt.savefig('pricing_comparison.png', dpi=300, bbox_inches='tight')
```

Deliverables:
1. pricing_data.csv (scraped data)
2. pricing_comparison.png (visualization)
3. references/ (screenshots from each competitor)
4. scraping_script.sh (reproducible scraping commands)
```

### Expected Outputs
```
competitor-analysis/
├── pricing_data.csv           (scraped data)
├── pricing_comparison.png     (visualization)
├── references/
│   ├── competitor-a.png
│   ├── competitor-b.png
│   └── competitor-c.png
└── scrape.sh                  (automation script)
```

---

## Example 5: Multi-Panel Figure for Publication

### Scenario
Create a complex multi-panel figure (Figure 4) for a research paper with 4 subplots arranged in a 2x2 grid.

### Conversation

```
You: Create Figure 4 for my paper: 2x2 grid with (A) time series, (B) bar chart,
     (C) heatmap, (D) scatter plot. All grayscale-safe, consistent styling.

DataViz Artist:
→ /beautiful-data-viz

I'll create a multi-panel figure with consistent styling:

```python
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from beautiful_style import set_beautiful_style, finalize_axes

# Set publication style
set_beautiful_style(medium='paper', background='light')

# Create figure with GridSpec for flexible layout
fig = plt.figure(figsize=(10, 8), dpi=300)
gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)

# Panel A: Time series
ax_a = fig.add_subplot(gs[0, 0])
ax_a.plot(time, values, color='#2C3E50', linewidth=2)
ax_a.set_xlabel('Time (days)')
ax_a.set_ylabel('Expression Level')
ax_a.text(-0.15, 1.05, 'A', transform=ax_a.transAxes,
          fontsize=16, fontweight='bold')
finalize_axes(ax_a, tight=False)

# Panel B: Bar chart
ax_b = fig.add_subplot(gs[0, 1])
ax_b.bar(categories, means, color='#34495E', yerr=stds, capsize=3)
ax_b.set_xlabel('Treatment')
ax_b.set_ylabel('Response')
ax_b.text(-0.15, 1.05, 'B', transform=ax_b.transAxes,
          fontsize=16, fontweight='bold')
finalize_axes(ax_b, tight=False)

# Panel C: Heatmap
ax_c = fig.add_subplot(gs[1, 0])
im = ax_c.imshow(matrix, cmap='RdBu_r', aspect='auto')
ax_c.set_xlabel('Samples')
ax_c.set_ylabel('Genes')
cbar = plt.colorbar(im, ax=ax_c, fraction=0.046, pad=0.04)
cbar.set_label('Log2 Fold Change')
ax_c.text(-0.15, 1.05, 'C', transform=ax_c.transAxes,
          fontsize=16, fontweight='bold')

# Panel D: Scatter plot
ax_d = fig.add_subplot(gs[1, 1])
ax_d.scatter(x, y, c='#7F8C8D', s=20, alpha=0.6, edgecolors='white', linewidths=0.5)
ax_d.set_xlabel('Variable X')
ax_d.set_ylabel('Variable Y')
ax_d.text(-0.15, 1.05, 'D', transform=ax_d.transAxes,
          fontsize=16, fontweight='bold')
finalize_axes(ax_d, tight=False)

# Save
plt.savefig('figure4.pdf', dpi=300, bbox_inches='tight')
plt.savefig('figure4.png', dpi=300, bbox_inches='tight')
```

Features:
- Consistent styling across all panels
- Panel labels (A, B, C, D) in consistent positions
- Grayscale-safe colors
- Appropriate chart types for each data type
- Tight layout, minimal whitespace
- High-resolution exports
```

---

## Common Workflow Patterns Summary

| Scenario | Skills Used | Key Steps |
|----------|-------------|-----------|
| **Research figure** | beautiful-data-viz | Select chart → Choose palette → Apply styling → Export |
| **Analysis notebook** | jupyter + beautiful-data-viz | Structure → Load data → Analyze → Plot → Validate |
| **Business dashboard** | plotly-dashboard | Story → Layout → Theme → Callbacks → Optimize → Document |
| **Web scraping** | agent-browser → beautiful-data-viz | Scrape → Structure data → Visualize |
| **Presentation** | beautiful-data-viz | Large fonts → High contrast → Simple layouts |

---

## Tips for Success

1. **Specify medium** - "for paper", "for slides", "for notebook"
2. **Mention accessibility** - "grayscale-safe", "colorblind-safe"
3. **Describe message** - What should viewer understand instantly?
4. **Request validation** - "ensure reproducible", "validate in grayscale"
5. **Provide context** - Data characteristics, audience, constraints

