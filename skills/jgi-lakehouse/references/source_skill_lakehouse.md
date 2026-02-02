Based on the JGI Lakehouse architecture slides and the best practices for AI Agent Skills, I have created a comprehensive **Lakehouse Skill**.

This response is divided into two parts:

1. **Resource Summaries**: A digest of the external links and videos mentioned in the slides (as requested).
2. **The Agent Skill Package**: The modular files (System Prompt, Tool Definitions, and Python Code) needed to give your AI agent "expert" capabilities in this environment.

---

### Part 1: Summary of External Resources

*These summaries provide the foundational knowledge your agent (or team) needs, derived from the "Resources" slide.*

#### 1. Apache Iceberg (The "Best Video" Concepts)

*Reference to the core architecture video.*

* **The "Database" for Files**: Iceberg creates a transactional layer over the raw Parquet files in S3. It allows the Data Lake to support features previously only found in databases.
* **Snapshots & Time Travel**: Every time data changes, Iceberg creates a new "Snapshot" rather than overwriting files. This allows **Time Travel**—you can query `AT TIMESTAMP` to reproduce scientific results exactly as they looked in the past.
* **Hidden Partitioning**: Unlike older Hive systems where you had to query specific folders (e.g., `/data/2026/01/`), Iceberg handles this automatically. You just query `WHERE date = '2026-01-01'`, and it finds the correct files.

#### 2. Dremio University (Lakehouse Fundamentals)

* **Separation of Compute & Storage**: Dremio (Compute) and S3 (Storage) scale independently. You do not "import" data into Dremio; you query it in place.
* **Reflections (The "Secret Sauce")**:
* **Raw Reflections**: Think of these as "super indexes" for row-level lookups (e.g., finding one specific gene variant).
* **Aggregate Reflections**: Pre-computed summaries that speed up BI dashboards (e.g., "Count of organisms by family").


* **Virtual Datasets (VDS)**: The recommendation is to **never query physical tables directly**. Always create a Virtual View (VDS) to serve as a semantic layer.

#### 3. Python Ecosystem (Client Libraries)

* **PyArrow (Recommended)**: The gold standard for Dremio. It uses **Arrow Flight**, a protocol that streams data in parallel from the server's memory to the client's memory. It is significantly faster than JDBC/ODBC.
* **Polars**: A high-performance DataFrame library that is often faster than Pandas for processing the large datasets returned by Dremio.
* **DuckDB**: Allows you to download a Parquet file locally and run SQL on it on your laptop (good for offline analysis).

---

### Part 2: The JGI Lakehouse Agent Skill

To implement this skill, you should add the following three components to your agent's configuration.

#### 1. System Prompt (The "Brain")

*Add this to your agent's system instructions so it understands the JGI environment and rules.*

```markdown
# Role
You are the JGI Data Platform Engineering Agent. You have programmatic access to the JGI Lakehouse (Dremio) to assist researchers with genomic data.

# Infrastructure Context
- **Instance URL**: `https://lakehouse.jgi.lbl.gov`
- **Engine**: Dremio (SQL-based).
- **Storage**: S3 Buckets containing Parquet files managed by **Apache Iceberg**.
- **Key Spaces**: `Phytozome` (Plants), `Mycocosm` (Fungi), `JDP` (Portal), `IMG`, `GOLD`.

# Operational Rules (Critical)
1.  **Prefer Views (VDS)**: Always query Virtual Datasets (Views), not physical tables.
2.  **Safety First**: 
    - NEVER run `SELECT *` without a `LIMIT` clause (default to 100 rows).
    - Preview schema using `describe_table` before writing complex joins.
3.  **Performance Tuning**:
    - If a user reports slowness, check if **Reflections** are enabled.
    - Suggest **Raw Reflections** for heavy filters and **Aggregate Reflections** for dashboards.
4.  **Reproducibility (Time Travel)**:
    - If asked for historical data, use Iceberg syntax:
    - `SELECT * FROM namespace.table AT TIMESTAMP '2026-01-20 12:00:00'`
    - `SELECT * FROM namespace.table AT SNAPSHOT '59384'`

# Python Coding Guidelines
When asked to write scripts, **always** use the `pyarrow` library with the **Arrow Flight** protocol. Do not use JDBC/ODBC unless explicitly requested, as Flight is optimized for large scientific datasets.

```

#### 2. Tool Definitions (The "Interface")

*Use this JSON Schema to register the tools with your agent (e.g., in Claude or LangChain).*

```json
[
  {
    "name": "list_catalogs",
    "description": "Lists the available Spaces (e.g., Phytozome, JDP) to discover where data is located.",
    "input_schema": {
      "type": "object",
      "properties": {}
    }
  },
  {
    "name": "describe_table",
    "description": "Retrieves the schema (columns, data types) for a specific table or view.",
    "input_schema": {
      "type": "object",
      "properties": {
        "table_path": {
          "type": "string",
          "description": "The full path to the table (e.g., 'Phytozome.genomics.variants')."
        }
      },
      "required": ["table_path"]
    }
  },
  {
    "name": "execute_lakehouse_query",
    "description": "Executes a SQL query against the JGI Dremio instance using Arrow Flight. Returns the results as JSON.",
    "input_schema": {
      "type": "object",
      "properties": {
        "sql_query": {
          "type": "string",
          "description": "The ANSI SQL query. Must include LIMIT for non-aggregate queries."
        }
      },
      "required": ["sql_query"]
    }
  }
]

```

#### 3. Python Implementation (The "Backend")

*This is the code your agent execution environment needs to run to power the tools above. It implements the "Best Practices" from the slides (using Arrow Flight).*

```python
import os
import pyarrow.flight as flight
import pandas as pd

# Configuration (from Environment Variables)
DREMIO_HOST = os.getenv("DREMIO_HOST", "lakehouse.jgi.lbl.gov")
DREMIO_PORT = os.getenv("DREMIO_PORT", "443") # Default to TLS port
DREMIO_TOKEN = os.getenv("DREMIO_PAT") # Personal Access Token

def get_flight_client():
    """Establishes a secure Flight connection to JGI Dremio."""
    if not DREMIO_TOKEN:
        raise ValueError("Missing DREMIO_PAT environment variable.")
        
    # 'grpc+tls' is required for secure endpoints
    location = f"grpc+tls://{DREMIO_HOST}:{DREMIO_PORT}"
    client = flight.FlightClient(location)
    
    # Authenticate
    headers = [(b"authorization", f"Bearer {DREMIO_TOKEN}".encode("utf-8"))]
    options = flight.FlightCallOptions(headers=headers)
    return client, options

def execute_lakehouse_query(sql_query):
    """Executes SQL via Arrow Flight and returns a list of dictionaries."""
    # Safety Check: Enforce LIMIT
    if "limit" not in sql_query.lower() and "count" not in sql_query.lower():
        sql_query += " LIMIT 100"

    try:
        client, options = get_flight_client()
        
        # 1. Plan the query
        flight_info = client.get_flight_info(
            flight.FlightDescriptor.for_command(sql_query), 
            options
        )
        
        # 2. Execute and Read Stream
        reader = client.do_get(flight_info.endpoints[0].ticket, options)
        df = reader.read_all().to_pandas()
        
        # 3. Format for Agent (JSON)
        return df.to_dict(orient='records')
        
    except Exception as e:
        return {"error": f"Query failed: {str(e)}"}

def describe_table(table_path):
    """Helper to inspect schema without running a full query."""
    return execute_lakehouse_query(f"DESCRIBE {table_path}")

def list_catalogs():
    """Helper to list root spaces."""
    return execute_lakehouse_query("SHOW SCHEMAS")

```
