---
name: notebooks
description: Author, run and convert marimo or Jupyter notebooks. Use when delivering an analysis notebook executed end to end with figures embedded.
---

# Notebooks

A single skill for authoring, validating, and delivering reproducible analysis notebooks. Marimo is the default format; Jupyter is supported for existing `.ipynb` files and when a downstream tool requires JSON. Conversion between the two formats is part of this skill.

A notebook is not "done" until it has been executed end-to-end on a fresh kernel and every figure is embedded in the delivered file.

## Instructions

1. **Pick the format.**
   - New notebook: write a marimo `.py` notebook. Use the canonical cell layout (one concept per cell, final expression renders, no `if` guards around outputs, no `try/except` for control flow).
   - Existing `.ipynb` to extend or polish: keep it as Jupyter unless the user asks to convert.
   - Conversion: see "Convert between marimo and Jupyter" below.

2. **Outline before coding.** Write the notebook plan (purpose, data sources, analysis steps, expected outputs/plots) as the first markdown cell, then implement against that plan.

3. **Keep marimo cells clean.** These are hard rules for every `.py` notebook:
   - Markdown cells use one plain triple-quoted string: `mo.md(r"""...""")` or `mo.md(f"""...""")` only when interpolation is required. Put the prose directly inside the string; never paste quoted string fragments such as `" ... "` lines inside the markdown body.
   - Do not leave empty generated cells, whitespace-only cells, or `@app.cell def _(): return` placeholders. Remove them before final verification.
   - Do not accept a marimo "fix" prompt blindly. If one is accepted during interactive editing, inspect the diff immediately and remove unintended PEP 723/header/cell churn.

4. **Set up the kernel and dependencies.**
   - **Marimo.** Pin dependencies in the PEP 723 script header at the top of the `.py` file:
     ```python
     # /// script
     # requires-python = ">=3.12"
     # dependencies = [
     #     "marimo",
     #     "polars",
     #     "duckdb",
     #     "matplotlib",
     #     # ... add every import used in the notebook
     # ]
     # ///
     ```
     Run with `uvx marimo run --sandbox <notebook.py>` or edit interactively with `uvx marimo edit --sandbox <notebook.py>`. The sandbox reads the header and resolves the notebook environment.
   - **Jupyter.** Register a named ipykernel for the project's pixi env *before* the first execution and pin the kernel in the notebook metadata. The kernel name is mandatory: the generic `python3` kernel leaks the system interpreter.
     ```bash
     pixi run python -m ipykernel install --user --name <project> --display-name "<project> (pixi)"
     ```
     Then in `<notebook>.ipynb` confirm:
     ```json
     "kernelspec": {"name": "<project>", "display_name": "<project> (pixi)"}
     ```
     Add every import used in the notebook to `pixi.toml` so the kernel can resolve it from a clean install.

5. **Load data with project-relative paths.** Prefer DuckDB for TSV/Parquet (`duckdb.read_csv`, `duckdb.read_parquet`). Avoid absolute paths and `~`. Avoid hidden state from the runtime working directory.

6. **Run checks and all cells to generate plots.** Execute the notebook headlessly on a fresh kernel before delivery:
   - Marimo: run `uvx marimo check --strict <notebook.py>` before export. Then run `uvx marimo export ipynb <notebook.py> -o <notebook.executed.ipynb> --include-outputs --sandbox -f`. For a deterministic HTML artifact, use `uvx marimo export html <notebook.py> -o <notebook.html> --sandbox -f`. Run the strict check again after the final edit/export cycle.
   - Jupyter: resolve the installed skill root, then run its self-provisioning helper (or use the equivalent repo path while developing this skill):
     ```bash
     NOTEBOOKS_SKILL="${NOTEBOOKS_SKILL:-$HOME/.agents/skills/notebooks}"
     uv run --script "$NOTEBOOKS_SKILL/scripts/execute_notebook.py" \
       <notebook.ipynb> --kernel <project>
     ```
     The helper writes `<notebook>.executed.ipynb`. `pixi run jupyter nbconvert --to notebook --execute --inplace <notebook.ipynb>` is also valid when Jupyter is declared in the project environment.

7. **Evaluate the plots, then refine.** This step is required. Figures follow `/beautiful-data-viz` (greyscale first, color only to encode information, colorblind-safe, no in-plot titles on manuscript figures); [references/plot_style.md](references/plot_style.md) has the notebook style cell. After the run-all execution:
   - Open the executed notebook (or exported HTML) and visually inspect every figure.
   - Check for: empty axes, mis-scaled axes (log when linear was intended or vice versa), missing labels or legends, overlapping ticks, illegible font sizes at target output size, color that encodes nothing, colorbars without units, NaN-driven gaps, axis ranges clipping data, broken layouts.
   - Place each caption below its figure: the figure cell comes first and the caption markdown cell follows it.
   - If a figure is wrong or unclear, edit the source cell and re-run end-to-end. Repeat until each figure communicates what the surrounding markdown says it communicates.
   - Record what changed between revisions in a brief "Figure revision log" markdown cell or in the run log.

8. **Deliver pre-executed notebooks.** The artifact handed back to the user must:
   - Have every cell executed against the registered kernel.
   - Embed every figure (PNG / SVG cell outputs) directly in the `.ipynb` (or in the marimo HTML export).
   - Be reproducible from a clean clone: a new environment built from the PEP 723 header (marimo) or `pixi install` + `jupyter nbconvert --to notebook --execute` (Jupyter) must reproduce the same notebook end-to-end.

9. **Convert between marimo and Jupyter** when the user asks for it:
   - Use `scripts/convert_notebook.py` for a pinned conversion path. The fixtures under `fixtures/` exercise both directions. Replace `<PROJECT_NAME>` and `<PIXI_PROJECT_KERNEL>` in copied Jupyter templates with the actual Pixi kernel before execution.
   - `.ipynb` → marimo `.py`: `uvx marimo convert <notebook.ipynb> -o <notebook.py>`, then `uvx marimo check --strict <notebook.py>`, then clean up Jupyter artifacts (`display()` calls, `%magic`s, indented final expressions, ipywidget usage). See `references/widgets.md` and `references/latex.md` for ipywidget→marimo and MathJax→KaTeX mappings.
   - marimo `.py` → `.ipynb`: `uvx marimo export ipynb <notebook.py> -o <notebook.ipynb> --include-outputs --sandbox -f`.
   - After conversion, re-run step 6 (check/execute), step 7 (inspect plots), and step 8 (deliver pre-executed).

## Quick Reference

| Task | Action |
|------|--------|
| Resolve bundled helpers | `NOTEBOOKS_SKILL="${NOTEBOOKS_SKILL:-$HOME/.agents/skills/notebooks}"` |
| Author marimo notebook | Edit `.py`, run `uvx marimo edit --sandbox <notebook.py>` |
| Author Jupyter notebook | Register pixi kernel, set notebook `kernelspec`, edit `.ipynb` |
| Lint marimo notebook | `uvx marimo check --strict <notebook.py>` |
| Execute marimo headlessly | `uvx marimo export ipynb <notebook.py> -o <executed.ipynb> --include-outputs --sandbox -f` |
| Execute Jupyter headlessly | `uv run --script "$NOTEBOOKS_SKILL/scripts/execute_notebook.py" <notebook.ipynb> --kernel <project>` |
| Convert `.ipynb` → marimo | `uvx marimo convert <notebook.ipynb> -o <notebook.py>` |
| Convert marimo → `.ipynb` | `uvx marimo export ipynb <notebook.py> -o <notebook.ipynb> --include-outputs --sandbox -f` |
| Marimo references | `references/notebook_structure.md`, `references/UI.md`, `references/SQL.md`, `references/STATE.md`, `references/EXPORTS.md`, `references/PYTEST.md`, `references/TOP-LEVEL-IMPORTS.md`, `references/DEPLOYMENT.md` |
| Conversion references | `references/widgets.md`, `references/latex.md` |
| Pixi + Jupyter | `references/pixi_jupyter.md` |
| Plot style | `references/plot_style.md` |
| Data loading (DuckDB/TSV/Parquet) | `references/data_loading_duckdb.md` |
| Definition-of-done checklist | `references/verification.md` |
| Templates | `templates/marimo_notebook_template.py`, `templates/jupyter_kiss_template.py` |
| Headless executor | `scripts/execute_notebook.py` |
| Jupyter structure linter | `uv run --script "$NOTEBOOKS_SKILL/scripts/lint_notebook_structure.py" <notebook.ipynb>` |
| Pinned converter | `uv run --script "$NOTEBOOKS_SKILL/scripts/convert_notebook.py" --help` |

## Input Requirements

- Notebook scope and goals (what question, what data, what output).
- Data file paths (TSV/Parquet preferred for DuckDB ingestion).
- For marimo: `uv` available on PATH, or `marimo` installed in the environment.
- For Jupyter: `pixi` available and a `pixi.toml` (or equivalent env spec) for the project.

## Output

- A reproducible notebook (`.py` for marimo, `.ipynb` for Jupyter) with narrative markdown cells, code cells, and embedded figures.
- A pre-executed copy (`<notebook>.executed.ipynb` or an `.html` export) where every cell has been run on a fresh kernel.
- A short "Figure revision log" recording any plot-revision rounds.

## Quality Gates

- [ ] Notebook format chosen explicitly (marimo by default; Jupyter only when justified or when the input is `.ipynb`).
- [ ] Kernel registered and pinned: marimo PEP 723 header complete, or Jupyter `kernelspec` set to a named pixi kernel.
- [ ] Every Python import used in the notebook is declared in the dependency spec (PEP 723 header or `pixi.toml`).
- [ ] Data paths are project-relative and verified to exist.
- [ ] Headless run-all succeeds on a fresh kernel: marimo export uses `--include-outputs --sandbox`, or Jupyter execution exits zero.
- [ ] Every figure is inspected after execution; any figure that fails the visual checks above triggers a code revision and re-run.
- [ ] Figures pass the `/beautiful-data-viz` quality gates: grey unless color encodes information, no in-plot titles on manuscript figures, caption cell below the figure.
- [ ] Delivered notebook has every cell pre-executed with figures embedded; users do not have to run the notebook to see the plots.
- [ ] For marimo: `uvx marimo check --strict <notebook.py>` passes before and after export.
- [ ] For marimo: no malformed markdown cells, quoted-string fragments inside `mo.md(...)`, trailing empty cells, or `return`-only placeholder cells remain.
- [ ] Template dependencies use bounded versions and no delivered notebook retains the literal `<PIXI_PROJECT_KERNEL>` placeholder.
- [ ] Jupyter-to-marimo and marimo-to-Jupyter conversions both pass the fixture gate.

## Examples

### Example 1: New marimo notebook

```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["marimo", "polars", "duckdb", "matplotlib"]
# ///

import marimo
app = marimo.App(width="medium")

@app.cell
def _():
    import marimo as mo
    import polars as pl
    import duckdb
    import matplotlib.pyplot as plt
    return mo, pl, duckdb, plt

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Analysis notebook

    This notebook loads project data, validates it, and renders the requested figures.
    """)
    return

@app.cell
def _(duckdb):
    df = duckdb.read_parquet("data/measurements.parquet").pl()
    df.head()
    return (df,)

@app.cell
def _(df, plt):
    _fig, _ax = plt.subplots(figsize=(5, 3.2))
    _ax.scatter(df["x"], df["y"], s=10)
    _ax.set_xlabel("x (units)"); _ax.set_ylabel("y (units)")
    _fig
    return
```

Then:
```bash
uvx marimo check --strict notebook.py
uvx marimo export ipynb notebook.py -o notebook.executed.ipynb \
  --include-outputs --sandbox -f
uvx marimo check --strict notebook.py
```

### Example 2: Jupyter notebook with a named pixi kernel

```bash
# One-time kernel registration in the project root:
pixi run python -m ipykernel install --user --name myproject --display-name "myproject (pixi)"

# After authoring, run end-to-end on a fresh kernel:
NOTEBOOKS_SKILL="${NOTEBOOKS_SKILL:-$HOME/.agents/skills/notebooks}"
uv run --script "$NOTEBOOKS_SKILL/scripts/execute_notebook.py" notebooks/analysis.ipynb \
  --kernel myproject \
  --out notebooks/analysis.executed.ipynb
```

### Example 3: Convert `.ipynb` to marimo

```bash
uvx marimo convert notebooks/legacy.ipynb -o notebooks/legacy.py
uvx marimo check --strict notebooks/legacy.py
uvx marimo export ipynb notebooks/legacy.py -o notebooks/legacy.executed.ipynb \
  --include-outputs --sandbox -f
```

## Troubleshooting

**Issue:** Jupyter notebook executes locally but fails on a teammate's machine.
**Solution:** The kernel was unpinned (`python3`) or used a packaged interpreter outside the project's pixi env. Re-register a named kernel and pin it in the notebook `kernelspec`.

**Issue:** Marimo cell does not render a figure.
**Solution:** The figure must be the final expression of the cell. Indented expressions inside `if` blocks or expressions buried before other statements will not render.

**Issue:** Figures look correct interactively but the executed file shows empty plots.
**Solution:** Code is mutating shared state across cells (e.g. `plt.gcf()` reuse). Build a fresh figure per cell (in marimo `_fig, _ax = plt.subplots(...)`, because a global `fig` defined in two cells is an error) and make the figure the final expression.

**Issue:** Converted notebook fails `marimo check`.
**Solution:** Remove leftover `display(...)` calls, drop `%magic` lines that have no marimo equivalent, and rewrite ipywidget usage using `mo.ui.*` per `references/widgets.md`.

**Issue:** Every matplotlib figure appears twice in the executed Jupyter notebook.
**Solution:** The inline backend's `flush_figures` post-execute hook auto-displays every open figure (`display_data`), and the cell's `fig` return value produces a second copy (`execute_result`). Unregister the hook in the preamble cell:
```python
plt.ioff()
try:
    from matplotlib_inline.backend_inline import flush_figures
    get_ipython().events.unregister("post_execute", flush_figures)
except Exception:
    pass
```
With this fix, only the cell's final `fig` expression renders. For figures inside `if/else` blocks (where `fig` is not a top-level expression and therefore not captured as `execute_result`), use `display(fig)` explicitly instead of bare `fig`. Do not use `mpl.use("agg")` as a workaround; it disables `_repr_png_()` entirely and produces zero images.
