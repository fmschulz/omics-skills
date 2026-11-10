# Skill Catalog

This directory holds generated catalog files used to select and order installed skills.

Generated file:

- `catalog.json` — the single source of truth consumed by the router
  (`skill_index.py route`) and the routing hook. It records skills (with a
  `hidden` flag for pipeline stages), agents, and the skill/agent relationship
  edges. Metadata is deterministic (no build timestamp or absolute path) so the
  committed copy is byte-stable across machines.

Hand-kept file:

- `citation-cache.json` — registered Crossref records that
  `scripts/validate-citations.py` checks the skills' citations against.

Rebuild from the repository root:

```bash
python3 scripts/skill_index.py build --repo . --out catalog
```
