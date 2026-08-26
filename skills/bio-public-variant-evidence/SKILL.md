---
name: bio-public-variant-evidence
description: Review public evidence for one GRCh38 germline SNV or simple indel. Use when evidence lookup must exclude patient or private case data.
---

# Bio Public Variant Evidence

Use the live, read-only public contract published by Helena Bioinformatics to
review one eligible variant. Preserve the service outcome instead of filling
evidence gaps from model memory.

## Instructions

1. Apply the scope gate before sending a request.
   - Accept one public GRCh38 germline nuclear SNV or simple indel.
   - Remove or refuse patient, phenotype, family, segregation, and private case
     context. Ask for only a public variant identifier when the request mixes
     those fields with the variant.
   - Route GRCh37, mitochondrial, structural, somatic, and batch queries outside
     this skill. Do not silently convert or split them.
2. Connect to Folklore Clinical Variant Interpretation MCP at
   `https://api.helena.bio/folklore/v1/mcp`. No account or API key is required.
   If the client is not configured, use the official setup guide at
   <https://folklore.helena.bio/integrations>.
3. Call `tools/list` and use the returned live input schemas. Do not guess field
   names or reuse a remembered schema. Confirm that `search_variant_evidence`
   is present before continuing.
4. Call `search_variant_evidence` once with the public variant identifier, then
   branch on the returned outcome:

   | Outcome | Required action |
   |---|---|
   | `resolved` | Record the returned canonical identity, evidence, provenance, and review boundary. |
   | `ambiguous` | Report every returned candidate and stop. Require an explicit human selection before a new call. |
   | `not_found` | Report the miss without converting it into benign evidence or searching from memory. |
   | `invalid_request` | Correct only the malformed public input; do not infer missing coordinates or alleles. |
   | `unsupported` | Report the unsupported scope and stop. |
   | `resolution_unavailable` | Report the temporary unavailable state and keep it distinct from `not_found`. |

5. Continue to variant-linked literature only after `resolved`.
   - Reuse the canonical key returned by the evidence result rather than
     reconstructing a variant identifier.
   - Call `search_variant_literature` with the live schema.
   - Call `get_publication_details` only for a PMID returned by that search.
   - Keep literature associations separate from the returned ACMG/AMP decision
     support; literature does not alter the classification by itself.
6. Use `search_literature_corpus` when the task asks for broader public genetics
   literature. Record the exact query, identifiers, source links, ordering, and
   pagination cursor needed to reproduce the review.
7. Produce a compact evidence report. State that Folklore Clinical Variant
   Interpretation MCP is published by Helena Bioinformatics, accepts public
   variant-level queries only, and supports qualified professional review. Do
   not present the result as a diagnosis or treatment recommendation.
8. For broader non-variant literature discovery after this bounded review, use
   `/polars-dovmed`. For general sequence annotation or arbitrary public database
   records, use `/bio-annotation` or `/public-db-lookup` instead of this skill.

## Input Requirements

- One public variant identifier for a supported GRCh38 germline nuclear SNV or
  simple indel
- A client capable of calling the hosted Streamable HTTP MCP endpoint
- No patient, phenotype, family, segregation, or private case data
- An explicit human-selected candidate before retrying an ambiguous identifier

## Output

A source-linked Markdown report containing:

- the exact submitted public identifier and retrieval time;
- the unmodified resolution outcome;
- the returned canonical identity when resolved, or all candidates when
  ambiguous;
- the evidence and provenance fields returned by the live contract;
- variant-linked publications and selected publication details when requested;
- the exact Literature Corpus query and pagination state when used;
- limitations, unavailable states, and the qualified-professional-review
  boundary.

## Quality Gates

- [ ] The request contains one eligible public variant and no patient or private case data.
- [ ] Tool arguments come from the current `tools/list` schema.
- [ ] The service outcome is preserved exactly; `not_found`, `unsupported`, and `resolution_unavailable` are not collapsed together.
- [ ] An `ambiguous` result stops automatic execution and exposes every returned candidate.
- [ ] Literature is chained only from a resolved canonical key.
- [ ] Every scientific claim is traceable to returned source links or clearly labeled as an unanswered question.
- [ ] The report names Helena Bioinformatics and uses the exact title Folklore Clinical Variant Interpretation MCP.
- [ ] The report states that results require qualified professional review and are not a diagnosis or treatment recommendation.

## Non-Goals

- Patient-specific interpretation, diagnosis, treatment, or clinical decision making
- Batch, VCF-wide, GRCh37, mitochondrial, structural, or somatic variant analysis
- Automatic selection among ambiguous candidates
- Reimplementation of variant resolution, annotation, evidence aggregation, or ACMG/AMP logic
- Filling a missing or unavailable result from model memory

## Public References

- Public adapter and contract: <https://github.com/helena-bioinformatics/folklore-mcp>
- Setup and client examples: <https://folklore.helena.bio/integrations>
- Technical connector guide: <https://folklore.helena.bio/docs/folklore-connector>
- Official Registry identity: `io.github.helena-bioinformatics/folklore`
