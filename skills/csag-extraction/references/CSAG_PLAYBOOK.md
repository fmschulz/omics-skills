# CSAG Playbook — Detailed extraction guide (references/CSAG_PLAYBOOK.md)

You are performing **information extraction and normalization**. Your job is to convert a scientific publication into a **CSAG (Conditional Scientific Argumentation Graph)** instance that is:

- **Schema-valid** (LinkML CSAG hybrid schema)
- **Evidence-grounded** (TextSpan provenance for everything that matters)
- **Canonical** (support/refute only in EvidenceLink; contradictions only in AssertionRelation)
- **Conditional** (no assertion without at least one Context; add Conditions when available)
- **Scalable** (small, atomic objects; minimal redundancy; stable IDs)

Your output will be used for downstream scientific search, review, and reuse. **Do not summarize** the paper. **Extract structured reasoning.**

---

## Core output contract

### Output format
Return **only** a single **YAML** document representing a `PaperExtraction` instance that conforms to the CSAG schema.

- No extra commentary, no markdown fences, no explanations.
- Every `id` must be a valid CURIE/URI (`uriorcurie`).
- Use stable IDs so the same paper re-extraction yields mostly the same IDs.

### Model-assisted extraction pattern
For model-assisted workflows, separate scientific reading from schema
bookkeeping:

1. Extract the argument content first: assertions, evidence snippets, evidence
   polarity, inferences, critiques, knowledge gaps, artifacts, datasets, and
   exact source quotes.
2. Assemble the final `PaperExtraction` with deterministic tooling whenever
   possible: assign IDs, populate reference fields, normalize enum labels,
   compute offsets from exact quotes, and run the validator.

This avoids the most common mechanical failures: missing or duplicated IDs,
dangling references, scalar values in list fields, non-CSAG enum labels,
field aliases such as `evidence_id` instead of `evidence_item`, and missing
artifact or dataset metadata.

The validator report includes machine-readable `structured_errors`,
`error_summary`, and optional `repair_actions`. Mechanical repairs can make a
candidate easier to curate, but they do not replace scientific review.

### Canonical truth rules (do not violate)
1. **Support/refute is encoded ONLY in `EvidenceLink`**
   - Never add “supports/refutes” semantics anywhere else.
2. **Contradiction/qualification/replication is encoded ONLY in `AssertionRelation`**
3. **Reasoning chains are encoded ONLY in `InferenceStep`**
4. **Every `Assertion` MUST have at least one `Context`**
   - This is enforced by schema (`contexts` minimum_cardinality = 1).
5. **Do not fabricate**
   - If the paper does not say it, do not invent it.
   - If you infer (e.g., a flaw), mark `origin: extractor_inferred` and reduce confidence.

---

## Extraction phases (must follow)

### Phase 1 (required for every paper)
Goal: Build the minimum useful CSAG graph.

You MUST extract:
- `entities`
- `contexts` (at least one minimal Context per paper; referenced by every Assertion)
- `assertions` (hypotheses/claims/results/conclusions as atomic nodes)
- `evidence_items` + `results` (when extractable)
- `evidence_links` (support/refute polarity edges)
- `text_spans` for assertions and evidence items (strongly preferred; required if feasible)

**Deliverable:** A valid `PaperExtraction` with a working argument spine:
`Assertion` ⇄ `EvidenceLink` ⇄ `EvidenceItem`

### Phase 2 (do if the paper provides enough structure)
Goal: Add study/experiment scaffolding and enrich context.

Add:
- `studies`, `experiments`, `variables`
- Context enrichment: `organism`, `cell_type`, `tissue`, `disease_state`, etc. (as Entity references)
- Link assertions/evidence to `asserted_in_study` / `associated_experiment`

### Phase 3 (do when explicitly present or strongly supported)
Goal: Add conditions + inference chains + critique/gaps + QA.

Add:
- `conditions` (dose, time, genotype, treatment regime, etc.)
- `inferences` (InferenceSteps connecting evidence/premises to derived assertions)
- `critiques`, `knowledge_gaps`
- `qa_items` using the templates below

---

## ID policy (stable, scalable)

### Document id
Prefer:
- DOI: `doi:<doi_string>` (e.g., `doi:10.1038/s41586-020-2216-3`)
- Else PMID: `pmid:<pmid_string>`
- Else: `csag:doc/<slug>` where `<slug>` is deterministic from title (lowercase, alnum, dash)

### Within-document IDs
Use deterministic, local IDs under the document id namespace:

- Assertions: `csag:assertion/<docid>/A0001`
- EvidenceItems: `csag:evidence/<docid>/E0001`
- EvidenceLinks: `csag:elink/<docid>/L0001`
- Contexts: `csag:context/<docid>/C0001`
- Conditions: `csag:condition/<docid>/K0001`
- Studies: `csag:study/<docid>/S0001`
- Experiments: `csag:experiment/<docid>/X0001`
- Critiques: `csag:critique/<docid>/R0001`
- Gaps: `csag:gap/<docid>/G0001`
- QA items: `csag:qa/<docid>/Q0001`
- Answers: `csag:answer/<docid>/ANS0001`
- TextSpans: `csag:span/<docid>/T0001`

IDs must be unique within a paper.

---

## TextSpan grounding requirements

### Strong rule
For every:
- Assertion
- EvidenceItem
- EvidenceLink rationale (optional but recommended)
- Critique
- KnowledgeGap

…provide at least one `TextSpan` **when the text exists in the input**.

### TextSpan fields
Each `TextSpan` MUST include:
- `document_id` (the paper id)
- `section_type` (best guess)
- `start_char`, `end_char` (0-based; end exclusive)
- Prefer also `exact_text`

### If you don’t have offsets
Compute them:
- If you have the full section text, search for `exact_text` and record the matching span.
- If there are multiple matches, choose the one that best matches nearby phrasing.
- If no match exists (e.g., paraphrase), extract a shorter verbatim substring and anchor that.

Never put fake offsets.

---

## Entity extraction and ontology normalization

### Entity policy
Create an `Entity` node for each biologically meaningful concept needed by Assertions/Context/Conditions:
- genes, proteins, variants, chemicals/drugs, diseases, phenotypes, cell types, tissues/anatomy, organisms, assays/methods

### Ontology annotations
If you can map confidently, add `ontology_annotations` with:
- `term_id` as CURIE (e.g., `NCBITaxon:10090`, `CL:0000540`, `MONDO:0004979`, `CHEBI:15365`)
- `match_type` (“exact”, “broad”, etc.)
- `confidence_score`

If uncertain, keep Entity without term_id (still useful), but lower confidence.

---

## CSAG conditionality rule: contexts and conditions

### Contexts (required)
Every `Assertion` must include `contexts: [ ... ]` with at least one `Context`.

#### Minimal Phase-1 Context (always create)
Create one baseline context per paper, even if coarse:

- `Context.id`: `csag:context/<docid>/C0001`
- `context_facet`: `unspecified`
- `label`: “in this study”
- `origin`: `extractor_inferred`
- `confidence_score`: 0.5–0.7

Then, attach this context to every Assertion as a default unless a more specific context is extracted.

#### Phase-2 Context enrichment
When present, create additional Contexts (or enrich existing) with:
- `organism` (Entity ref; NCBITaxon preferred)
- `cell_type` (Entity ref; CL preferred)
- `tissue` (Entity ref; UBERON preferred)
- `disease_state` (Entity ref; MONDO preferred)
- and optional `additional_context_qualifiers`

### Conditions (phase 3)
Conditions represent parameterized prerequisites (dose/time/genotype/stress, etc.)

Create `Condition` objects when:
- the paper explicitly defines a parameter (dose, timepoint, KO/knockdown, temperature, etc.)
- and that parameter scopes a result/claim

Attach conditions to:
- Assertions (`conditions`)
- EvidenceItems (`conditions`)
- optionally Context via qualifiers if it is truly contextual rather than conditional

---

## Assertions: extraction + normalization status

### What is an Assertion?
An `Assertion` is an atomic scientific statement:
- hypothesis
- result-claim
- conclusion/discovery
- limitation/future work (optional; often captured as Critique/Gap instead)

Extract multiple smaller assertions rather than one long one.

### Assertion normalization_status (required for every Assertion)
Set `normalization_status` to one of:
- `raw` — only `assertion_text` + role/type + contexts (+ spans). No triple.
- `partially_normalized` — has some structured fields (e.g., subject + object Entities) but predicate is missing/ambiguous or mapped only to a local csag predicate.
- `fully_normalized` — subject/predicate/object are present AND:
  - subject/object reference Entities (not raw strings)
  - predicate is a proper ontology predicate when possible (RO/SIO preferred; csag local allowed if no better)
  - qualifiers/contexts/conditions are properly attached

### When to create a normalized triple
If the statement is about a relationship, fill:
- `subject` (Entity id)
- `predicate` (RO/SIO/CSAG predicate CURIE)
- `object` (Entity id)

Do not force triples for narrative assertions (“this suggests…”) unless you can represent them cleanly.

---

## Evidence model (canonical)

### EvidenceItem
Create EvidenceItems as *units of evidence*, usually:
- one experiment result summary (often one figure/table panel)
- one statistical test summary
- one literature citation used as evidence (optional)

EvidenceItems can include structured `results` when possible.

### EvidenceLink (the only support/refute edge)
For each Assertion, link one or more EvidenceItems via EvidenceLinks:
- `polarity`: supports/refutes/mixed/inconclusive
- `strength`: very_strong/strong/moderate/weak/very_weak/unknown
- `rationale`: short explanation tying evidence to claim

#### Strength heuristics (use best judgement)
- very_strong: strong design + clear effect + strong stats + appropriate controls/replication
- strong: solid stats and design but limited replication/sample size
- moderate: some evidence but caveats (small n, indirect measurement)
- weak: suggestive only, unclear stats, qualitative
- very_weak: speculative/poorly supported
- unknown: cannot judge

Always reflect uncertainty in `confidence_score`.

---

## InferenceSteps (phase 3)

Create `InferenceStep` objects when the paper explicitly performs a reasoning jump:
- evidence supports intermediate claim → mechanistic conclusion
- multiple premises → derived conclusion
- observational association + assumption → causal inference

InferenceStep fields:
- `input_evidence_links` (preferred) and/or `input_assertions`
- `output_assertion`
- `inference_method`
- optional `assumptions`
- optional `inference_rationale` (short)

Do not create long chains unless the paper supports them.

---

## AssertionRelation (canonical contradictions, qualifications, replication)

Create `AssertionRelation` edges when:
- authors state conflict with prior literature
- authors qualify/limit a claim
- the paper replicates or fails to replicate a prior claim
- two claims in the same paper contradict/qualify each other

Use `relation_type`:
- contradicts, qualifies, supports, refutes, replicates, etc.

Anchor to text spans if present.

---

## Critiques and Knowledge Gaps (phase 3)

### StudyCritique
Extract explicit limitations and bias risks:
- author-stated limitations → `origin: author_stated`
- inferred limitations (e.g., multiple testing not corrected) → `origin: extractor_inferred` with lower confidence

Link them to:
- `impacted_assertions`
- `impacted_evidence_items`

### KnowledgeGap
Extract open questions and missing evidence:
- author-stated “future work” → origin author_stated
- inferred “replication needed” → origin extractor_inferred

Link them to:
- `related_assertions`
- `suggested_actions` when the paper suggests experiments

---

# CSAG Extraction Procedure: CSAG_EXTRACT_PAPER

This is the procedure you must execute.

## Inputs
- Paper metadata (doi/pmid/title/journal/date) if available
- Paper text segmented by section if available (preferred)
- If figures/tables are available as text, include them

## Output
A single `PaperExtraction` YAML conforming to CSAG.

## Steps (deterministic)
1. **Initialize paper**
   - Set `PaperExtraction.id` (doi/pmid/csag:doc/slug)
   - Fill metadata fields if present
2. **Create baseline Context (C0001)**
   - label “in this study”, facet unspecified
3. **Extract Entities**
   - Create Entities for all biological items needed for claims/evidence/context
   - Add ontology_annotations when confident
4. **Extract Assertions**
   - Identify hypotheses, main findings, conclusions, key negative results
   - Split into atomic assertions
   - Attach ≥1 Context (at least baseline)
   - Set `claim_role`, `assertion_type`
   - Set `normalization_status`
   - Add text spans
5. **Extract EvidenceItems**
   - Extract result statements (figures/tables/results text)
   - Create EvidenceItems (atomic)
   - Add Result objects when numeric/stats appear
   - Attach contexts/conditions if available
   - Add text spans
6. **Create EvidenceLinks**
   - For each assertion, link EvidenceItems that bear on it
   - Set polarity/strength/rationale
7. **Phase-2 enrichment (if possible)**
   - Create Study/Experiment nodes
   - Enrich contexts with organism/cell type/tissue/disease
8. **Phase-3 enrichment (if possible)**
   - Extract Conditions (dose/time/genotype/perturbation)
   - Add InferenceSteps for explicit reasoning chains
   - Add Critiques + Gaps
   - Generate QA items using templates below
9. **Self-check**
   - Every Assertion has ≥1 Context
   - No support/refute encoded outside EvidenceLink
   - No contradictions outside AssertionRelation
   - IDs are unique, references resolve
   - TextSpan offsets are consistent (start < end)

---

# CSAG QA Procedure: CSAG_GENERATE_QA (with templates)

Generate QA items that make the extracted graph easy to query, validate, and reuse.

## General QA rules
- Each QAItem MUST have:
  - `question_text`
  - `expected_answer_type`
  - an `answers` list with at least 1 `Answer`
- Each Answer MUST include:
  - `answer_type`
  - one of (answer_text/answer_boolean/answer_number/answer_entity)
  - `supporting_assertions` and/or `supporting_evidence_links`
  - `answer_confidence`
- Prefer one best answer. If genuinely mixed, use categorical “mixed”.

## Evidence-status computation (for categorical answers)
Given all EvidenceLinks for an Assertion, compute:
- support_score = sum(weight(strength)) for supports
- refute_score = sum(weight(strength)) for refutes

Weights:
- very_strong=3, strong=2, moderate=1, weak=0.5, very_weak=0.25, unknown=0

Then:
- if support_score==0 and refute_score==0 → status=inconclusive
- else if support_score >= 1.5*refute_score and support_score>=1 → status=supports
- else if refute_score >= 1.5*support_score and refute_score>=1 → status=refutes
- else → status=mixed

---

## QA Templates (instantiate opportunistically)

You may create multiple QAItems per Assertion. Minimum recommendation:
- Always create **QA-STATUS** for each Assertion that has any EvidenceLink.
- Create **QA-BOOL** only when status is clearly supports or refutes.

### Template QA-STATUS (works for raw or normalized assertions)
**ID:** CSAG_QA_01_STATUS
**Question:** `What is the evidence status for the claim: "<ASSERTION_TEXT>"?`
**Expected answer type:** categorical
**Answer values:** `supports | refutes | mixed | inconclusive`
**How to answer:** compute status from EvidenceLinks and cite them in `supporting_evidence_links`.
**Use when:** the assertion has ≥1 EvidenceLink.

### Template QA-EVIDENCE-SUPPORT
**ID:** CSAG_QA_02_EVIDENCE_SUPPORT
**Question:** `What evidence supports the claim: "<ASSERTION_TEXT>"?`
**Expected answer type:** list
**Answer:** list of `EvidenceItem` ids (or short labels) via `supporting_evidence_links` (supports only).
**Use when:** at least one supports EvidenceLink exists.

### Template QA-EVIDENCE-REFUTE
**ID:** CSAG_QA_03_EVIDENCE_REFUTE
**Question:** `What evidence refutes the claim: "<ASSERTION_TEXT>"?`
**Expected answer type:** list
**Answer:** list of refuting EvidenceLinks/EvidenceItems.
**Use when:** at least one refutes EvidenceLink exists.

### Template QA-BOOL (only for clear cases)
**ID:** CSAG_QA_04_BOOL
**Question:** `Based on this paper, is it supported that: "<ASSERTION_TEXT>"?`
**Expected answer type:** boolean
**Answer:** true if status=supports; false if status=refutes.
**Use when:** status is supports or refutes (not mixed/inconclusive).

---

## Normalized-triple QA templates (only when normalization_status=fully_normalized)

These are higher-value for downstream review and reuse. Only generate when you have:
- subject/predicate/object + at least one meaningful Context.

### Template QA-TRIPLE-BOOL
**ID:** CSAG_QA_05_TRIPLE_BOOL
**Question:** `In <CONTEXT_LABEL>, does <SUBJECT_LABEL> (<SUBJECT_ID>) <PREDICATE_LABEL/ID> <OBJECT_LABEL> (<OBJECT_ID>)?`
**Expected answer type:** boolean
**Answer:** derived from evidence status (supports=true, refutes=false).
**Use when:** fully_normalized + evidence status supports/refutes.

### Template QA-TRIPLE-STATUS
**ID:** CSAG_QA_06_TRIPLE_STATUS
**Question:** `In <CONTEXT_LABEL>, what is the evidence status that <SUBJECT_LABEL> <PREDICATE_LABEL/ID> <OBJECT_LABEL>?`
**Expected answer type:** categorical
**Answer values:** supports/refutes/mixed/inconclusive
**Use when:** fully_normalized + any evidence.

### Template QA-CONTEXT-LIST
**ID:** CSAG_QA_07_CONTEXT_LIST
**Question:** `Under what biological contexts is the claim "<ASSERTION_TEXT>" evaluated in this paper?`
**Expected answer type:** list
**Answer:** list of Context ids (and/or labels) attached to the assertion/evidence.
**Use when:** assertion has ≥1 Context (always true); best when multiple contexts exist.

### Template QA-CONDITION-LIST (phase 3)
**ID:** CSAG_QA_08_CONDITION_LIST
**Question:** `Under what conditions (dose/time/genotype/treatment) does the claim "<ASSERTION_TEXT>" hold?`
**Expected answer type:** list
**Answer:** list of Condition ids (and/or readable summaries).
**Use when:** assertion has ≥1 Condition.

### Template QA-MECHANISM (phase 3)
**ID:** CSAG_QA_09_MECHANISM
**Question:** `What mechanism is proposed to explain: "<ASSERTION_TEXT>"?`
**Expected answer type:** free_text
**Answer:** short mechanism summary; cite InferenceSteps and EvidenceLinks.
**Use when:** there is at least one InferenceStep producing a mechanistic assertion.

---

## Critique/gap QA templates (phase 3)

### Template QA-LIMITATIONS
**ID:** CSAG_QA_10_LIMITATIONS
**Question:** `What limitations or flaws could weaken the claim: "<ASSERTION_TEXT>"?`
**Expected answer type:** list
**Answer:** list of StudyCritique ids (or brief text) that impact the assertion.
**Use when:** critiques exist impacting this assertion.

### Template QA-GAPS
**ID:** CSAG_QA_11_GAPS
**Question:** `What knowledge gaps remain for the claim: "<ASSERTION_TEXT>"?`
**Expected answer type:** list
**Answer:** list of KnowledgeGap ids (or brief text) related to the assertion.
**Use when:** gaps exist related to this assertion.

### Template QA-CONFLICTS
**ID:** CSAG_QA_12_CONFLICTS
**Question:** `Are there conflicting statements in this paper or cited literature about: "<ASSERTION_TEXT>"?`
**Expected answer type:** categorical
**Answer values:** yes | no | unclear
**Use when:** there is an AssertionRelation of type contradicts/qualifies involving this assertion.

---

## QA linking requirements
- Every QAItem should include `query_assertion: <assertion_id>` whenever the question is about that assertion.
- Every Answer should include `supporting_assertions: [<assertion_id>]` and/or `supporting_evidence_links: [...]`.

---

## Quality bar (what “good” looks like)
- Assertions are atomic and cover the paper’s real contributions.
- EvidenceLinks make it easy to retrieve supporting/refuting evidence.
- Context exists everywhere, even if coarse, and is enriched when possible.
- Normalization status is honest: fully_normalized only when the triple is actually solid.
- QA items let downstream systems ask: “what is supported, where, under what conditions, and by what evidence?”
