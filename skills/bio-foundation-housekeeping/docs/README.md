# Tool Documentation

Last verified: 2026-07-11
Tool version/release checked: Pixi v0.69.0; LinkML v1.11.1; Pydantic v2.13.4; DuckDB v1.5.3
Official docs/manual: See linked per-tool guides in this directory.
Release/source: See linked per-tool guides in this directory.

This directory contains practical usage guides for the core tools used in bio-foundation-housekeeping.

## Tools Covered

### [Pixi](pixi.md)
**Version checked**: v0.69.0
**Purpose**: Developer workflow and environment management for multi-platform, language-agnostic workspaces
**Key Use**: Creating locked conda-forge and bioconda environments

**Quick Start**:
```bash
pixi init myproject --channel conda-forge --channel bioconda
cd myproject
pixi add python biopython pysam
pixi install
```

### [LinkML](linkml.md)
**Version checked**: v1.11.1
**Purpose**: Schema language for typed records authored in YAML
**Key Use**: Defining metadata schemas and generating Pydantic models

**Quick Start**:
```bash
SKILL_ROOT=~/.agents/skills/bio-foundation-housekeeping
uv run --script "$SKILL_ROOT/scripts/generate_models.py" \
  --schema "$SKILL_ROOT/schemas/project-metadata.yaml" \
  --output ./schemas/generated/project_metadata.py \
  --expect-class MetadataBundle
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

1. **Pixi**: Resolves the project environment and lockfile.
2. **LinkML**: Defines sample, run, file, result, and provenance records.
3. **Pydantic**: Validates runtime data with the generated models.
4. **DuckDB**: Catalogs validated Parquet tables and their checksums.

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

## Fixture workflow

Run `../scripts/build_metadata_catalog.py` with `../schemas/project-metadata.yaml` and the bundled JSON fixtures. The driver validates record fields, identifiers, and foreign keys before publishing generated models, Parquet tables, or DuckDB.
