---
name: tracking-taxonomy-updates
description: Track NCBI, GTDB, ICTV, and eukaryotic taxonomy releases, and route genomes, bins, or contigs to domain classifiers. Use when comparing releases, resolving renamed taxa, or assigning taxonomy.
---

# Tracking Taxonomy Updates

Report taxonomy changes from authoritative sources with explicit versions, dates, and provenance, and assign taxonomy to sequences through a QuickClade domain screen followed by a domain-specific classifier.

`SKILL_DIR` is the directory that contains this `SKILL.md`, for example `~/.agents/skills/tracking-taxonomy-updates`.

## Instructions

### Release and name changes

1. Fix the scope: domains, timeframe, and output type.
2. Pull release notes and current releases from the sources in [reference/sources.md](reference/sources.md). The snapshots in [reference/last-verified-snapshots.md](reference/last-verified-snapshots.md) are examples; re-check the sources for any "latest" claim.
3. Extract versioned changes and their impact, using stable identifiers from [reference/ranks-and-identifiers.md](reference/ranks-and-identifiers.md).
4. Deliver a versioned report from [reference/report-template.md](reference/report-template.md) with conflicts flagged.

### Taxonomy assignment

1. Run QuickClade first on any assembly, MAG, SAG, isolate genome, bin set, or contig FASTA, through the BBTools container with `percontig` ([reference/tools.md](reference/tools.md)). Skip it only when the user supplies a trusted domain label and asks to skip triage. QuickClade routes; it is not the final authority.
2. Convert the QuickClade machine output into `domain_routing.tsv`:

   ```bash
   uv run --script "$SKILL_DIR/scripts/quickclade_to_routing.py" \
     results/taxonomy/quickclade_percontig.tsv \
     --sample-id S1 --output results/taxonomy/domain_routing.tsv
   ```

3. Route each row:
   - Bacteria or Archaea: GTDB-Tk. If the reference package is missing, install it under the project or shared database root, set `GTDBTK_DATA_PATH`, record the release, and pass `gtdbtk check_install` before classifying.
   - Phage or prokaryotic virus: `/bio-viromics`, then vConTACT3.
   - Giant virus or Nucleocytoviricota: `/bio-viromics`, then GVClass plus a marker-gene phylogeny.
   - Eukaryota: EukCC.
   - Mixed, low-confidence, or conflicting domains: split or flag the contigs for manual review before any domain-specific tool.
4. Submit GTDB-Tk, EukCC, vConTACT3, and GVClass through the scheduler, never on a login node:

   ```bash
   SLURM_ACCOUNT=<account> "$SKILL_DIR/scripts/submit_taxonomy.sh" gtdbtk bins results/taxonomy/gtdbtk
   ```

   The template [templates/taxonomy-tool.sbatch](templates/taxonomy-tool.sbatch) requests 16 CPUs, 64 GB, and 24 h, and passes `$SLURM_CPUS_PER_TASK` as the thread count to every tool. It needs `GTDBTK_DATA_PATH`, `EUKCC2_DB`, or `VCONTACT3_DB` for the matching tool; set `GTDBTK_EXTENSION` when genome files do not end in `.fa`. sbatch reads `SBATCH_CLUSTERS`, `SBATCH_PARTITION`, and `SBATCH_QOS` from the environment. On Dori, export `SBATCH_CLUSTERS=perceus-00`, `SBATCH_PARTITION=dori`, `SBATCH_QOS=jgi_normal`, and `SLURM_ACCOUNT=grp-org-sc-mgs`, and qualify `squeue`/`sacct` with `-M perceus-00`.
5. Normalize identifiers and taxonomy strings across tools, and flag disagreements between QuickClade, the classifier, and NCBI.

Use the project's pinned Pixi environment for every tool and record its lockfile.

## Input Requirements

- For release tracking: domains, timeframe, and the source systems to compare (NCBI, GTDB, ICTV, eukaryotic frameworks).
- For assignment: genome, bin, or contig FASTA files, a QuickClade reference spectra file (`QUICKCLADE_REF`), the downstream databases, and a Slurm account.

## Output

- Versioned taxonomy update summary and a cross-source conflict report.
- For assignment workflows:
  - `results/taxonomy/quickclade_percontig.tsv` (agent-authored path, written by QuickClade)
  - `results/taxonomy/domain_routing.tsv` (agent-authored path, written by `quickclade_to_routing.py`) with columns `sample_id`, `query_id`, `contig_id`, `quickclade_domain`, `quickclade_taxonomy`, `quickclade_confidence`, `route`, `downstream_tool`, `review_flag`, `notes`
  - tool outputs under `results/taxonomy/{gtdbtk,eukcc,vcontact3,gvclass}/`
  - a standardized assignment table joined on stable identifiers

## Quality Gates

- [ ] Every "latest" claim names the authority, version, and date.
- [ ] Joins use stable identifiers (NCBI taxids, GTDB genome IDs), not names.
- [ ] Provenance lists tool versions, database releases, container tag and digest, and run dates.
- [ ] QuickClade ran first, per contig, and its routing table chose the downstream tools.
- [ ] Bacterial and archaeal routes report GTDB-Tk output and the GTDB release, or report the missing database as a blocker.
- [ ] Viral routes separate prokaryotic viruses (vConTACT3) from giant-virus candidates (GVClass).
- [ ] Eukaryotic routes use EukCC, not prokaryotic QC or taxonomy tools.
- [ ] Classifiers ran through the scheduler with explicit thread counts, and outputs were checked as non-empty.
- [ ] Items in [reference/qa-checklist.md](reference/qa-checklist.md) pass.

## Examples

```text
Domains: Bacteria + Archaea
Timeframe: last 12 months
Output: summary table + pipeline impact notes
```

## Troubleshooting

**Issue**: Sources disagree on a taxon.
**Solution**: Report both assignments with conflict flags and provenance.

**Issue**: Stable identifiers are missing.
**Solution**: Resolve names with TaxonKit and report merged or deleted taxid warnings.

**Issue**: vConTACT3 exits with "No database path provided (--db-path)".
**Solution**: Run `vcontact3 prepare_databases --get-version latest --set-location DIR` and export `VCONTACT3_DB=DIR` before submitting.
