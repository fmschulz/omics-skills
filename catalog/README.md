# Skill Catalog

This directory holds generated catalog files used to select and order installed skills.

Generated files:

- `catalog.json`
- `relationships.json`
- `routing.json`

Rebuild from the repository root:

```bash
python3 scripts/skill_index.py build --repo . --out catalog
```
