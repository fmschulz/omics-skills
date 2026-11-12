# Validation

The tests show that the pack's contracts hold on small fixtures. They do not show that the external tools produce correct biology. The pack ships fixture tests only; the table keeps the three kinds of claim apart.

## Evidence levels

| Level | Required evidence | Permitted claim |
|---|---|---|
| Fixture | Deterministic local inputs, schemas, command plans, normalized outputs and failure tests | The repository contract works on the fixture. |
| Scheduler integration | Pinned environment and databases, a completed scheduler job, exit state, elapsed time, peak RSS and checked outputs | The pinned external tools ran on the named scheduler profile. |
| Biological validation | Versioned truth labels, stratified scientific metrics, controls and documented limitations | The tested tool stack reached the reported metrics on the named truth set. |

One level does not imply the next. A completed Slurm job is not biological validation until its result is scored against truth labels.

## What the tests cover

`make test` runs the skill, supplementary-doc and citation validators, and the unit and fixture tests. For skills that ship a driver or an artifact builder, the fixture tests check command plans, restart and reuse decisions, output normalization, schema validation and failure paths. They do not run the heavy external tools or their databases. A production run still needs pinned databases and containers, a scheduler job, and the QC gates in each skill.
