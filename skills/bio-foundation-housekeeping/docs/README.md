# Tool Documentation

Last verified: 2026-07-11
Tool version/release checked: Pixi v0.69.0; LinkML v1.11.1; Pydantic v2.13.4; DuckDB v1.5.3
Official docs/manual: https://pixi.sh/latest/ ; https://linkml.io/linkml/ ; https://docs.pydantic.dev/latest/ ; https://duckdb.org/docs/stable/
Release/source: https://github.com/prefix-dev/pixi/releases/tag/v0.69.0 ; https://github.com/linkml/linkml/releases/tag/v1.11.1 ; https://github.com/pydantic/pydantic/releases/tag/v2.13.4 ; https://github.com/duckdb/duckdb/releases/tag/v1.5.3

Versions checked for the bio-foundation-housekeeping skill. The scripts pin LinkML and Pydantic themselves; DuckDB and Pixi come from the project's environment.

The pattern is schema-first: define records in LinkML, validate incoming metadata through the generated Pydantic models, write normalized Parquet, then register those Parquet files in DuckDB. Load raw CSV or JSON into the catalog only as a clearly marked staging table that downstream analysis excludes.

Fixture workflow: run `../scripts/build_metadata_catalog.py` with `../schemas/project-metadata.yaml` and the bundled JSON fixtures. The driver validates record fields, identifiers, and foreign keys before it publishes generated models, Parquet tables, or DuckDB.
