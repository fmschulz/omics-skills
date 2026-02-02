---
name: jgi-lakehouse
description: Queries and explores the JGI Lakehouse (Dremio + Iceberg) using safe SQL patterns via REST API. Use when working with JGI genomics data, GOLD projects, IMG annotations, or when the user mentions Dremio, Lakehouse, or needs schema discovery.
---

# JGI Lakehouse Skill

## TL;DR for Agents

**What is it?** JGI's unified data warehouse with genomics data from GOLD, IMG, Mycocosm, Phytozome.

**SQL Dialect:** ANSI SQL (not PostgreSQL). Key differences:
- Use `CAST(x AS type)` not `::`
- Use `REGEXP_LIKE()` not `~`
- Identifiers with dashes need double quotes: `"gold-db-2 postgresql"`

**Quick Start:**
```sql
-- Discover
SHOW SCHEMAS IN "gold-db-2 postgresql";
DESCRIBE "gold-db-2 postgresql".gold.project;

-- Query (always use LIMIT!)
SELECT gold_id, project_name, ecosystem
FROM "gold-db-2 postgresql".gold.project
WHERE is_public = 'Yes'
LIMIT 100;
```

**Key Sources:** `"gold-db-2 postgresql".gold.*` (projects, samples, taxonomy), `"img-db-2 postgresql".img_core_v400.*` (genes, annotations), `"myco-db-1 mysql".<organism>.*` (fungi), `"plant-db-7 postgresql".*` (plants)

**Docs:** `docs/sql-quick-reference.md` (syntax), `docs/data-catalog.md` (all tables)

---

## When to use
- User asks for data in the JGI Lakehouse, Dremio SQL, Iceberg time travel, or dataset discovery.
- User needs safe query patterns, schema inspection, or performance guidance (reflections, VDS).

## Core context
- Instance: https://lakehouse.jgi.lbl.gov
- Engine: Dremio (ANSI SQL, not PostgreSQL)
- Storage: Iceberg tables on object storage + federated PostgreSQL/MySQL sources
- Spaces: Phytozome, Mycocosm, JDP, IMG, GOLD

## Operational rules (must follow)
1. Prefer VDS (views) over physical tables.
2. Never run SELECT * without a LIMIT (default 100).
3. Always inspect schema before complex joins.
4. If performance issues arise, check reflections and recommend the right type.
5. Use Iceberg time travel syntax for historical questions.

## Expected tools
These tool interfaces should be registered in your agent runtime. See `references/tools.json` for a starter schema.
- list_catalogs(): list available spaces/schemas
- describe_table(table_path: string): return columns and types
- execute_lakehouse_query(sql_query: string): run SQL over Arrow Flight

## Query workflow
1. **Read `examples/` FIRST** - contains working patterns with documented pitfalls
2. Check `docs/data-catalog.md` for table/column reference
3. If not documented, discover via `SHOW SCHEMAS`, `DESCRIBE`
4. Write minimal SQL with LIMIT and explicit columns
5. Return results plus the SQL used

## Examples (MUST READ for complex queries)

**Before writing joins or cross-database queries, read these:**

| Example | When to Use |
|---------|-------------|
| `examples/01-find-16s-rrna-genes.md` | Gene searches by taxonomy |
| `examples/02-download-genomes-by-taxonomy.md` | Getting genome sequences |
| `examples/03-cross-database-joins.md` | **Any GOLD↔IMG↔SRA joins** |

### Critical Pitfalls (from examples)

| Wrong | Correct |
|-------|---------|
| `project.ecosystem` | Join `study` via `master_study_id` |
| `rnaseq_experiment.experiment_id` | `exp_oid` |
| `sra_experiment_v2.platform` | `library_instrument` |
| `WHERE family = 'X'` | `LIKE '%X%'` on display name |
| Get sequences from Lakehouse | Download from NCBI |

## Implementation guidance
- Use Arrow Flight (pyarrow.flight) with a bearer token.
- Read Dremio token from DREMIO_PAT environment variable.
- Do not log secrets or tokens.
- If query fails, return a structured error with next steps.

## Authentication

Token stored in `DREMIO_PAT` environment variable (30-hour lifetime).

**Quick setup:**
```bash
./scripts/get_dremio_token.sh username password > ~/.secrets/dremio_pat
chmod 600 ~/.secrets/dremio_pat
export DREMIO_PAT=$(cat ~/.secrets/dremio_pat)
```

See `docs/authentication.md` for full setup guide.

## Dremio REST API (v3)
- Base URL: https://lakehouse.jgi.lbl.gov/api/v3 (all API paths are relative to /api/v3).
- Auth: Use Authorization: Bearer <dremioAccessToken>. Tokens can be OAuth or PAT; username/password tokens require the v2 login API and are internal-only.
- Submit SQL: POST /api/v3/sql with {"sql": "...", "context": ["Space","Folder"], "references": {...}}. Response includes a job id.
- Job results: GET /api/v3/job/{id}/results?limit=...&offset=... (default limit 100, max 500). Use rowCount from the response to page through all rows.
- Other endpoints: Some list APIs use pageToken rather than limit/offset; preserve all other query params when using pageToken.

## Paging and bulk download
- To download large result sets, loop GET job results with limit=500 and offset+=500 until offset >= rowCount.
- If the result set is very large, prefer filtering and projecting in SQL to reduce transfer size before paging.

## Time travel patterns
- AT TIMESTAMP 'YYYY-MM-DD HH:MM:SS'
- AT SNAPSHOT '123456'

## Usage Examples

### Python API (use scripts/rest_client.py)
```python
from rest_client import query
results = query("SELECT gold_id, study_name FROM \"gold-db-2 postgresql\".gold.study LIMIT 10")
for row in results:
    print(row)
```

### Available Scripts
- `scripts/rest_client.py` - REST API client with `query()` and `show_schemas()` functions
- `scripts/get_dremio_token.sh` - Token generation

## Documentation
- `docs/sql-quick-reference.md` - Dremio SQL syntax, differences from PostgreSQL, time travel
- `docs/data-catalog.md` - Complete catalog of all tables and schemas
- `docs/authentication.md` - Token generation details

## References
- Claude skill best practices: see `references/skill-best-practices.md`
- Lakehouse notes derived from internal JGI slides and tooling notes
- Dremio API docs: https://docs.dremio.com/current/reference/api/
