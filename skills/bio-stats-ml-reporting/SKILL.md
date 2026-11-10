---
name: bio-stats-ml-reporting
description: Run statistics or machine learning on biological results and write a validated report. Use when testing hypotheses, training classifiers or rolling up discovery evidence.
disable-model-invocation: true
---

# Bio Stats ML Reporting

Aggregate results, train ML models, validate the predictions, and roll up discovery evidence into a report. Shared pipeline rules: read `~/.agents/skills/omics-pipeline/SKILL.md` first (in a plugin install, `../omics-pipeline/SKILL.md` from this file).

## Instructions

Tool versions: [docs/README.md](docs/README.md). DuckDB guide: [docs/duckdb.md](docs/duckdb.md).

1. Join the outputs in DuckDB and build feature tables. Hand large tables to ML code as Arrow (`.arrow()`, `.pl()`, or `.df()` on a DuckDB result) instead of writing intermediate CSVs.
2. Train baseline models and evaluate with cross-validation: scikit-learn for linear, tree, and clustering baselines; XGBoost for gradient boosting. On a CUDA GPU node, set `device="cuda"` on XGBoost (supported since v2.0); RAPIDS cuML gives GPU equivalents of scikit-learn-style estimators (random forest, k-means, PCA, UMAP). Record the device in the run log.
3. Validate the prediction table before you report any model:

   ```bash
   uv run --script ~/.agents/skills/bio-stats-ml-reporting/scripts/validate_predictions.py \
     predictions.tsv --report validation.json --require-beats-null
   ```

   Keep group identifiers and confounder labels in the table so the gate can detect sample/group leakage, class imbalance, calibration failure, batch-outcome imbalance, and performance that does not beat the majority-class null.
4. For exploratory omics projects, aggregate discovery evidence across the literature-derived analysis playbook, annotation, phylogenomics, viromics, and comparative-genomics outputs.
5. Roll up the per-axis comparison artifacts of the upstream skills into `comparative_axes_summary.tsv`, with one row per (query genome, axis). The five axes link to these files:
   - genome-property frontier: `relative_genome_metrics.tsv`, `genome_size_frontier.tsv`
   - marker-gene census: `marker_census.tsv`
   - family copy-number expansions and contractions: `family_copy_number_comparison.tsv`, `family_expansion_candidates.tsv`
   - synteny and conserved neighborhoods: `conserved_neighborhoods.tsv`
   - non-coding RNA census: `ncRNA_census.tsv`

   Each row records the observation, comparison baseline, literature reference, status (notable, conserved, artifact, or negative), and a follow-up test.
6. Write an interesting-findings section that ranks candidates against the literature-derived baseline and separates strong candidates with multiple evidence types, plausible candidates needing validation, likely artifacts or conserved lineage features, and explicit negative findings. Give each candidate its comparison baseline, literature context, confidence, and next discriminating analyses.
7. Draw report figures (performance curves, calibration plots, effect sizes) with `/beautiful-data-viz`.

## Input Requirements

- `results/*.parquet` or `results/*.tsv`, and `metadata.tsv`.

## Output

- results/bio-stats-ml-reporting/models/
- results/bio-stats-ml-reporting/metrics.tsv
- results/bio-stats-ml-reporting/comparative_axes_summary.tsv
- results/bio-stats-ml-reporting/discovery_summary.tsv
- results/bio-stats-ml-reporting/report.md
- results/bio-stats-ml-reporting/logs/
- results/bio-stats-ml-reporting/prediction_validation.json

## Quality Gates

- [ ] Input tables are readable and schema-consistent.
- [ ] Grouped splits have no sample or group overlap, calibration is reported, confounding and imbalance are quantified, and the model is compared with a declared null baseline.
- [ ] The discovery summary joins candidate genes and features to annotation evidence, comparison baseline, literature context, and confidence.
- [ ] `comparative_axes_summary.tsv` covers all five axes for every query genome, with rows for axes that produced negative findings.
- [ ] The final report states what is interesting, what is conserved or expected, what is likely artifact, and what to test next.
