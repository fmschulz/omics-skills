---
name: bio-reads-qc-mapping
description: Ingest, quality-control, and map sequencing reads with reproducible outputs. Use when processing raw reads, removing contaminants, or calculating mapping and coverage statistics.
---

# Bio Reads QC Mapping

Ingest, QC, and map reads with reproducible outputs. Use for raw read processing and coverage stats.

## Instructions

1. Parse and validate `sample_sheet.tsv` against `schemas/sample-sheet.schema.json`. Use the executable driver for both planning and restartable execution:

   ```bash
   uv run --script skills/bio-reads-qc-mapping/scripts/run_reads_qc_mapping.py \
     sample_sheet.tsv --out results/bio-reads-qc-mapping
   # Inspect run_manifest.json, then execute the same plan:
   uv run --script skills/bio-reads-qc-mapping/scripts/run_reads_qc_mapping.py \
     sample_sheet.tsv --out results/bio-reads-qc-mapping --execute
   ```

   `read_type` must be `paired_short`, `single_short`, or `long`. Mapping runs only for rows with a non-empty `reference`; a missing reference is not a mapping failure. The driver reuses a stage only when its declared outputs are non-empty and the stage's `.done` marker exists.
2. For short reads: run QC and adapter/quality trimming with `bbduk` or `fastp` v1.3.3+.
3. For long reads: use current basecaller-aware QC first. For ONT, prefer Dorado summaries/trimming during basecalling or demultiplexing when starting from signal/BAM; for FASTQ-only filtering use `chopper` for quality/length/end trimming or `filtlong` v0.2.1 when selecting reads for assembly. Use `Pychopper` for full-length cDNA. Treat `Porechop_ABI` as a targeted legacy/fallback adapter-discovery tool, and record why it is needed.
   - For very large ONT FASTQ inputs, do not burn the first full read pass on raw `gzip -t` or raw `seqkit stats` preflight unless the user explicitly asks for it. Record raw `stat` metadata and, if needed, a small sampled sanity check; let the first full pass be the actual filtering/orientation step, then run `seqkit stats` on produced outputs.
   - For ONT cDNA with `Pychopper`, write outputs with plain `.fastq` suffixes unless you explicitly pipe/compress them yourself. `Pychopper` can write plain FASTQ even when the output path ends in `.gz`; avoid `gzip -t` on `Pychopper` outputs unless magic bytes confirm gzip. If legacy outputs have `.fastq.gz` names but plain FASTQ content, rename them to `.fastq` before resuming.
   - `Pychopper` report plotting can fail after the reads are already processed, for example from a pandas/statistics type-conversion error. On that failure, inspect whether the classified/unclassified/rescued/read-stats outputs exist and are non-empty. If they do, resume downstream from those outputs rather than rerunning the full `Pychopper` pass.
4. Map reads and produce coverage tables:
   - Short reads, CPU: `bbmap` or `bwa-mem2` v2.2.1+. Short reads, GPU node available: NVIDIA Parabricks `fq2bam` (wraps `bwa-mem2` + GATK markdup; typically 3–4× faster than `bwa-mem2` on 8 cores and up to ~80× over a 96-core CPU pipeline).
   - Long reads, CPU: `minimap2` v2.30+. AVX-512 hardware: `mm2-fast` as a drop-in replacement (~1.8× speedup). GPU node available: `mm2-gb` or `mm2-ax` for CUDA-accelerated long-read alignment.
5. Record the tool, version, and any GPU device used in the run log.

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
- Sample sheet and reads are available.
Inputs:
- sample_sheet.tsv
- reads/*.fastq.gz
- reference.fasta (optional)

## Output

- results/bio-reads-qc-mapping/trimmed_reads/
- results/bio-reads-qc-mapping/qc_reports/
- results/bio-reads-qc-mapping/mapping_stats.tsv
- results/bio-reads-qc-mapping/coverage.tsv
- results/bio-reads-qc-mapping/logs/

## Quality Gates

- [ ] Post-QC read count sanity checks pass.
- [ ] Mapping rate meets project thresholds.
- [ ] On failure: retry with alternative parameters; if still failing, record in report and exit non-zero.
- [ ] Validate sample sheet schema and FASTQ integrity.
- [ ] The plan covers every sheet row exactly once, and mapping gates are applied only to rows that supplied a reference.
- [ ] For long-read QC, record whether trimming happened in the basecaller/demultiplexer, `chopper`, `filtlong`, `Pychopper`, or a documented Porechop_ABI fallback.
- [ ] For huge ONT inputs, avoid redundant full-file raw preflights; document raw file size/mtime and make the first full pass productive.
- [ ] For `Pychopper` outputs, verify actual file type by content, not suffix. Plain FASTQ with a `.gz` suffix must be renamed or explicitly compressed before downstream tools that expect gzip.
- [ ] Resume guards skip a stage only when its expected outputs are non-empty and its `.done` marker exists. Run a lightweight content check (`seqkit stats`, FASTQ header sniff, or gzip magic as appropriate) before accepting downstream data.

## Examples

### Example 1: Expected input layout

```text
sample_sheet.tsv
reads/*.fastq.gz
reference.fasta (optional)
```

The runnable fixture at `fixtures/sample_sheet.tsv` covers paired-end, single-end, and long reads.

## Troubleshooting

**Issue**: Missing inputs or reference databases
**Solution**: Verify paths and permissions before running the workflow.

**Issue**: Low-quality results or failed QC gates
**Solution**: Review reports, adjust parameters, and re-run the affected step.

**Issue**: `Pychopper` failed during report/stat plotting but output FASTQs exist
**Solution**: Treat this as a recoverable post-processing failure. Confirm the classified FASTQ is non-empty and readable, fix any misleading `.gz` suffix, run `seqkit stats`, and resume downstream steps from the existing `Pychopper` outputs.
