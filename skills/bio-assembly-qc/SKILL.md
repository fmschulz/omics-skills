---
name: bio-assembly-qc
description: Assemble genomes/metagenomes and produce assembly QC artifacts.
---

# Bio Assembly QC

Assemble genomes/metagenomes and produce assembly QC artifacts.

## Instructions

1. Select an assembler based on read type, genome/metagenome scope, and sample diversity:
   - Illumina short-read isolates and hybrid assemblies: SPAdes v4.0.0+ (final feature release; bug-fix-only series continues). Use `metaSPAdes` for short-read metagenomes.
   - Long-read isolates (PacBio CLR, ONT): Flye v2.9.5+.
   - Long-read metagenomes: Flye v2.9.5+ in `--meta` mode (metaFlye) as the baseline.
   - HiFi metagenomes: prefer **metaMDBG v1.1** (~2× more circularized high-quality MAGs vs metaFlye on HiFi, better virus/plasmid recovery; *Nature Biotechnology* 2024, DOI: 10.1038/s41587-023-01983-6). Keep metaFlye as a comparator when a per-sample failure mode is suspected.
   - Diverse or very large long-read datasets where speed dominates: **myloasm** (2025) as a faster long-read metagenome assembler when its profile matches the dataset; document the choice in the run log.
2. Run assembly with resource-aware settings and record exact CLI, version, thread count, and RAM ceiling.
3. Run QUAST v5.3+ (use MetaQUAST for metagenomes) and summarize metrics.

## Quick Reference

| Task | Action |
|------|--------|
| Run workflow | Follow the steps in this skill and capture outputs. |
| Validate inputs | Confirm required inputs and reference data exist. |
| Review outputs | Inspect reports and QC gates before proceeding. |
| Tool docs | See `docs/README.md`. |

## Input Requirements

Prerequisites:
- Tools available in the active environment (Pixi/conda/system). See `docs/README.md` for expected tools.
- Sufficient disk and RAM for chosen assembler.
Inputs:
- reads/*.fastq.gz (raw reads).
- assembler choice (spades | flye | metamdbg | myloasm).

## Output

- results/bio-assembly-qc/contigs.fasta
- results/bio-assembly-qc/assembly_metrics.tsv
- results/bio-assembly-qc/qc_report.html
- results/bio-assembly-qc/logs/

## Quality Gates

- [ ] Assembly size range and N50 distribution meet project thresholds.
- [ ] On failure: retry with alternative parameters; if still failing, record in report and exit non-zero.
- [ ] Verify reads are present and gzip-readable.
- [ ] Check available disk space before assembly.

## Examples

### Example 1: Expected input layout

```text
reads/*.fastq.gz (raw reads).
assembler choice (spades | flye).
```

## Troubleshooting

**Issue**: Missing inputs or reference databases
**Solution**: Verify paths and permissions before running the workflow.

**Issue**: Low-quality results or failed QC gates
**Solution**: Review reports, adjust parameters, and re-run the affected step.