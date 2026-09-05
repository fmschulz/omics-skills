# Skill Quality

This page records the v1.5 quality pass across all 34 checked-in skills. It distinguishes executable, fixture-backed behavior from guidance that still depends on external tools, databases, schedulers, or scientific datasets.

## Executive Summary

Version 1.5 closed every item carried forward from the v1.4 quality backlog except the explicitly deferred `jgi-lakehouse` work; that skill was later removed from the pack rather than completed. The release adds restartable drivers and normalized artifacts to the core omics workflows, strengthens metadata and project scaffolding, expands literature-client resilience, adds real notebook and visualization smoke tests, and makes review outputs schema-validatable.

The tests exercise small deterministic fixtures, command planning, normalization, restart behavior, schema validation, routing, and failure modes. They do not claim biological validation of every external program or reference database. Production runs must still pin the actual databases and containers, execute scheduler-backed tools, and apply the scientific QC gates documented by each skill.

## v1.5 Completion Record

| Skill | v1.5 result |
|---|---|
| `ai-scientist-evaluator` | Validates review JSON, reloads the selected weight profile, recomputes category totals, and routes AI-generated notebook audits through the evaluator. |
| `arxiv-search` | Adds expiring response caches, a cross-process pacing lock, and routing coverage for physics, computer science, and direct arXiv identifiers. |
| `beautiful-data-viz` | Annotation helpers inherit active text colors; a pinned Pixi environment and fixture export PNG, SVG, and PDF with metadata. |
| `bio-annotation` | Adds a fixture-backed bundle builder for normalized annotations, taxonomy, markers, family copy number, domain routing, and discovery candidates. |
| `bio-assembly-qc` | Adds restartable short-read, long-read, and metagenome plans with read-QC prerequisites, normalized assembler outputs, and QUAST/MetaQUAST gates. |
| `bio-binning-qc` | Restricts GUNC to prokaryotic bins and joins QuickClade/GTDB-Tk routing with normalized MAG QC tables. |
| `bio-fasta-database-curator` | Uses SHA-256 deduplication, validates raw headers before parsing, handles empty input, and writes mapping and deduplication reports from one CLI. |
| `bio-foundation-housekeeping` | Adds compatible and breaking LinkML extension fixtures, a schema compatibility report, and an explicit migration record. |
| `bio-gene-calling` | Routes prokaryotic, viral, and eukaryotic assemblies to Pyrodigal, pyrodigal-gv, and BRAKER4 plans with pinned resource manifests and ncRNA steps. |
| `bioinformatics-project` | Adds opt-in MIT license and citation templates that require explicit author and copyright inputs. |
| `bio-interdomain-hgt` | Adds a versioned evidence driver for homology, RBH, direction, frame-aware context, per-gene tree planning, normalization, database manifests, and hypothesis reflections. |
| `bio-logic` | Adds study-type profiles for intervention, observational, computational, evolutionary, and exploratory work; corrects association and causal-design guidance. |
| `bio-phylogenomics` | Adds reference checksums, fixed seeds, restartable marker/alignment/trimming/tree plans, and normalized support values. |
| `bio-prefect-dask-nextflow` | Creates and closes Dask clusters inside flow runtime, fixes FASTQ output naming, and adds an `sbatch` Nextflow launcher with post-run checks. |
| `bio-protein-clustering-pangenome` | Persists copy-number, presence/absence, marker, ncRNA, family comparison, and synteny artifacts for a tested multi-genome fixture. |
| `bio-reads-qc-mapping` | Adds a sample-sheet schema, paired/single/long-read fixtures, conditional mapping gates, restartable command plans, and execution receipts. |
| `bio-stats-ml-reporting` | Adds executable checks for sample and group split leakage, confounding, calibration, imbalance, and null baselines. |
| `bio-structure-annotation` | Adds smoke-tested Boltz input generation, Foldseek padded-database handling, and a TM-Vec wrapper; public MSA submission remains approval-gated. |
| `bio-viromics` | Adds pinned resource manifests and normalized frontier, marker, family-copy, synteny, ncRNA, discovery, hypothesis, and reflection artifacts. |
| `bio-workflow-methods-docwriter` | Adds Snakemake and CWL extractors and strengthens the Nextflow evidence path with trace, versions, inputs, outputs, run identity, and redaction fixtures. |
| `biorxiv-search` | Adds bounded retry/backoff, explicit latest-version behavior, and separate author-variant match groups. |
| `crossref-lookup` | Removes the hidden writing-skill dependency, normalizes BibTeX fields, distinguishes missing records from transient failures, and adds strict audit exits. |
| `csag-extraction` | Validates against the authoritative LinkML-derived schema before semantic checks and makes missing text grounding fail strict mode. |
| `exploratory-data-analysis` | Adds representative fixtures and analyzers across sequence, structure, array, and mass-spectrometry families, with streaming or memory mapping for large inputs. |
| `manuscript-review-council` | Separates critique from rebuttal drafting, defines deterministic review-bundle paths, and validates machine-readable issues against JSON Schema. |
| `notebooks` | Pins template dependencies, uses an explicit project-kernel placeholder, and tests Jupyter-to-marimo and marimo-to-Jupyter conversion fixtures. |
| `pdf-to-md` | Adds complete and missing-author paper bundles that test section audit, article validation, figure handling, and credible missing-field behavior. |
| `plotly-dashboard-skill` | Adds a pinned runnable Dash example, HTTP startup smoke test, pure-callback performance check, and linked QA guidance. |
| `polars-dovmed` | Adds a complete processed-output fallback fixture and records the upstream corpus revision in query metadata. |
| `proposal-review` | Validates sponsor-defined rubrics or normalized default weights and maps scores to deterministic recommendation categories. |
| `scientific-impact-assessment` | Adds OpenAlex cache expiry, cross-process request pacing, and report-level cache policy metadata. |
| `scientific-writing` | Removes generic `write` triggering and distinguishes prose drafting and revision from scientific critique and review-council work. |
| `tracking-taxonomy-updates` | Moves GTDB-Tk, EukCC, vConTACT3, and GVClass examples behind scheduler templates and converts QuickClade results into tested domain-routing tables. |

## Biological Validation Status

The [biological validation reference](biological-validation.md) defines candidate truth sets and scheduler evidence for the eight core omics skills. The registry distinguishes synthetic truth, biological proxies, and empirical labels. It also records task-specific metrics because assembly, topology, orthology, annotation, viral detection, and HGT direction cannot share one accuracy threshold.

All registered datasets remain `candidate` until downloaded artifacts receive local SHA-256 values. The first scheduler pilot targets phylogenomics because it does not require a large reference database. Its job manifest remains `draft` until the low-memory cluster profile, remote paths, QfO subset, reference tree, and solved Pixi lock are fixed.

Comparative-discovery thresholds still require separate prokaryote, eukaryote, phage, and Nucleocytoviricota campaigns. The `jgi-lakehouse` item that this program excluded is moot: the skill was removed.
