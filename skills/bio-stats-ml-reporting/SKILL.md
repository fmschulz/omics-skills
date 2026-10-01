---
name: bio-stats-ml-reporting
description: Run statistics or machine learning on biological results and write a validated report. Use when testing hypotheses, training classifiers or rolling up discovery evidence.
---

# Bio Stats ML Reporting

Aggregate results, train ML models, and produce reports with validated references.

## Instructions

1. Join outputs in DuckDB and build feature tables. Hand large tables to ML code as Arrow (`.arrow()`, `.pl()`, or `.df()` on a DuckDB result) instead of writing intermediate CSVs.
2. Train baseline models and evaluate with cross-validation. Versions checked for this skill are in [docs/README.md](docs/README.md); pin the ones you use in the project's `pixi.toml`.
   - CPU baseline: scikit-learn for linear, tree, and clustering baselines; XGBoost for gradient boosting.
   - GPU node available (CUDA): set `device="cuda"` on XGBoost (supported since v2.0). For scikit-learn-style estimators (random forest, k-means, PCA, UMAP), RAPIDS cuML provides GPU equivalents; record the device in the run log.
   - On HPC, train through the scheduler (`sbatch`) and set explicit thread limits (`n_jobs`, `nthread`, `OMP_NUM_THREADS`) to match the allocation.
3. Generate reports and validate references.
   - Validate the prediction table with
     `scripts/validate_predictions.py`. Keep group identifiers and confounder
     labels in the table so the gate can detect sample/group leakage, class
     imbalance, calibration failure, batch-outcome imbalance, and performance
     that does not beat the majority-class null.
4. For exploratory omics projects, aggregate discovery evidence across the literature-derived analysis playbook, annotation, phylogenomics, viromics, and comparative-genomics outputs.
5. **Comparative-axes rollup** — join the per-axis comparison artifacts produced by upstream skills into a single `comparative_axes_summary.tsv`. The rollup must have one row per (query genome, axis) and include:
   - `genome-property frontier` (size, gene count, etc. — link to `relative_genome_metrics.tsv` and `genome_size_frontier.tsv`)
   - `marker-gene census` (link to `marker_census.tsv`)
   - `family copy-number expansions/contractions` (link to `family_copy_number_comparison.tsv` and `family_expansion_candidates.tsv`)
   - `synteny / conserved neighborhoods` (link to `conserved_neighborhoods.tsv`)
   - `non-coding RNA census` (link to `ncRNA_census.tsv`)
   Each row records observation, comparison baseline, literature reference, status (notable / conserved / artifact / negative), and a follow-up test.
6. Produce an interesting-findings section that ranks candidate discoveries relative to the literature-derived baseline and separates:
   - strong candidates with multiple evidence types
   - plausible candidates needing validation
   - likely artifacts or conserved lineage features
   - explicit negative findings where nothing notable was detected
7. Include the comparison baseline, literature context, confidence, and next discriminating analyses for each candidate.
8. Draw report figures (performance curves, calibration plots, effect sizes) with `/beautiful-data-viz`: grey by default, color only for the compared models or the one highlighted result.

## Quick Reference

| Task | Action |
|------|--------|
| Validate predictions | `uv run --script skills/bio-stats-ml-reporting/scripts/validate_predictions.py predictions.tsv --report validation.json --require-beats-null` |

## Input Requirements

Prerequisites:
- Tools declared in the project's pinned Pixi environment. See `docs/README.md` for expected tools.
- Results tables and metadata are available.
Inputs:
- results/*.parquet or results/*.tsv
- metadata.tsv

## Output

- results/bio-stats-ml-reporting/models/
- results/bio-stats-ml-reporting/metrics.tsv
- results/bio-stats-ml-reporting/comparative_axes_summary.tsv
- results/bio-stats-ml-reporting/discovery_summary.tsv
- results/bio-stats-ml-reporting/report.md
- results/bio-stats-ml-reporting/logs/
- results/bio-stats-ml-reporting/prediction_validation.json

## Quality Gates

- [ ] Model performance sanity checks pass.
- [ ] Reference validation passes.
- [ ] On execution failure, preserve logs and report the failed command; retry only after diagnosing the cause and recording the changed parameters. Report unmet biological thresholds as results; never tune parameters solely to pass a gate.
- [ ] Verify input tables are readable and schema-consistent.
- [ ] Discovery summary joins candidate genes/features to annotation evidence, comparison baseline, literature context, and confidence.
- [ ] `comparative_axes_summary.tsv` covers all five mandatory axes (genome-property frontier, marker-gene census, family copy-number, synteny/neighborhoods, ncRNA census) for every query genome, with rows for axes that produced negative findings.
- [ ] Final report states what is interesting, what is conserved/expected, what is likely artifact, and what should be tested next.
- [ ] Grouped splits have no sample or group overlap, calibration is reported,
      confounding and imbalance are quantified, and the model is compared with
      a declared null baseline.
