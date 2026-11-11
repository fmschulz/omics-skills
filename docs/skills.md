# Skills

One row per skill. Each skill's `SKILL.md` is the authoritative description: its frontmatter gives the name and trigger, and its body gives instructions, inputs, outputs and quality gates. The sources are under [`skills/`](https://github.com/fmschulz/omics-skills/tree/main/skills).

Two kinds of skill exist. A **model-visible** skill is listed in every session, and the model loads it when its description fits the task. A **pipeline stage** skill is hidden (`disable-model-invocation: true` in Claude Code, `allow_implicit_invocation: false` for Codex), so its description costs no prompt space. The model reaches a stage skill through `omics-pipeline`. A person can still call one by name, such as `/bio-annotation`.

## Model-visible skills

| Skill | Use when | Main result |
|---|---|---|
| `omics-pipeline` | A genome, metagenome, or viral analysis needs a stage page, a driver, or the shared pipeline rules. | The shared rules (domain routing first, hypothesis register, five comparative axes, discovery and reporting, environment, scheduler), the stage pages below, and the stage skills to read. |
| `bioinformatics-project` | Starting, reorganizing, or reproducibility-hardening a bioinformatics project. | Project layout, pinned environment, task records, hypothesis register, restartable drivers, provenance, and sharing metadata. |
| `public-db-lookup` | Fetching a record from UniProt, NCBI, MGnify, InterPro, AlphaFold DB, STRING, or ENA. | A compact JSON envelope with bounded records, counts, and an optional raw-response file. |
| `bio-logic` | Auditing scientific reasoning, study design, bias, or strength of evidence behind project results. | A hypothesis register and a structured critique with uncertainty, alternative explanations, and follow-up checks. |
| `polars-dovmed` | Searching PMC Open Access or bioRxiv full text, through the connector or the hosted API or parquet script. | A run directory with `query.json`, raw responses, and timings, plus a paper list with relevance notes. |
| `crossref-lookup` | Validating DOIs, matching titles to citation metadata, or comparing papers by citations. | Crossref records, DOI matches, bibliography cleanup evidence, OpenAlex citation counts, and a journal impact factor from a small manual table. |
| `notebooks` | Building or converting reproducible marimo or Jupyter notebooks. | A fully executed notebook with embedded figures and clear analysis flow. |
| `beautiful-data-viz` | Making, restyling, or reviewing any plot, chart, figure, dashboard, or data visual. | Greyscale-first PNG, SVG, PDF, or HTML figures, color only to encode information, reproducible plotting code, and a Plotly Dash guide with an example app. |

## Pipeline stage pages

A stage without scripts of its own is one decision page in [`skills/omics-pipeline/references/`](https://github.com/fmschulz/omics-skills/tree/main/skills/omics-pipeline/references). A page gives the default tool per case, the rules a model would not guess, command lines, the QC gates to record, and the outputs. The model runs the tools; a project writes its own restartable driver as `bioinformatics-project` describes.

| Page | Use when |
|---|---|
| `reads-qc-mapping.md` | Raw FASTQ, adapters, contaminants, mapping and coverage. |
| `assembly.md` | QC-passed reads to isolate or metagenome contigs, with QUAST or MetaQUAST. |
| `binning.md` | Binning contigs and scoring completeness, contamination and chimerism of MAGs. |
| `gene-calling.md` | CDS prediction for prokaryotes, viruses and eukaryotes, and the tRNA and rRNA census. |
| `phylogenomics.md` | Marker alignments, ML trees, support values and closest relatives. |
| `structure.md` | Fold or complex prediction and structure search when sequence hits are weak. |

Tool notes sit beside the pages for tools that models know poorly: QuickBin, Autocycler, pyrodigal-gv, Infernal with its Rfam models, Boltz and TM-Vec.

## Pipeline stage skills

Read these through `omics-pipeline`. Projects call their scripts by path, so the names and script paths stay stable.

| Skill | Use when | Main result |
|---|---|---|
| `tracking-taxonomy-updates` | Routing sequences by domain with QuickClade before any domain-specific stage, comparing NCBI, GTDB, ICTV, or eukaryotic taxonomy releases, or assigning taxonomy. | `results/taxonomy/domain_routing.tsv`, GTDB-Tk, EukCC, vConTACT3, or GVClass assignments, and a versioned release change and conflict report. |
| `bio-annotation` | Assigning function and taxonomy from sequence homology. | Annotation and taxonomy Parquet tables, `marker_census.tsv`, a family copy-number matrix, and `discovery_candidates.tsv`. |
| `bio-viromics` | Detecting, classifying, and QCing viral contigs. | Viral calls, quality summaries, taxonomy evidence, and candidate discovery tables. |
| `bio-interdomain-hgt` | Testing interdomain horizontal gene transfer and donor direction. | Homology, context, contamination, and per-gene phylogenetic evidence for candidate transfers. |

## Skills from other repositories

The pack ships no skills for manuscript prose, manuscript review, proposal review, evaluation of AI-scientist output, PDF conversion, or claim-graph extraction. Install these from the repositories that own them, for example `academic-writing` with `stop-slop` for prose, `nelli-paper-review` for review, `pdf-to-md` for PDF conversion, and `csag-extraction` for claim graphs.
