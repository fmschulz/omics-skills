# Examples

## 1) Start JupyterLab with Pixi
From the project directory (where `pixi.toml` lives):

```bash
pixi run jupyter lab
```

## 2) Lint notebook structure
```bash
python scripts/lint_notebook_structure.py notebooks/01_analysis.ipynb --require-local-pixi
```

## 3) Execute notebook end-to-end (validation gate)
```bash
python scripts/execute_notebook.py notebooks/01_analysis.ipynb --out notebooks/01_analysis.executed.ipynb
```
