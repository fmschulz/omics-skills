# JGI Lakehouse Skill

Query and explore the JGI Lakehouse (Dremio + Apache Iceberg) using safe SQL patterns.

## Quick Start

### 1. Setup Authentication

```bash
# Generate token from LBNL server (one-time)
ssh <lbnl-server>
cd ~/.agents/skills/jgi-lakehouse/scripts
./get_dremio_token.sh username password

# Store token (on your workstation)
echo "your-token" > ~/.secrets/dremio_pat
chmod 600 ~/.secrets/dremio_pat

# Auto-load token
echo 'export DREMIO_PAT=$(cat ~/.secrets/dremio_pat 2>/dev/null)' >> ~/.bashrc
source ~/.bashrc
```

See `docs/authentication.md` for details.

### 2. Explore Databases

```bash
# List all schemas
python3 examples/explore_database.py

# Explore GOLD database
python3 examples/explore_database.py GOLD

# Or use bash script (from LBNL network)
bash scripts/explore_gold_database.sh > catalog.txt
```

### 3. Query Data

```python
import sys
sys.path.append('~/.agents/skills/jgi-lakehouse/scripts')

from rest_client import query

# Simple query
results = query("SELECT * FROM GOLD.PROJECT LIMIT 10")

# With context
results = query(
    "SELECT * FROM genomics LIMIT 10",
    context=["Phytozome"]
)
```

## File Structure

```
.
├── SKILL.md                        # Skill definition
├── README.md                       # This file
│
├── scripts/
│   ├── get_dremio_token.sh        # Token generation
│   ├── rest_client.py             # REST API client
│   ├── explore_gold_database.sh   # GOLD exploration (bash)
│   └── README.md                  # Scripts documentation
│
├── examples/
│   └── explore_database.py        # Interactive database explorer
│
├── docs/
│   ├── authentication.md          # Token setup
│   ├── data-catalog.md            # Table catalog
│   ├── sql-quick-reference.md     # SQL syntax cheatsheet
│   └── explore_gold.md            # GOLD exploration guide
│
└── references/
    ├── tools.json                 # Tool definitions
    └── ...                        # Additional references
```

## Network Requirements

**Public HTTPS Endpoint** (`https://lakehouse.jgi.lbl.gov`)
- ❌ Blocked by Cloudflare Access (requires browser auth)

**Internal HTTP Endpoint** (`http://lakehouse-1.jgi.lbl.gov:9047`)
- ✅ Direct API access with token
- ⚠️ Only accessible from LBNL network

## Available Databases

- **GOLD** - Genomes OnLine Database
- **Phytozome** - Plant genomics
- **Mycocosm** - Fungal genomics
- **IMG** - Integrated Microbial Genomes
- **JDP** - JGI Data Portal

## Operational Rules

1. Prefer VDS (views) over physical tables
2. Never run SELECT * without LIMIT (default: 100)
3. Always inspect schema before complex joins
4. Check reflections if performance issues arise
5. Use Iceberg time travel for historical queries

## Documentation

- **Setup**: `docs/setup_guide.md`
- **Authentication**: `docs/authentication.md`
- **GOLD Database**: `docs/explore_gold.md`
- **API Reference**: https://docs.dremio.com/current/reference/api/

## Examples

### List Schemas
```python
from rest_client import show_schemas
schemas = show_schemas()
```

### Query with Time Travel
```sql
SELECT * FROM GOLD.PROJECT
AT TIMESTAMP '2026-01-20 12:00:00'
LIMIT 10
```

### Describe Table
```python
from rest_client import query
schema = query("DESCRIBE GOLD.PROJECT")
```

## Token Management

- **Lifetime**: 30 hours
- **Storage**: `~/.secrets/dremio_pat` (gitignored)
- **Refresh**: Re-run `get_dremio_token.sh` from LBNL server

## Troubleshooting

**"No route to host"**
→ Port 9047 blocked. Use SSH tunnel or run from LBNL network.

**"HTTP 302 redirect"**
→ Cloudflare Access blocking. Use internal endpoint.

**"Token expired"**
→ Regenerate token (30 hour lifetime).

## Support

- **Skill docs**: `SKILL.md`
- **Dremio API**: https://docs.dremio.com/
- **Admin contact**: Georg Rath (JGI Slack)
