---
name: notebooks
description: Author, run and convert marimo or Jupyter notebooks. Use when delivering an analysis notebook executed end to end with figures embedded.
---

# Notebooks

Author, validate and deliver reproducible analysis notebooks in marimo or Jupyter, and convert between the two. Installed at `~/.agents/skills/notebooks`; set `NOTEBOOKS_SKILL="${NOTEBOOKS_SKILL:-$HOME/.agents/skills/notebooks}"` for the helper scripts.

A notebook is not "done" until it has been executed end to end on a fresh kernel and every figure is embedded in the delivered file.

## Instructions

1. **Pick the format.** Marimo is the default for a new standalone notebook. Use Jupyter when the project's record format is Jupyter (for example a bester project record) or the project already uses `.ipynb`; keep an existing `.ipynb` as Jupyter unless the user asks to convert.
   - Marimo layout: one concept per cell, final expression renders, no `if` guards around outputs, no `try/except` for control flow.

2. **Outline before coding.** Write the notebook plan (purpose, data sources, analysis steps, expected outputs/plots) as the first markdown cell, then implement against that plan.

3. **Keep marimo cells clean.** These are hard rules for every `.py` notebook:
   - Markdown cells use one plain triple-quoted string: `mo.md(r"""...""")` or `mo.md(f"""...""")` only when interpolation is required. Put the prose directly inside the string; never paste quoted string fragments such as `" ... "` lines inside the markdown body.
   - Do not leave empty generated cells, whitespace-only cells, or `@app.cell def _(): return` placeholders. Remove them before final verification.
   - Do not accept a marimo "fix" prompt blindly. If one is accepted during interactive editing, inspect the diff immediately and remove unintended PEP 723/header/cell churn.

4. **Set up the kernel and dependencies.**
   - **Marimo.** Declare dependencies with lower bounds in the PEP 723 script header at the top of the `.py` file (no upper bounds, no exact pins; the sandbox resolves the newest release):
     ```python
     # /// script
     # requires-python = ">=3.12"
     # dependencies = [
     #     "marimo>=0.23",
     #     "polars>=1.0",
     #     "duckdb>=1.1",
     #     "matplotlib>=3.9",
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
   - Jupyter: run the self-provisioning helper:
     ```bash
     uv run --script "$NOTEBOOKS_SKILL/scripts/execute_notebook.py" \
       <notebook.ipynb> --kernel <project>
     ```
     The helper writes `<notebook>.executed.ipynb` and sets its kernelspec name to the `--kernel` value. Without `--kernel` it uses the notebook's own kernelspec, else `python3`. `pixi run jupyter nbconvert --to notebook --execute --inplace <notebook.ipynb>` is also valid when Jupyter is declared in the project environment.

7. **Evaluate the plots, then refine.** This step is required. Figures follow `/beautiful-data-viz`; [references/plot_style.md](references/plot_style.md) has the notebook style cell. After the run-all execution:
   - Open the executed notebook (or exported HTML) and inspect every figure.
   - Check for: empty axes, mis-scaled axes (log versus linear), missing labels or legends, overlapping ticks, illegible fonts at target size, colour that encodes nothing, colourbars without units, NaN-driven gaps, ranges that clip data, broken layouts.
   - If a figure is wrong or unclear, edit the source cell and re-run end to end. Record revisions in a brief "Figure revision log" markdown cell or in the run log.

8. **Deliver pre-executed notebooks.** The delivered artifact has every cell executed against the registered kernel, every figure embedded (PNG or SVG cell outputs in the `.ipynb`, or the marimo HTML export), re-run instructions in the header or README, and seeds set where results are random. It must reproduce end to end from a clean clone: a new environment built from the PEP 723 header (marimo) or `pixi install` plus `jupyter nbconvert --to notebook --execute` (Jupyter). No delivered notebook keeps the literal `<PIXI_PROJECT_KERNEL>` placeholder.

9. **Convert between marimo and Jupyter** when the user asks for it:
   - Use `scripts/convert_notebook.py`, which brings its own marimo through its PEP 723 header. The fixtures under `fixtures/` exercise both directions. Replace `<PROJECT_NAME>` and `<PIXI_PROJECT_KERNEL>` in copied Jupyter templates with the actual Pixi kernel before execution.
   - `.ipynb` → marimo `.py`: `uv run --script "$NOTEBOOKS_SKILL/scripts/convert_notebook.py" <notebook.ipynb> --to marimo --out <notebook.py>`, then `uvx marimo check --strict <notebook.py>`, then clean up Jupyter artifacts (`display()` calls, `%magic`s, indented final expressions, ipywidget usage). See [references/widgets.md](references/widgets.md) and [references/latex.md](references/latex.md) for ipywidget→marimo and MathJax→KaTeX mappings.
   - marimo `.py` → `.ipynb`: `uv run --script "$NOTEBOOKS_SKILL/scripts/convert_notebook.py" <notebook.py> --to jupyter --out <notebook.ipynb>`. The converter writes no cell outputs; to embed them, use the `uvx marimo export ipynb ... --include-outputs --sandbox -f` command of step 6.
   - After conversion, re-run step 6 (check/execute), step 7 (inspect plots), and step 8 (deliver pre-executed).

10. **References.** Marimo: [references/notebook_structure.md](references/notebook_structure.md), [references/UI.md](references/UI.md), [references/STATE.md](references/STATE.md), [references/EXPORTS.md](references/EXPORTS.md). For testing, SQL cells, top-level imports and deployment, see the marimo documentation at https://docs.marimo.io/. Conversion: [references/widgets.md](references/widgets.md), [references/latex.md](references/latex.md). Pixi and Jupyter: [references/pixi_jupyter.md](references/pixi_jupyter.md). DuckDB loading: [references/data_loading_duckdb.md](references/data_loading_duckdb.md). Templates (start a new notebook from one): [templates/marimo_notebook_template.py](templates/marimo_notebook_template.py), [templates/jupyter_kiss_template.py](templates/jupyter_kiss_template.py). Both import `beautiful_style`: copy `assets/beautiful_style.py` from the beautiful-data-viz skill next to the notebook. Jupyter structure linter: `uv run --script "$NOTEBOOKS_SKILL/scripts/lint_notebook_structure.py" <notebook.ipynb>`.

## Input Requirements

Notebook scope (question, data, outputs) and data paths (TSV or Parquet preferred). Marimo needs `uv`; Jupyter needs `pixi` and a `pixi.toml`.

## Output

A notebook (`.py` for marimo, `.ipynb` for Jupyter) with narrative cells, code and embedded figures, plus a pre-executed copy (`<notebook>.executed.ipynb` or an `.html` export).

## Quality Gates

- `uvx marimo check --strict <notebook.py>` passes before and after export, and no malformed markdown cells, quoted-string fragments inside `mo.md(...)`, or `return`-only placeholder cells remain.
- Every import is declared in the PEP 723 header or `pixi.toml`; template dependencies use lower bounds only (`>=`), with no upper bounds and no exact pins.
- Data paths are project-relative and verified to exist.
- Both conversion directions pass the fixture gate.

## Troubleshooting

**Issue:** Jupyter notebook executes locally but fails on a teammate's machine.
**Solution:** The kernel was unpinned (`python3`) or used a packaged interpreter outside the project's pixi env. Re-register a named kernel and pin it in the notebook `kernelspec`.

**Issue:** Marimo cell does not render a figure.
**Solution:** The figure must be the final expression of the cell. Indented expressions inside `if` blocks or expressions buried before other statements will not render.

**Issue:** Figures look correct interactively but the executed file shows empty plots.
**Solution:** Code is mutating shared state across cells (e.g. `plt.gcf()` reuse). Build a fresh figure per cell (in marimo `_fig, _ax = plt.subplots(...)`, because a global `fig` defined in two cells is an error) and make the figure the final expression.

**Issue:** Converted notebook fails `marimo check`.
**Solution:** Remove leftover `display(...)` calls, drop `%magic` lines that have no marimo equivalent, and rewrite ipywidget usage using `mo.ui.*` per [references/widgets.md](references/widgets.md).

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
