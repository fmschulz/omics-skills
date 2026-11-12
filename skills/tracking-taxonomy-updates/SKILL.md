---
name: tracking-taxonomy-updates
description: Route genomes, bins, or contigs to domain classifiers with QuickClade, and track NCBI, GTDB, ICTV, and eukaryotic taxonomy releases. Use when assigning taxonomy, choosing a domain-specific tool, comparing releases, or resolving renamed taxa.
disable-model-invocation: true
---

# Tracking Taxonomy Updates

Two separate jobs. Domain routing is the first gate for the omics stage skills. Release tracking reports taxonomy changes and shares no steps with routing.

Shared pipeline rules: read `~/.agents/skills/omics-pipeline/SKILL.md` first (in a plugin install, `../omics-pipeline/SKILL.md` from this file).

`SKILL_DIR` is the directory that contains this `SKILL.md`, for example `~/.agents/skills/tracking-taxonomy-updates`. `RUN_DIR` is the run directory that `bioinformatics-project` defines (`results/<date>_<name>/`); stage outputs go to `$RUN_DIR/taxonomy/`. Only the routing table has a fixed path, `results/taxonomy/domain_routing.tsv`.

## Instructions

### Job 1: Domain routing (QuickClade, then a domain classifier)

1. Run QuickClade first on any assembly, MAG, SAG, isolate genome, bin set, or contig FASTA, through the BBTools container with `percontig` ([reference/tools.md](reference/tools.md)). Skip it only when the user supplies a trusted domain label and asks to skip triage. QuickClade routes; it is not the final authority.
2. Convert the QuickClade machine output into the one routing table, `results/taxonomy/domain_routing.tsv`:

   ```bash
   uv run --script "$SKILL_DIR/scripts/quickclade_to_routing.py" \
     "$RUN_DIR/taxonomy/quickclade_percontig.tsv" \
     --sample-id S1 --output results/taxonomy/domain_routing.tsv
   ```

   - The converter reads the real `format=machine` columns (`#QueryName`, `Q_Contigs`, `lineage`, `Confidence`) and keeps the first row of each query, the best of the five hits QuickClade prints. It stops when a query spans more than one contig (the run lacked `percontig`).
   - The domain is the `sk__` rank of the lineage (`Bacteria`, `Archaea`, `Eukaryota`, `Viruses`), or `Nucleocytoviricota` for the giant-virus phylum.
   - `quickclade_confidence` is the domain-level value of the `Confidence` column (`d:`, 0 to 100). `--min-confidence` (default 90) sets the limit: a row below it gets `low_confidence` `true`, route `manual_review`, no downstream tool and `review_flag` `true`.
   - The table refuses to overwrite. Add a second sample with `--append` and another `--sample-id`; a repeated sample and contig pair, or a table whose header is not exactly the columns below, stops the run and leaves the table unchanged. A lock file beside the table serialises concurrent runs. A `d:` value or `--min-confidence` outside a finite 0 to 100 is an input error.
   - `fixtures/quickclade-machine.tsv` is unedited output of the `bryce911/bbtools:39.85` container; the test file records the command.

3. Route each row:
   - Bacteria or Archaea: GTDB-Tk. If the reference package is missing, install it under the project or shared database root, set `GTDBTK_DATA_PATH`, record the release, and pass `gtdbtk check_install` before classifying.
   - Phage or prokaryotic virus: `bio-viromics`, then vConTACT3.
   - Giant virus or Nucleocytoviricota: `bio-viromics`, then GVClass plus a marker-gene phylogeny.
   - Eukaryota: EukCC.
   - Mixed, low-confidence (`low_confidence` `true`), or conflicting domains: split or flag the contigs for manual review before any domain-specific tool.
4. Submit GTDB-Tk, EukCC, vConTACT3, and GVClass through the scheduler (`hpc-slurm`), from the project root:

   ```bash
   cd PROJECT_ROOT && SLURM_ACCOUNT=<account> "$SKILL_DIR/scripts/submit_taxonomy.sh" gtdbtk bins "$RUN_DIR/taxonomy/gtdbtk"
   ```

   The wrapper submits with `--chdir=$PROJECT_ROOT`; `PROJECT_ROOT` defaults to the current directory and is never derived from the script path. The template [templates/taxonomy-tool.sbatch](templates/taxonomy-tool.sbatch) requests 16 CPUs, 64 GB, and 24 h, runs every tool with `pixi run --frozen` in the project's pixi environment (the project root holds `pixi.toml` and `pixi.lock`), writes the Slurm logs to `logs/taxonomy-<jobid>.out` and `.err` in the project root (the wrapper creates `logs/`), and passes `$SLURM_CPUS_PER_TASK` as the thread count to every tool. It needs `GTDBTK_DATA_PATH`, `EUKCC2_DB`, or `VCONTACT3_DB` for the matching tool; set `GTDBTK_EXTENSION` (GTDB-Tk, without the dot) or `EUKCC_SUFFIX` (EukCC, with the dot, such as `.fna`) when genome files do not end in `.fa`; both tools skip files with another ending. sbatch reads `SBATCH_CLUSTERS`, `SBATCH_PARTITION`, and `SBATCH_QOS` from the environment; set them as `hpc-slurm` says.
   - vConTACT3 exits with "No database path provided (--db-path)" when `VCONTACT3_DB` is unset: run `vcontact3 prepare_databases --get-version latest --set-location DIR` and export `VCONTACT3_DB=DIR` before submitting.
5. Normalize identifiers and taxonomy strings across tools, and flag disagreements between QuickClade, the classifier, and NCBI.

### Job 2: Taxonomy release tracking

1. Fix the scope: domains, timeframe, and output type.
2. Pull release notes and current releases from the sources in [reference/sources.md](reference/sources.md). The snapshots in [reference/last-verified-snapshots.md](reference/last-verified-snapshots.md) are examples; re-check the sources for any "latest" claim.
3. Extract versioned changes and their impact, using stable identifiers from [reference/ranks-and-identifiers.md](reference/ranks-and-identifiers.md). When identifiers are missing, resolve names with TaxonKit and report merged or deleted taxid warnings.
4. Deliver a versioned report from [reference/report-template.md](reference/report-template.md). When sources disagree on a taxon, report both assignments with conflict flags and provenance.

## Input Requirements

- Domain routing: genome, bin, or contig FASTA files; a QuickClade reference spectra file (`QUICKCLADE_REF`); the downstream databases; a Slurm account.
- Release tracking: domains, timeframe, and the source systems to compare (NCBI, GTDB, ICTV, eukaryotic frameworks).
- Tools come from the project's pinned pixi environment, which the batch jobs enter through `pixi run --frozen`; record its lockfile.

## Output

- Domain routing:
  - `$RUN_DIR/taxonomy/quickclade_percontig.tsv` (agent-authored path, written by QuickClade), under the run directory that `bioinformatics-project` defines (`results/<date>_<name>/<stage>/`, stage `taxonomy`)
  - `results/taxonomy/domain_routing.tsv` (agent-authored path, fixed and shared, written by `quickclade_to_routing.py`) with columns `sample_id`, `query_id`, `contig_id`, `quickclade_domain`, `quickclade_taxonomy`, `quickclade_confidence`, `low_confidence`, `route`, `downstream_tool`, `review_flag`, `notes`
  - tool outputs under `$RUN_DIR/taxonomy/{gtdbtk,eukcc,vcontact3,gvclass}/`
  - a standardized assignment table joined on stable identifiers
- Release tracking: a versioned taxonomy update summary and a cross-source conflict report.

## Quality Gates

- [ ] Routing: QuickClade ran first, per contig, and its table chose the downstream tools; rows with `low_confidence` `true` went to manual review.
- [ ] Bacterial and archaeal routes report GTDB-Tk output and the GTDB release, or report the missing database as a blocker.
- [ ] Viral routes separate prokaryotic viruses (vConTACT3) from giant-virus candidates (GVClass).
- [ ] Eukaryotic routes use EukCC, not prokaryotic QC or taxonomy tools.
- [ ] Classifier outputs are non-empty, with explicit thread counts.
- [ ] Provenance lists tool versions, database releases, container tag and digest, and run dates.
- [ ] Release tracking: every "latest" claim names the authority, version, and date; joins use stable identifiers (NCBI taxids, GTDB genome IDs), not names.
- [ ] Items in [reference/qa-checklist.md](reference/qa-checklist.md) pass.
