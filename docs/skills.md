# Skills

One row per skill. Each skill's `SKILL.md` is the authoritative description: its frontmatter gives the name and trigger, and its body gives instructions, inputs, outputs and quality gates. The sources are under [`skills/`](https://github.com/fmschulz/omics-skills/tree/main/skills).

Two kinds of skill exist. A **model-visible** skill is listed in every session, and the model loads it when its description fits the task. A **pipeline stage** skill is hidden (`disable-model-invocation: true` in Claude Code, `allow_implicit_invocation: false` for Codex), so its description costs no prompt space. The model reaches a stage through `omics-pipeline`, which holds the stage table and the rules every stage shares, and then reads the stage's `SKILL.md`. A person can still call a stage by name, such as `/bio-annotation`.

## Model-visible skills

| Skill | Use when | Main result |
|---|---|---|
| `omics-pipeline` | A genome, metagenome, or viral analysis needs a stage workflow, a driver script, or the shared pipeline rules. | The stage to read, the shared rules (domain routing first, hypothesis register, five comparative axes, environment, scheduler), a Nextflow submit wrapper, and a workflow-engine guide. |
| `bioinformatics-project` | Starting, reorganizing, or reproducibility-hardening a bioinformatics project. | Project layout, pinned environment, task records, hypothesis register, restartable drivers, provenance, and sharing metadata. |
| `exploratory-data-analysis` | Inspecting an unfamiliar scientific data file before choosing a workflow. | A Markdown report covering file type, structure, quality issues, and downstream analysis options. |
| `public-db-lookup` | Fetching a record from UniProt, NCBI, MGnify, InterPro, AlphaFold DB, STRING, or ENA. | A compact JSON envelope with bounded records, counts, and an optional raw-response file. |
| `bio-workflow-methods-docwriter` | Turning Nextflow, Snakemake, or CWL run artifacts into a Methods section. | Schema-validated `run_manifest.yaml` and `METHODS.md` with exact commands, versions, parameters, QC, and outputs. |
| `bio-logic` | Auditing scientific reasoning, study design, bias, or strength of evidence behind project results. | A structured critique with uncertainty, alternative explanations, and follow-up checks. |
| `polars-dovmed` | Searching PMC Open Access or bioRxiv full text, through the connector or the hosted API or parquet script. | A run directory with `query.json`, raw responses, and timings, plus a paper list with relevance notes. |
| `preprint-search` | Finding arXiv preprints or ID metadata, or scanning bioRxiv by date range, category, author, or DOI. | JSON search results, optional Markdown notes per arXiv ID, and bioRxiv scan counts with truncation warnings. |
| `crossref-lookup` | Validating DOIs, matching titles to citation metadata, or comparing papers and journals by citation impact. | Crossref records, DOI matches, bibliography cleanup evidence, and OpenAlex citation counts with curated journal metrics. |
| `proposal-review` | Scoring an AI/ML, computational-biology, or bioscience proposal for a funding decision. | Structured review, risk register, weighted scorecard, funding recommendation with conditions, and questions for the PI. |
| `ai-scientist-evaluator` | Evaluating finished outputs from one or more AI scientists. | A scored audit of rigor, reproducibility, novelty, task completion, and publication readiness. |
| `notebooks` | Building or converting reproducible marimo or Jupyter notebooks. | A fully executed notebook with embedded figures and clear analysis flow. |
| `beautiful-data-viz` | Making, restyling, or reviewing any plot, chart, figure, dashboard, or data visual. | Greyscale-first PNG, SVG, PDF, or HTML figures, color only to encode information, reproducible plotting code, and a Plotly Dash guide with an example app. |

## Pipeline stages

Read these through `omics-pipeline`. They keep their names, drivers, fixtures and tests, so projects that call their scripts by path keep working.

| Skill | Use when | Main result |
|---|---|---|
| `tracking-taxonomy-updates` | Routing sequences by domain with QuickClade before any domain-specific stage, comparing NCBI, GTDB, ICTV, or eukaryotic taxonomy releases, or assigning taxonomy. | `results/taxonomy/domain_routing.tsv`, GTDB-Tk, EukCC, vConTACT3, or GVClass assignments, and a versioned release change and conflict report. |
| `bio-reads-qc-mapping` | Ingesting raw reads, trimming or filtering them, and mapping reads to references or assemblies. | Per-sample trimmed reads, fastp reports for short reads, SAM alignments when a reference is given, a run manifest, and a mapping-status table. |
| `bio-assembly-qc` | Assembling QC-passed reads into isolate or metagenome contigs and checking contiguity. | Per-sample `contigs.fasta`, QUAST or MetaQUAST `report.tsv`, and a run manifest. |
| `bio-binning-qc` | Binning a metagenome assembly with QuickBin or scoring bin completeness, contamination, and chimerism. | Bins, `bin_metrics.tsv` with CheckM2, GUNC, or EukCC scores, and GTDB-Tk taxonomy. |
| `bio-gene-calling` | Calling CDS in prokaryotic, viral, or eukaryotic assemblies, or counting tRNA and rRNA genes. | Gene models, protein and coding sequences per assembly (BRAKER outputs for eukaryotes), an `ncRNA_census.tsv` of tRNA and rRNA counts, and gene metrics. |
| `bio-annotation` | Assigning function and taxonomy from sequence homology. | Annotation and taxonomy Parquet tables, `marker_census.tsv`, a family copy-number matrix, and `discovery_candidates.tsv`. |
| `bio-viromics` | Detecting, classifying, and QCing viral contigs. | Viral calls, quality summaries, taxonomy evidence, and candidate discovery tables. |
| `bio-phylogenomics` | Inferring marker-gene phylogenies, placing genomes, choosing substitution models, or checking tree support. | Per-marker trimmed alignments, ML trees, support tables, `closest_relatives.tsv`, and fetched relative genomes and proteomes. |
| `bio-protein-clustering-pangenome` | Clustering proteins into orthogroups, or comparing gene-family copy number and core/accessory content. | Orthogroups, presence/absence and copy-number matrices, family fold-change table, conserved neighborhoods, and marker and ncRNA censuses. |
| `bio-interdomain-hgt` | Testing interdomain horizontal gene transfer and donor direction. | Homology, context, contamination, and per-gene phylogenetic evidence for candidate transfers. |
| `bio-structure-annotation` | Adding structure-based evidence to protein interpretation. | Predicted or searched structures, fold-level annotations, and confidence notes. |
| `bio-stats-ml-reporting` | Testing hypotheses, training classifiers, or rolling up discovery evidence from biological results. | Models and `metrics.tsv`, prediction validation, `comparative_axes_summary.tsv`, `discovery_summary.tsv`, and `report.md`. |
| `bio-fasta-database-curator` | Preparing sequence databases for BLAST, DIAMOND, MMseqs2, HMMER, pyhmmer, or custom reference searches. | Curated FASTA/FAA files, stable headers, deduplicated records, mapping tables, and database statistics. |
| `bio-foundation-housekeeping` | Defining metadata schemas or adding a queryable data catalog. | Generated LinkML/Pydantic models, cross-record validation, normalized Parquet tables, fixtures, and a DuckDB catalog. |

## Skills from other repositories

The pack no longer ships skills for manuscript prose, manuscript review, PDF conversion, or claim-graph extraction. Install these from the repositories that own them: `academic-writing` with `stop-slop` for prose, `nelli-paper-review` for review, `pdf-to-md` for PDF conversion, and `csag-extraction` for claim graphs. The agents name them in prose, and the router never recommends them.
