# Skill Catalog

This directory holds generated catalog files used to select and order installed skills.

Generated file:

- `catalog.json` — the single source of truth consumed by the router
  (`skill_index.py route`) and the routing hook. It records skills, agents, and
  the skill/agent relationship edges. Metadata is deterministic (no build
  timestamp or absolute path) so the committed copy is byte-stable across
  machines.

Rebuild from the repository root:

```bash
python3 scripts/skill_index.py build --repo . --out catalog
```
