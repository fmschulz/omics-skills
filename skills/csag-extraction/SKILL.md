---
name: csag-extraction
description: >-
  Extract a CSAG (Conditional Scientific Argumentation Graph) from a manuscript using the canonical
  argumentation spine (Assertions, EvidenceItems, EvidenceLinks, InferenceSteps) while enforcing
  CSAG conditionality (no assertion without at least one Context). Also generates paper-grounded
  Q&A items using bundled QA templates.
license: CC0-1.0
metadata:
  version: "0.6.0"
---

# CSAG extraction skill

## Goal

Convert a manuscript into a **CSAG `PaperExtraction`** instance that is:

- **Schema-valid** (LinkML: `assets/csag.yaml`)
- **Evidence-grounded** (TextSpans for key objects)
- **Canonical** (support/refute only via `EvidenceLink`, chains via `InferenceStep`)
- **Conditional** (every Assertion has ≥1 Context)

## Files in this skill

- `assets/csag.yaml` — authoritative schema
- `assets/csag_qa_templates.yaml` — QA template catalog
- `references/CSAG_PLAYBOOK.md` — detailed extraction guide + edge cases

## Quick Reference

| Task | Action |
|------|--------|
| Extract paper | Build one `PaperExtraction` per manuscript, not per search hit. |
| Ground claims | Attach important assertions, evidence, and links to TextSpans. |
| Validate schema | Run `scripts/validate_paper_extraction.py` before finalizing. |
| Review quality | Run `scripts/csag_quality_report.py --strict` and resolve issues. |

## Non‑negotiable invariants

1) **Every Assertion MUST have ≥1 Context** (schema-enforced).
2) **Support/refute polarity ONLY in `EvidenceLink`**.
3) **Contradictions/qualification ONLY in `AssertionRelation`**.
4) **Reasoning chains ONLY as `InferenceStep`**.
5) Ground important objects to TextSpans.
6) Every Assertion MUST have `normalization_status`:
   - `raw` / `partially_normalized` / `fully_normalized`

## Extraction scope

The extraction scope is the **full manuscript**: title, abstract, introduction, methods, results, discussion, conclusion, and supplementary material when available. If retrieval was driven by topic terms (organisms, genes, methods), do not restrict extracted assertions or evidence to sentences that mention those terms — the retrieval scope is not the extraction scope.

## Instructions

## Reliability pattern for model-assisted extraction

When a model is used to assist extraction, prefer a two-step workflow:

1. Draft the scientific content first: claims, evidence snippets, evidence
   polarity, inferences, critiques, gaps, artifacts, datasets, and exact source
   quotes.
2. Let tooling assemble the final `PaperExtraction`: deterministic IDs,
   reference fields, enum normalization, offset lookup from `exact_text`, and
   validator repair for mechanical schema-shape issues.

Do not rely on a model to perform all final bookkeeping in one pass. The most
common failures are missing IDs, dangling references, scalar values where lists
are required, field aliases such as `evidence_id` instead of `evidence_item`,
wrong enum labels, and missing artifact/dataset metadata.

Use the validator as a feedback loop:

```bash
uv run python skills/csag-extraction/scripts/validate_paper_extraction.py \
  work/STEM/paper_extraction.json \
  --source-markdown work/STEM/STEM.md \
  --article-json work/STEM/STEM.article.json \
  --report-out work/STEM/paper_extraction.validation.json
```

For mechanical cleanup before curation, write a repaired candidate and inspect
the `repair_actions` in the validation report:

```bash
uv run python skills/csag-extraction/scripts/validate_paper_extraction.py \
  work/STEM/paper_extraction.raw.json \
  --source-markdown work/STEM/STEM.md \
  --article-json work/STEM/STEM.article.json \
  --repair-out work/STEM/paper_extraction.repaired.json \
  --report-out work/STEM/paper_extraction.validation.json
```

Repairs are intentionally narrow. They can normalize deterministic schema shape,
but they do not certify scientific correctness.

### Phase 1 — Core graph (always)
1. Build `PaperExtraction` metadata (id/title/doi/pmid if available).
   - Resolve `doi` and `pmid` from the staged source, OCR/article outputs, TEI/XML, or local metadata whenever recoverable.
   - If one or both cannot be resolved, record explicit `doi_status` / `pmid_status` entries in `extraction_activities.parameters` with `resolved` or `unresolved`.
2. Extract **Artifacts** when the paper exposes figure/table/supplement captions.
3. Extract **Datasets** when the paper exposes data-availability text, repository links, accessions, or project identifiers.
4. Extract **Entities** with ontology annotations when possible.
5. Extract **Assertions** (hypotheses, result-claims, conclusions):
   - must include `contexts` (≥1)
   - must include `normalization_status`
   - include `criticality` (`core`, `major`, `supporting`, `background`) when the importance of the claim can be judged
   - include `falsification_criteria` for any core or major assertion (what observation would weaken or refute the claim)
6. Extract **EvidenceItems** (results/analyses/citations).
7. Create **EvidenceLinks** (EvidenceItem -> Assertion) with `polarity`, `strength`, `rationale`.
8. Add **TextSpans** grounding key Assertions/EvidenceItems/EvidenceLinks.

### Phase 2 — Study & experiment structure (if feasible)
- Add `Study` and `Experiment` objects.
- Enrich Contexts (organism/cell_type/tissue/disease) using Entity references.

### Phase 3 — Conditions + reasoning + critique/gaps + QA (when available)
- Add `Condition` objects (dose/time/genotype/treatment regime).
- Add `InferenceStep`s for explicit/implicit reasoning chains.
- Add `StudyCritique` and `KnowledgeGap` objects.
- Generate QA items from templates.

## Input Requirements

- A full manuscript, preprint, article markdown, XML/JSON extraction, or equivalent source text.
- Any available identifiers: DOI, PMID, PMCID, title, journal, authors, year, and source URL.
- Source text or article JSON when offset-aware TextSpan validation is required.
- A target path for `paper_extraction.json` and validation reports.

## Output

- `paper_extraction.json` conforming to `assets/csag.yaml`.
- Validation report from `scripts/validate_paper_extraction.py`.
- Quality report from `scripts/csag_quality_report.py`.
- Optional QA items generated from `assets/csag_qa_templates.yaml`.

## Minimum coverage expectations (full research articles)

Unless the source is a short note/editorial with genuinely limited content, target:
- >=1 assertion for hypothesis/research-question/objective when present
- >=2 result/conclusion assertions from different parts of the paper when present
- >=2 evidence items and >=2 evidence links when present
- >=1 inference step when reasoning combines multiple premises/evidence
- >=1 critique/gap when explicitly discussed by authors
- >=1 artifact when figure/table captions are present in the source
- >=1 dataset when data-availability text, accessions, or repository links are present in the source

If a category is not present in the paper, state that in `notes` for the paper/assertion rather than silently omitting it.

## Quality Gates

Confirm all checks:
- Assertions are not just keyword-hit snippets; they reflect core study claims.
- Evidence links cover key claims, not only the first matched sentence.
- At least one TextSpan anchors each non-trivial extracted object.
- Output includes explicit statement of absent components (e.g., no clear hypothesis section).
- `doi` / `pmid` are resolved when recoverable, or explicit `doi_status` / `pmid_status` parameters are present in `extraction_activities`.
- `artifacts` are present when figure/table captions are present in the source.
- `datasets` are present when data-availability text, accessions, or repository links are present in the source.
- The repo-local validation pass succeeds (`scripts/validate_paper_extraction.py`).
- The quality report is reviewed (`scripts/csag_quality_report.py`). Treat it as the default CSAG knowledge-artifact evaluation after `paper_extraction.json` is generated: inspect `completeness`, `missing_or_weak`, and `field_quality` as well as `issues`.
- Any non-empty `issues` list is resolved before stopping; warnings in `missing_or_weak` are fixed or justified in `notes`.

For higher-stakes use, run validation with `--profile promoted_claim` or `--profile benchmark_key`. These profiles additionally require:

- every non-background assertion has decisive evidence and assertion/evidence text-span grounding
- core and major benchmark assertions have at least moderate decisive evidence unless explicitly marked as `limitation` or `speculation`

## Anti-patterns (forbidden)

- Emitting a paper with only one assertion/evidence pair when richer claims are present.
- Restricting extraction to sentences that mention the topic terms used during retrieval.
- Skipping mechanistic or statistical claims because they sit outside the topic terms.

## Identifier and provenance requirements

1. Use `pmid:<id>` for `PaperExtraction.id` when PMID is known; fall back to `doi:<doi>` or `csag:doc/<slug>` otherwise.
2. Anchor `TextSpan.document_id` to the same identifier used for `PaperExtraction.id`.
3. If only PMCID is available, use `pmc:<id>` and mark PMID resolution as pending in `notes`.
4. Produce one `PaperExtraction` per source manuscript; do not mix spans across manuscripts.
5. Record `extraction_activities` with `tool_name`, `tool_version`, `model_name` (when applicable), and explicit `doi_status` / `pmid_status` parameters when those identifiers cannot be resolved from the source.

## Validation hook (blocking)

Before finalizing the extraction, run:

```bash
uv run python skills/csag-extraction/scripts/validate_paper_extraction.py \
  ABS_PATH/paper_extraction.json \
  --source-markdown ABS_PATH/STEM.md \
  --article-json ABS_PATH/STEM.article.json \
  --report-out ABS_PATH/paper_extraction.validation.json
```

Use `--profile promoted_claim` for curated claims and `--profile benchmark_key` for scoring keys. Do not stop until the validator returns `OK`.

Then run the quality report and review how complete the artifact is, what is missing or weak, and the field-level information quality:

```bash
uv run python skills/csag-extraction/scripts/csag_quality_report.py \
  ABS_PATH/paper_extraction.json \
  --source-markdown ABS_PATH/STEM.md \
  --article-json ABS_PATH/STEM.article.json \
  --report-out ABS_PATH/paper_extraction.quality.json \
  --strict
```

## Manuscript interrogation questions

Before finalizing a `PaperExtraction`, answer these (internally or as `qa_items`):

- What are the manuscript's hypotheses, research questions, or objectives?
- What are the primary result claims and conclusions or discoveries?
- What evidence supports each key claim, and what evidence (if any) refutes it?
- Which assertions are core, major, supporting, or background?
- What observation or analysis would falsify or seriously weaken each core or major assertion?
- What inference or mechanistic chains connect evidence to conclusions?
- What limitations or flaws are stated or strongly implied?
- What open knowledge gaps or future-work items are stated?

Map answers to CSAG objects:

- hypotheses / results / conclusions → `assertions`
- claim importance → assertion `criticality`
- falsifiability checks → assertion `falsification_criteria`
- support / refute → `evidence_links`
- reasoning chains → `inferences`
- limitations → `critiques`
- open questions → `knowledge_gaps`
- question-driven outputs → `qa_items` (from `assets/csag_qa_templates.yaml`)

## Normalization rubric

- `raw`: free-text only; triple fields may be empty.
- `partially_normalized`: some of {subject,predicate,object} filled OR ambiguous mappings.
- `fully_normalized`: subject+predicate+object present; refer to Entity IDs; predicate is CURIE/URI (RO/SIO preferred).

## QA templates

Use `assets/csag_qa_templates.yaml` to instantiate `QAItem` + `Answer` objects.
Answers must cite `supporting_assertions` and/or `supporting_evidence_links`.

For edge cases and scoring guidance, see `references/CSAG_PLAYBOOK.md`.

## Examples

```bash
uv run python skills/csag-extraction/scripts/validate_paper_extraction.py \
  work/paper/paper_extraction.json \
  --source-markdown work/paper/paper.md \
  --article-json work/paper/paper.article.json \
  --report-out work/paper/paper_extraction.validation.json
```

## Troubleshooting

- **Validator reports missing contexts**: Add at least one `Context` to every `Assertion`; this is not optional.
- **Dangling references**: Rebuild IDs deterministically and verify every referenced assertion, evidence item, entity, artifact, and dataset exists.
- **Weak extraction**: Re-read the full manuscript and add missing hypotheses, result claims, evidence links, critiques, gaps, artifacts, and datasets when present.
- **Offset mismatch**: Use exact source text for TextSpans and rerun validation against the same markdown/article JSON used for extraction.
