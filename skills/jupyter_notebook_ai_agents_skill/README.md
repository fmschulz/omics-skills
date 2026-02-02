# Notebook KISS Builder & Verifier (Pixi + DuckDB)

This folder is an **Agent Skill** that teaches an AI agent to:
- build/refactor Jupyter notebooks with a clean narrative structure,
- use per-directory Pixi environments via `pixi.toml` + `pixi-kernel`,
- load data reliably (DuckDB + TSV/Parquet) using correct paths,
- generate polished plots with minimal whitespace,
- *never* claim completion until the notebook passes a full run-all-cells execution.

Start here: `SKILL.md`
