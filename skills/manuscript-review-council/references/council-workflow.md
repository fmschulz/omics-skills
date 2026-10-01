# Council Workflow

Use this staged workflow for every manuscript review.

## Stage 0: Shared Review Packet

Prepare a common packet before delegation:
- title and abstract
- sectioned manuscript text
- figure and table list
- main claims to evaluate
- methods snapshot
- user priorities or journal rubric
- prior reviews and rebuttal material when reviewing a revision

## Stage 1: Independent Reviewers

Run the three core reviewers independently:
- domain reviewer
- methods and statistics reviewer
- skeptical reviewer

Add support reviewers only when the manuscript warrants them.

Keep reviewer outputs separate. Do not average them into a single voice during this stage.

## Stage 2: Cross-Review And Adjudication

Build a conflict log:
- disagreements on recommendation
- disagreements on severity
- mutually incompatible interpretations
- duplicated concerns that should be merged

For each disagreement, decide:
- resolved by stronger evidence
- unresolved but non-blocking
- unresolved and decision-driving

## Stage 3: Editor Synthesis

The editor writes:
- recommendation
- short rationale
- ranked major revisions
- ranked minor revisions
- questions for authors
- short decision letter or meta-review summary

## Artifact Bundle

Retain these artifacts even if the user only asked for prose:
- shared review packet
- reviewer reports
- conflict log
- editor meta-review

Persist them under `reviews/<manuscript-slug>/<YYYYMMDDTHHMMSSZ>/`: `packet.json`, `reviewers/<role>.json`, `conflicts.json`, `editor.json`, and a bundle index (for example `bundle.json`) that lists these paths and holds the machine-readable issue records. Validate the index with `scripts/validate_review_bundle.py`, which checks it against [../schemas/review-bundle.schema.json](../schemas/review-bundle.schema.json) and enforces the paths above; do not use ad hoc filenames that cannot be joined across runs. Set the bundle `mode` to `critique`, `revision_assessment`, or `rebuttal_assessment`.

## Decision Discipline

- Ground criticism in the manuscript or in explicit missing information.
- Do not invent literature, reviewer expectations, or venue rules.
- Make confidence visible.
- Keep the final recommendation consistent with the ranked issues.
