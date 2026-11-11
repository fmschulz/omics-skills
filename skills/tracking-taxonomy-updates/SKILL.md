---
name: tracking-taxonomy-updates
description: Route genomes, bins, or contigs to domain classifiers with QuickClade, and track NCBI, GTDB, ICTV, and eukaryotic taxonomy releases. Use when assigning taxonomy, choosing a domain-specific tool, comparing releases, or resolving renamed taxa.
disable-model-invocation: true
---

# Tracking Taxonomy Updates

Two separate jobs. Domain routing is the first gate for the omics stage skills. Release tracking reports taxonomy changes and shares no steps with routing.

Shared pipeline rules: read `~/.agents/skills/omics-pipeline/SKILL.md` first (in a plugin install, `../omics-pipeline/SKILL.md` from this file).

`SKILL_DIR` is the directory that contains this `SKILL.md`, for example `~/.agents/skills/tracking-taxonomy-updates`.

## Instructions

### Job 1: Domain routing (QuickClade, then a domain classifier)

1. Run QuickClade first on any assembly, MAG, SAG, isolate genome, bin set, or contig FASTA, through the BBTools container with `percontig` ([reference/tools.md](reference/tools.md)). Skip it only when the user supplies a trusted domain label and asks to skip triage. QuickClade routes; it is not the final authority.
2. Convert the QuickClade machine output into the one routing table, `results/taxonomy/domain_routing.tsv`:

   ```bash
   uv run --script "$SKILL_DIR/scripts/quickclade_to_routing.py" \
     results/taxonomy/quickclade_percontig.tsv \
     --sample-id S1 --output results/taxonomy/domain_routing.tsv
   ```

3. Route each row:
   - Bacteria or Archaea: GTDB-Tk. If the reference package is missing, install it under the project or shared database root, set `GTDBTK_DATA_PATH`, record the release, and pass `gtdbtk check_install` before classifying.
   - Phage or prokaryotic virus: `bio-viromics`, then vConTACT3.
   - Giant virus or Nucleocytoviricota: `bio-viromics`, then GVClass plus a marker-gene phylogeny.
   - Eukaryota: EukCC.
   - Mixed, low-confidence, or conflicting domains: split or flag the contigs for manual review before any domain-specific tool.
4. Submit GTDB-Tk, EukCC, vConTACT3, and GVClass through the scheduler (`hpc-slurm`), from the project root:

   ```bash
   cd PROJECT_ROOT && SLURM_ACCOUNT=<account> "$SKILL_DIR/scripts/submit_taxonomy.sh" gtdbtk bins results/taxonomy/gtdbtk
   ```

   The wrapper submits with `--chdir=$PROJECT_ROOT`; `PROJECT_ROOT` defaults to the current directory and is never derived from the script path. The template [templates/taxonomy-tool.sbatch](templates/taxonomy-tool.sbatch) requests 16 CPUs, 64 GB, and 24 h, and passes `$SLURM_CPUS_PER_TASK` as the thread count to every tool. It needs `GTDBTK_DATA_PATH`, `EUKCC2_DB`, or `VCONTACT3_DB` for the matching tool; set `GTDBTK_EXTENSION` (GTDB-Tk, without the dot) or `EUKCC_SUFFIX` (EukCC, with the dot, such as `.fna`) when genome files do not end in `.fa`; both tools skip files with another ending. sbatch reads `SBATCH_CLUSTERS`, `SBATCH_PARTITION`, and `SBATCH_QOS` from the environment; set them as `hpc-slurm` says.
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
- Tools come from the project's pinned pixi environment; record its lockfile.

## Output

- Domain routing:
  - `results/taxonomy/quickclade_percontig.tsv` (agent-authored path, written by QuickClade)
  - `results/taxonomy/domain_routing.tsv` (agent-authored path, written by `quickclade_to_routing.py`) with columns `sample_id`, `query_id`, `contig_id`, `quickclade_domain`, `quickclade_taxonomy`, `quickclade_confidence`, `route`, `downstream_tool`, `review_flag`, `notes`
  - tool outputs under `results/taxonomy/{gtdbtk,eukcc,vcontact3,gvclass}/`
  - a standardized assignment table joined on stable identifiers
- Release tracking: a versioned taxonomy update summary and a cross-source conflict report.

## Quality Gates

- [ ] Routing: QuickClade ran first, per contig, and its table chose the downstream tools.
- [ ] Bacterial and archaeal routes report GTDB-Tk output and the GTDB release, or report the missing database as a blocker.
- [ ] Viral routes separate prokaryotic viruses (vConTACT3) from giant-virus candidates (GVClass).
- [ ] Eukaryotic routes use EukCC, not prokaryotic QC or taxonomy tools.
- [ ] Classifier outputs are non-empty, with explicit thread counts.
- [ ] Provenance lists tool versions, database releases, container tag and digest, and run dates.
- [ ] Release tracking: every "latest" claim names the authority, version, and date; joins use stable identifiers (NCBI taxids, GTDB genome IDs), not names.
- [ ] Items in [reference/qa-checklist.md](reference/qa-checklist.md) pass.
