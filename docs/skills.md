# Skills

Each skill is a directory under `skills/` with a required `SKILL.md`. The frontmatter gives the name and short description; the body gives instructions, inputs, outputs, quality gates, and references. Optional subdirectories hold examples, scripts, tool notes, literature summaries, and reusable assets.

The table below is a reader-facing map. The source `SKILL.md` files are still canonical.

## Bioinformatics and Scientific Analysis

| Skill | Use when | Main result |
|---|---|---|
| `bio-foundation-housekeeping` | Starting a new bioinformatics project or normalizing an existing one. | A reproducible project scaffold with environments, schemas, manifests, and data cataloging. |
| `bio-reads-qc-mapping` | Ingesting raw reads, trimming or filtering them, and mapping reads to references or assemblies. | QC reports, cleaned reads, alignments, and coverage summaries. |
| `bio-assembly-qc` | Building genome, metagenome, or long-read assemblies. | Assemblies with QC metrics and assembly-level interpretation. |
| `tracking-taxonomy-updates` | Reconciling taxonomy across NCBI, GTDB, ICTV, eukaryote frameworks, and QuickClade-first domain triage. | Versioned taxonomy evidence and domain-specific routing decisions. |
| `bio-binning-qc` | Recovering and refining metagenomic bins. | MAG/bin sets with completeness, contamination, and chimerism checks. |
| `bio-gene-calling` | Calling genes and basic features in prokaryotic, viral, or eukaryotic sequence sets. | Predicted CDS, protein FASTA files, GFF annotations, and feature summaries. |
| `bio-annotation` | Assigning function and taxonomy from sequence homology. | Functional annotations, taxonomy calls, and evidence-ranked hit tables. |
| `bio-phylogenomics` | Building marker-gene or protein alignments and trees. | Alignments, phylogenetic trees, topology checks, and interpretation. |
| `bio-protein-clustering-pangenome` | Clustering proteins into orthogroups or building pangenome matrices. | Orthogroups, copy-number matrices, and core/accessory gene summaries. |
| `bio-structure-annotation` | Adding structure-based evidence to protein interpretation. | Predicted or searched structures, fold-level annotations, and confidence notes. |
| `bio-viromics` | Detecting, classifying, and QCing viral contigs. | Viral calls, quality summaries, taxonomy evidence, and candidate discovery tables. |
| `bio-stats-ml-reporting` | Aggregating results, training models, or preparing final analysis reports. | Validated statistics, model outputs, plots, and a reproducible report. |
| `bio-prefect-dask-nextflow` | Designing executable bioinformatics workflows. | Prefect+Dask or Nextflow scaffolds with clear execution boundaries. |
| `bio-workflow-methods-docwriter` | Turning workflow artifacts into a Methods section. | Reproducible Methods text with commands, versions, parameters, QC gates, and outputs. |
| `bio-logic` | Auditing scientific reasoning, study design, bias, or strength of evidence. | A structured critique with uncertainty, alternative explanations, and follow-up checks. |
| `jgi-lakehouse` | Querying JGI Lakehouse, GOLD, IMG, Mycocosm, or Phytozome data. | SQL-backed metadata pulls and, when allowed, downloaded IMG genome files. |

## Literature, Metadata, and APIs

| Skill | Use when | Main result |
|---|---|---|
| `polars-dovmed` | Searching PMC Open Access and bioRxiv with structured literature queries. | Source-backed literature summaries with fallback paths when the hosted API is unavailable. |
| `arxiv-search` | Searching recent or specific arXiv preprints. | Local Markdown summaries from arXiv metadata and IDs. |
| `biorxiv-search` | Searching bioRxiv preprints by keyword, date range, DOI, or author. | Filtered preprint shortlists with bioRxiv-native metadata. |
| `crossref-lookup` | Validating DOIs or matching titles to citation metadata. | Crossref records, DOI matches, and bibliography cleanup evidence. |
| `scientific-impact-assessment` | Comparing papers, journals, or literature shortlists by influence. | OpenAlex citation counts, optional Altmetric context, and impact summaries. |
| `get-api-docs` | Checking current API or SDK behavior before coding against a fast-moving interface. | Fresh documentation snippets gathered through the `chub` CLI. |

## Writing, Review, and Evaluation

| Skill | Use when | Main result |
|---|---|---|
| `scientific-writing` | Drafting, revising, or reviewing manuscripts, response letters, and grounded scientific prose. | A claim-safe draft or revision plan that stays tied to supplied evidence. |
| `manuscript-review-council` | Running a multi-angle manuscript review. | Parallel specialist reviews, disagreement checks, and an editor synthesis. |
| `proposal-review` | Reviewing grant, project, or funding proposals. | A decision-ready critique of strengths, risks, missing evidence, and fundability. |
| `ai-scientist-evaluator` | Evaluating finished outputs from one or more AI scientists. | A scored audit of rigor, reproducibility, novelty, task completion, and publication readiness. |

## Visualization, Notebooks, and Browser Work

| Skill | Use when | Main result |
|---|---|---|
| `notebooks` | Building or converting reproducible marimo or Jupyter notebooks. | A fully executed notebook with embedded figures and clear analysis flow. |
| `beautiful-data-viz` | Producing publication-quality matplotlib or seaborn figures. | High-data-ink static figures with readable axes, direct labels where feasible, tight layout, and appropriate palettes. |
| `plotly-dashboard-skill` | Building interactive Plotly Dash dashboards. | A production-ready dashboard layout with themed components and performant callbacks. |
| `agent-browser` | Automating browser navigation, scraping, form filling, screenshots, or UI checks. | Browser-driven evidence, screenshots, scraped content, or test observations. |

## Skill Source Links

The source directory for every skill is available under [`skills/`](https://github.com/fmschulz/omics-skills/tree/main/skills). When editing a skill, keep the `SKILL.md` frontmatter `name` equal to the directory name and rebuild the catalog afterward.
