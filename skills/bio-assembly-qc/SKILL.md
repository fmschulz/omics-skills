---
name: bio-assembly-qc
description: Assemble genomes or metagenomes and assess assembly quality. Use when turning sequence reads into contigs and reporting completeness, continuity, and contamination evidence.
---

# Bio Assembly QC

Assemble genomes/metagenomes and produce assembly QC artifacts.

## Instructions

1. Validate the assembly manifest and inspect a restartable execution plan before starting expensive work:

   ```bash
   uv run --script skills/bio-assembly-qc/scripts/run_assembly_qc.py \
     assemblies.tsv --out results/bio-assembly-qc
   uv run --script skills/bio-assembly-qc/scripts/run_assembly_qc.py \
     assemblies.tsv --out results/bio-assembly-qc --execute
   ```

   The driver rejects samples whose upstream `read_qc_status` is not `passed`. It normalizes assembler outputs to per-sample `contigs.fasta` and chooses QUAST or MetaQUAST from the declared mode. It reuses a stage only when its declared outputs are non-empty and its `.done` marker exists.
2. Select an assembler based on read type, genome/metagenome scope, and sample diversity:
   - Illumina short-read isolates and hybrid assemblies: SPAdes v4.0.0+ (final feature release; bug-fix-only series continues). Use `metaSPAdes` for short-read metagenomes.
   - Long-read bacterial isolates (PacBio CLR, ONT): Flye v2.9.5+ for the draft/baseline assembly. Use Autocycler v0.6+ when a complete, high-confidence bacterial consensus genome is needed from multiple independent long-read assembly attempts; do not use it for mixed-community metagenomes.
   - Long-read metagenomes: Flye v2.9.5+ in `--meta` mode (metaFlye) as the baseline for ONT/CLR mixed-community assemblies.
   - HiFi metagenomes: prefer **metaMDBG v1.1** (~2× more circularized high-quality MAGs vs metaFlye on HiFi, better virus/plasmid recovery; *Nature Biotechnology* 2024, DOI: 10.1038/s41587-023-01983-6). Keep metaFlye as a comparator when a per-sample failure mode is suspected.
   - Diverse or very large long-read datasets where speed dominates: **myloasm** (2025) as a faster long-read metagenome assembler when its profile matches the dataset; document the choice in the run log.
3. Run assembly with resource-aware settings and record exact CLI, version, thread count, and RAM ceiling.
   - For very large ONT/metagenome FASTQs, use `/bio-reads-qc-mapping` guidance for filtering and avoid redundant full-file raw-read preflights before filtering. Record raw file metadata (`stat` path, size, mtime), optionally run a small sampled check, and write `seqkit stats` after each produced read set.
   - Use atomic output patterns for long-running filters and assemblies: write to `.tmp`, verify non-empty/readable output, then `mv` into the final path. Resume mode should skip existing final outputs only after sanity checks; when checks fail, use a tool-supported overwrite option or remove the corrupt final output before rerunning.
   - For Flye/metaFlye failures or interrupted jobs, prefer `--resume` or `--resume-from` in the existing output directory when the prior run is structurally intact. Do not delete a large partial assembly unless logs or missing stage files show it is corrupted.
4. Run QUAST v5.3+ (use MetaQUAST for metagenomes) and summarize metrics.
5. For every produced `contigs.fasta`, invoke `/tracking-taxonomy-updates` to run the BBTools-container QuickClade `percontig` domain screen before choosing downstream genome/MAG/viral/eukaryotic workflows.
6. Use the QuickClade domain routing table to decide the next step:
   - Bacteria/Archaea -> `/bio-gene-calling`, `/bio-annotation`, and GTDB-Tk taxonomy assignment.
   - Viral or virus-like -> `/bio-viromics` before prokaryotic MAG tooling.
   - Eukaryota -> eukaryote-aware gene/QC workflows and EukCC where bins or genomes are present.
   - Mixed/low-confidence -> split or flag contigs before domain-specific analysis.

## Quick Reference

| Task | Action |
|------|--------|
| Run workflow | Follow the steps in this skill and capture outputs. |
| Validate inputs | Confirm required inputs and reference data exist. |
| Review outputs | Inspect reports and QC gates before proceeding. |
| Tool docs | See `docs/README.md`. |

## Input Requirements

Prerequisites:
- Tools declared in the project's pinned Pixi environment. See `docs/README.md` for expected tools.
- Sufficient disk and RAM for chosen assembler.
Inputs:
- reads/*.fastq.gz or reads/*.fastq (raw or filtered reads; verify actual compression by content when suffixes are suspect).
- `assemblies.tsv` with `sample_id`, `mode`, `read1`, `read2`, and `read_qc_status`; supported core modes are `short_isolate`, `long_isolate`, `short_metagenome`, `long_metagenome`, and `hifi_metagenome`.

## Output

- results/bio-assembly-qc/contigs.fasta
- results/bio-assembly-qc/assembly_metrics.tsv
- results/bio-assembly-qc/domain_routing.tsv
- results/bio-assembly-qc/qc_report.html
- results/bio-assembly-qc/logs/

## Quality Gates

- [ ] Assembly size range and N50 distribution meet project thresholds.
- [ ] Every assembler output is normalized to a non-empty per-sample `contigs.fasta` before QC or downstream routing.
- [ ] On failure: retry with alternative parameters; if still failing, record in report and exit non-zero.
- [ ] Verify reads are present and readable. If `gzip -t` fails on a `.gz`-named file, inspect magic bytes or file type before labeling it corrupt; it may be plain FASTQ with the wrong suffix.
- [ ] Check available disk space before assembly.
- [ ] For large ONT/metagenome inputs, raw file metadata and post-filter `seqkit stats` are recorded without redundant full-file raw preflight scans.
- [ ] Long-running filter outputs use `.tmp` plus atomic rename, and resume guards require a stage `.done` marker before reusing non-empty outputs.
- [ ] Flye/metaFlye logs are inspected before deciding whether to resume, rerun, or clean a partial output directory.
- [ ] For Autocycler isolate consensus, record each input assembler/run and confirm the sample is not a mixed community.
- [ ] QuickClade `percontig` domain screen completed or the reason for skipping it is explicitly recorded.
- [ ] Domain routing table is reviewed before selecting MAG, viral, bacterial/archaeal, or eukaryotic downstream tools.

## Examples

### Example 1: Expected input layout

```text
reads/*.fastq.gz (raw reads).
assembler choice (spades | flye).
```

Use `fixtures/assemblies.tsv` as the executable short-read, long-read, and metagenome planning fixture.

## Troubleshooting

**Issue**: Missing inputs or reference databases
**Solution**: Verify paths and permissions before running the workflow.

**Issue**: Low-quality results or failed QC gates
**Solution**: Review reports, adjust parameters, and re-run the affected step.

**Issue**: Large ONT assembly workflow appears stalled before assembly
**Solution**: Check whether the script is doing a raw full-file preflight (`gzip -t`, raw `seqkit stats`) instead of productive filtering. For urgent routing/assembly, replace raw full scans with metadata plus sampled checks, then run filtering and post-filter stats.

**Issue**: Flye job timed out or was interrupted
**Solution**: Inspect `flye.log` and stage files. If the output directory is intact, resubmit with Flye resume options rather than restarting from scratch.
