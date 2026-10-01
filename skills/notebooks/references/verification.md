# Verification and “definition of done”

## Why this exists
Notebooks often “work” only because of hidden state, out-of-order execution, or a messy environment.
This skill requires a strict execution gate.

## Definition of done (must satisfy all)
A notebook is “done” only if:

1. **Fresh-kernel execution succeeds**
   - Restart kernel
   - Run all cells top → bottom
   - No exceptions
2. **Outputs are sane**
   - Data loads from expected paths
   - Shapes / counts match expectations
   - Validation checks pass (keys, null rates, ranges)
3. **Narrative is complete**
   - Markdown above every code cell
   - Sections follow a clear arc: purpose → data → method → results
4. **Plots render cleanly**
   - tight layout, labels, grey unless color encodes information (see `/beautiful-data-viz`)
5. **Re-run instructions exist**
   - in the notebook header and/or README

## Recommended execution methods
### In UI (JupyterLab/Notebook)
Use **Restart Kernel and Run All Cells**.

### In automation (preferred if available)
Use the installed skill's `scripts/execute_notebook.py`, which provisions its dependencies through PEP 723, executes the notebook via **nbclient**, and writes an executed notebook artifact.

Example:
```bash
NOTEBOOKS_SKILL="${NOTEBOOKS_SKILL:-$HOME/.agents/skills/notebooks}"
uv run --script "$NOTEBOOKS_SKILL/scripts/execute_notebook.py" \
  notebooks/01_analysis.ipynb --out notebooks/01_analysis.executed.ipynb
```

## Output inspection checklist
After running all cells, verify:
- no truncated errors in cell outputs
- tables show expected columns
- plots appear and are labeled
- exported files exist where markdown says they will

## Handling randomness
If results vary run-to-run:
- set seeds (Python, NumPy, ML libs)
- document it in markdown
- if nondeterminism is inherent, state it clearly
