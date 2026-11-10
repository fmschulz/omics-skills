# Tool Documentation

Last verified: 2026-05-30
Tool version/release checked: DuckDB v1.5.3; scikit-learn 1.8.0; XGBoost v3.2.0
Official docs/manual: https://duckdb.org/docs/stable/ ; https://scikit-learn.org/stable/ ; https://xgboost.readthedocs.io/
Release/source: https://github.com/duckdb/duckdb/releases/tag/v1.5.3 ; https://github.com/scikit-learn/scikit-learn/releases/tag/1.8.0 ; https://github.com/dmlc/xgboost/releases/tag/v3.2.0

Versions checked for the bio-stats-ml-reporting skill. Declare the tools in the analysis project's `pixi.toml` (this skill ships none):

```bash
pixi add duckdb scikit-learn xgboost
```

- **[DuckDB](duckdb.md)**: SQL joins over Parquet and TSV results, CLI usage, performance tips.
- **scikit-learn** and **XGBoost**: baseline models and cross-validation; see the official docs above.
- **Prediction validation**: `../scripts/validate_predictions.py` (see `../SKILL.md`).
