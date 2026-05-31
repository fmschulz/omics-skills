# Tool Documentation

Last verified: 2026-05-30
Tool version/release checked: Pixi v0.69.0; LinkML v1.11.1; Pydantic v2.13.4; DuckDB v1.5.3
Official docs/manual: See linked per-tool guides in this directory.
Release/source: See linked per-tool guides in this directory.

This directory contains practical usage guides for the core tools used in bio-foundation-housekeeping.

## Tools Covered

### [Pixi](pixi.md)
**Version checked**: v0.69.0
**Purpose**: Developer workflow and environment management for multi-platform, language-agnostic workspaces
**Key Use**: Creating reproducible conda/mamba environments with lockfiles

**Quick Start**:
```bash
pixi init myproject --channel conda-forge --channel bioconda
cd myproject
pixi add python=3.11 biopython pysam
pixi install
```

### [LinkML](linkml.md)
**Version checked**: v1.11.1
**Purpose**: Flexible modeling language for authoring schemas in YAML
**Key Use**: Defining metadata schemas and generating Pydantic models

**Quick Start**:
```bash
pip install linkml
linkml generate pydantic --black schema.yaml > models.py
linkml validate --schema schema.yaml data.yaml
```

### [Pydantic](pydantic.md)
**Version checked**: v2.13.4
**Purpose**: Data validation using Python type hints
**Key Use**: Runtime validation of sample metadata and configuration

**Quick Start**:
```python
from pydantic import BaseModel, Field

class Sample(BaseModel):
    sample_id: str
    organism: str
    coverage: float = Field(gt=0)

sample = Sample(sample_id="S001", organism="Human", coverage=30.5)
```

### [DuckDB](duckdb.md)
**Version checked**: v1.5.3
**Purpose**: In-process SQL OLAP database
**Key Use**: Creating data catalogs and querying Parquet files

**Quick Start**:
```python
import duckdb
conn = duckdb.connect('catalog.duckdb')
conn.execute("CREATE TABLE samples AS SELECT * FROM 'samples.parquet'")
results = conn.execute("SELECT * FROM samples WHERE coverage > 30").df()
```

## Documentation Structure

Each tool guide includes:
- Official documentation URL
- Installation commands
- Key command-line flags and options
- Common usage examples for project setup
- Input/output formats
- Performance tips
- Bioinformatics-specific usage patterns

## Usage in bio-foundation-housekeeping

These tools work together in the skill workflow:

1. **Pixi**: Sets up reproducible environment with all dependencies
2. **LinkML**: Defines metadata schemas for samples, runs, etc.
3. **Pydantic**: Validates data at runtime using generated models
4. **DuckDB**: Catalogs validated Parquet files for efficient querying

The default pattern is schema-first. Define records in LinkML, validate incoming metadata, parse/coerce values through Pydantic models, write normalized Parquet, and then register those Parquet files in DuckDB. Avoid loading raw CSV/JSON directly into the catalog unless the raw table is clearly marked as staging and excluded from downstream analysis.

## Official Documentation Links

- Pixi: https://pixi.sh/latest/
- LinkML: https://linkml.io/linkml/
- Pydantic: https://docs.pydantic.dev/latest/
- DuckDB: https://duckdb.org/docs/stable/

## Release Sources Checked

- Pixi: https://github.com/prefix-dev/pixi/releases/tag/v0.69.0
- LinkML: https://github.com/linkml/linkml/releases/tag/v1.11.1
- Pydantic: https://github.com/pydantic/pydantic/releases/tag/v2.13.4
- DuckDB: https://github.com/duckdb/duckdb/releases/tag/v1.5.3

## Notes

- All guides focus on practical bioinformatics use cases
- Examples emphasize reproducibility and data validation
- Performance tips are tailored for typical genomics workflows
- Documentation will be updated as tool versions evolve
