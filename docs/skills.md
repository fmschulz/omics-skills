# Skills

One row per skill. Each skill's `SKILL.md` is the authoritative description: its frontmatter gives the name and trigger, and its body gives instructions, inputs, outputs and quality gates. The sources are under [`skills/`](https://github.com/fmschulz/omics-skills/tree/main/skills).

## Omics analysis

| Skill | Use when | Main result |
|---|---|---|
| `bioinformatics-project` | Starting, reorganizing, or reproducibility-hardening a bioinformatics project. | Project layout, pinned environment, task records, hypothesis register, restartable drivers, provenance, and sharing metadata. |
| `bio-foundation-housekeeping` | Defining metadata schemas or adding a queryable data catalog. | Generated LinkML/Pydantic models, cross-record validation, normalized Parquet tables, fixtures, and a DuckDB catalog. |
| `exploratory-data-analysis` | Inspecting an unfamiliar scientific data file before choosing a workflow. | A Markdown report covering file type, structure, quality issues, and downstream analysis options. |
| `bio-reads-qc-mapping` | Ingesting raw reads, trimming or filtering them, and mapping reads to references or assemblies. | Per-sample trimmed reads, fastp reports for short reads, SAM alignments when a reference is given, a run manifest, and a mapping-status table. |
| `bio-assembly-qc` | Assembling QC-passed reads into isolate or metagenome contigs and checking contiguity. | Per-sample `contigs.fasta`, QUAST or MetaQUAST `report.tsv`, a run manifest, and QuickClade domain routing. |
| `tracking-taxonomy-updates` | Comparing NCBI, GTDB, ICTV, or eukaryotic taxonomy releases, or assigning taxonomy to sequences. | Versioned change and conflict report, QuickClade `domain_routing.tsv`, and GTDB-Tk, EukCC, vConTACT3, or GVClass assignments. |
| `bio-binning-qc` | Binning a metagenome assembly with QuickBin or scoring bin completeness, contamination, and chimerism. | Bins, QuickClade domain routing, `bin_metrics.tsv` with CheckM2, GUNC, or EukCC scores, and GTDB-Tk taxonomy. |
| `bio-gene-calling` | Calling CDS in prokaryotic, viral, or eukaryotic assemblies, or counting tRNA and rRNA genes. | Gene models, protein and coding sequences per assembly (BRAKER outputs for eukaryotes), an `ncRNA_census.tsv` of tRNA and rRNA counts, and gene metrics. |
| `bio-annotation` | Assigning function and taxonomy from sequence homology. | Annotation and taxonomy Parquet tables, `marker_census.tsv`, a family copy-number matrix, and `discovery_candidates.tsv`. |
| `bio-fasta-database-curator` | Preparing sequence databases for BLAST, DIAMOND, MMseqs2, HMMER, pyhmmer, or custom reference searches. | Curated FASTA/FAA files, stable headers, deduplicated records, mapping tables, and database statistics. |
| `bio-phylogenomics` | Inferring marker-gene phylogenies, placing genomes, choosing substitution models, or checking tree support. | Per-marker trimmed alignments, ML trees, support tables, `closest_relatives.tsv`, and fetched relative genomes and proteomes. |
| `bio-interdomain-hgt` | Testing interdomain horizontal gene transfer and donor direction. | Homology, context, contamination, and per-gene phylogenetic evidence for candidate transfers. |
| `bio-protein-clustering-pangenome` | Clustering proteins into orthogroups, or comparing gene-family copy number and core/accessory content. | Orthogroups, presence/absence and copy-number matrices, family fold-change table, conserved neighborhoods, and marker and ncRNA censuses. |
| `bio-structure-annotation` | Adding structure-based evidence to protein interpretation. | Predicted or searched structures, fold-level annotations, and confidence notes. |
| `bio-viromics` | Detecting, classifying, and QCing viral contigs. | Viral calls, quality summaries, taxonomy evidence, and candidate discovery tables. |
| `bio-stats-ml-reporting` | Testing hypotheses, training classifiers, or rolling up discovery evidence from biological results. | Models and `metrics.tsv`, prediction validation, `comparative_axes_summary.tsv`, `discovery_summary.tsv`, and `report.md`. |
| `bio-prefect-dask-nextflow` | Designing a local, distributed, or Slurm-backed bioinformatics workflow. | Engine recommendation with rationale, runnable Prefect+Dask or Nextflow scaffold, per-step resource plan, and validation plan. |
| `bio-workflow-methods-docwriter` | Turning Nextflow, Snakemake, or CWL run artifacts into a Methods section. | Schema-validated `run_manifest.yaml` and `METHODS.md` with exact commands, versions, parameters, QC, and outputs. |
| `bio-logic` | Auditing scientific reasoning, study design, bias, or strength of evidence. | A structured critique with uncertainty, alternative explanations, and follow-up checks. |

## Literature and metadata

| Skill | Use when | Main result |
|---|---|---|
| `polars-dovmed` | Searching PMC Open Access or bioRxiv full text via the hosted API or parquet. | A run directory with `query.json`, raw responses, and timings, plus a paper list with relevance notes. |
| `arxiv-search` | Finding CS, math, physics, statistics, or quantitative-biology preprints, or resolving arXiv IDs. | JSON search results from the arXiv API and optional Markdown notes per arXiv ID. |
| `biorxiv-search` | Scanning bioRxiv preprints by date range, category, or author, or looking up bioRxiv DOIs. | JSON matches from a bounded date window, keyword-filtered locally, with scan counts and truncation warnings. |
| `crossref-lookup` | Validating DOIs or matching titles to citation metadata. | Crossref records, DOI matches, and bibliography cleanup evidence. |
| `public-db-lookup` | Fetching a record from UniProt, NCBI, MGnify, InterPro, AlphaFold DB, STRING, or ENA. | A compact JSON envelope with bounded records, counts, and an optional raw-response file. |
| `scientific-impact-assessment` | Comparing papers, journals, or literature shortlists by influence. | OpenAlex citation counts and history, curated journal impact factors, and optional Altmetric data. |
| `pdf-to-md` | Converting papers, PDFs, or office documents into analysis-ready Markdown. | Clean Markdown and, for papers, structured article and section-audit artifacts. |

## Writing and review

| Skill | Use when | Main result |
|---|---|---|
| `scientific-writing` | Drafting or revising manuscript sections, proposal narratives, or rebuttals, or running a clarity review. | Draft or revised prose within the evidence, severity-tagged findings, a citation audit, and unresolved evidence gaps. |
| `csag-extraction` | Converting manuscripts into structured Conditional Scientific Argumentation Graphs. | Schema-valid claim/evidence/inference graphs with TextSpan grounding, validation reports, and paper-grounded Q&A items. |
| `manuscript-review-council` | Running a journal-style peer review, or checking a revision or rebuttal against prior objections. | Role-separated reviewer reports, an adjudication log, an editor meta-review with recommendation, and a validated review bundle. |
| `proposal-review` | Scoring an AI/ML, computational-biology, or bioscience proposal for a funding decision. | Structured review, risk register, weighted scorecard, funding recommendation with conditions, and questions for the PI. |
| `ai-scientist-evaluator` | Evaluating finished outputs from one or more AI scientists. | A scored audit of rigor, reproducibility, novelty, task completion, and publication readiness. |

## Visualization and notebooks

| Skill | Use when | Main result |
|---|---|---|
| `notebooks` | Building or converting reproducible marimo or Jupyter notebooks. | A fully executed notebook with embedded figures and clear analysis flow. |
| `beautiful-data-viz` | Making, restyling, or reviewing any plot, chart, figure, dashboard, or data visual. | Greyscale-first PNG, SVG, PDF, or HTML figures, color only to encode information, and reproducible plotting code. |
| `plotly-dashboard-skill` | Building interactive Plotly Dash dashboards. | Dash app scaffold with layout, callbacks, one registered figure template, and a README with usage notes. |
