# Pixi + Jupyter kernel setup (per-directory pixi.toml)

## Goal
The notebook should run in a **per-directory Pixi environment** so that:
- dependencies are reproducible,
- the correct kernel is auto-selected based on the nearest `pixi.toml`,
- teammates can run the notebook without manual interpreter hunting.

Pixi supports this with **pixi-kernel**, which searches for `pixi.toml` (or `pyproject.toml`) in the notebook’s directory or any parent directory and uses that environment to start the kernel.

## Recommended setup (JupyterLab)
From the notebook/project directory:

```bash
pixi init
pixi add python
pixi add jupyterlab pixi-kernel ipykernel
pixi run jupyter lab
```

Then select the Pixi kernel in JupyterLab.

## Minimal `pixi.toml` conventions
- The `pixi.toml` should live in the **same directory as the notebook** (or a parent directory).
- Keep dependencies minimal; only add what the notebook imports.
- Prefer pinning versions for stability when notebooks are shared.

See `templates/pixi.toml` for a starting point.

## VS Code notes (if relevant)
Some Pixi kernel implementations may have limitations with VS Code kernel discovery. If VS Code can’t see the kernel, the fallback is often:
- run JupyterLab via `pixi run jupyter lab`, or
- explicitly install an ipykernel (project-specific) and select it.

(Only include these notes if the user uses VS Code.)

## Quick reproducibility check
- A fresh clone of the repo should be runnable with:
  1) `pixi run jupyter lab`
  2) open notebook
  3) **Restart & Run All**
