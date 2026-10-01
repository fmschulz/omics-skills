---
name: bio-reads-qc-mapping
description: QC, trim, and map short or long reads with a restartable driver. Use when processing raw FASTQ, removing adapters or contaminants, or computing mapping and coverage statistics.
---

# Bio Reads QC Mapping

Validate a read sample sheet, run read QC and trimming, and map reads to an optional reference with a restartable driver.

## Instructions

Tool guides and versions: [docs/README.md](docs/README.md).

1. Validate `sample_sheet.tsv` against `schemas/sample-sheet.schema.json` and inspect the plan before running anything:

   ```bash
   uv run --script skills/bio-reads-qc-mapping/scripts/run_reads_qc_mapping.py \
     sample_sheet.tsv --out results/bio-reads-qc-mapping --threads 4
   # Inspect run_manifest.json, then execute the same plan on a compute node:
   uv run --script skills/bio-reads-qc-mapping/scripts/run_reads_qc_mapping.py \
     sample_sheet.tsv --out results/bio-reads-qc-mapping --threads 16 --execute
   ```

   `read_type` must be `paired_short`, `single_short`, or `long`. Mapping runs only for rows with a non-empty `reference`; a missing reference is not a mapping failure. The driver reuses a stage only when its declared outputs are non-empty and the stage's `.done` marker exists. Run `--execute` through the scheduler (`sbatch`) for real data, not on a login node.
2. Know what the driver runs, and adapt the plan when the defaults do not fit:
   - Short reads: `fastp` v1.3.3+ with default adapter and quality trimming. Use BBDuk (BBTools container) instead when you need k-mer contaminant, spike-in, or host removal ([docs/bbduk.md](docs/bbduk.md)).
   - Long reads: `filtlong` with no thresholds, which passes every read through. Add `--min_length`, `--keep_percent`, or `--target_bases` for the project ([docs/filtlong.md](docs/filtlong.md)).
   - Short-read mapping: `bwa-mem2 mem`. Build the index first with `bwa-mem2 index reference.fasta`; the driver does not.
   - Long-read mapping: `minimap2 -ax map-ont`. For PacBio HiFi use `map-hifi`, and for PacBio CLR use `map-pb`.
   - The driver writes SAM. Sort and index it (`samtools sort`, `samtools index`), then compute per-reference coverage with `samtools coverage` or CoverM.
3. For long reads, use basecaller-aware QC first. For ONT, prefer Dorado trimming during basecalling or demultiplexing when starting from POD5 or BAM. For FASTQ-only input, use `chopper` for quality, length, and end trimming, or `filtlong` v0.3.1 when selecting reads for assembly (v0.3.0 renamed the long options to `--short_1` / `--short_2`). Use `Pychopper` for full-length cDNA. Use `Porechop_ABI` only as a documented fallback for adapter discovery, and record why.
   - For very large ONT FASTQ inputs, do not spend the first full read pass on `gzip -t` or raw `seqkit stats` unless asked. Record raw `stat` metadata, optionally check a small sample, make the first full pass the filtering step, then run `seqkit stats` on the outputs.
   - `Pychopper` can write plain FASTQ even when the output path ends in `.gz`. Give its outputs plain `.fastq` names unless you compress them yourself, and check gzip magic bytes before running `gzip -t`. Rename mislabeled legacy outputs to `.fastq` before resuming.
   - `Pychopper` report plotting can fail after the reads are written. If the classified, unclassified, rescued, and read-stats outputs exist and are non-empty, resume downstream from them instead of rerunning `Pychopper`.
4. Faster mappers, when hardware allows:
   - Short reads on a GPU node: NVIDIA Parabricks `fq2bam` (GPU BWA-MEM with sorting and duplicate marking).
   - Long reads on a GPU node: Parabricks `minimap2` (presets `map-ont`, `map-hifi`, `lr:hq`).
   - The CPU and GPU forks `mm2-fast` and `mm2-gb` are built on minimap2 v2.24, not current v2.30+. Use them only when the older base version is acceptable.
5. Record each tool, version, thread count, and any GPU device in the run log and `tasks/METHODS.md`.

## Input Requirements

Prerequisites:
- Tools declared in the project's pinned pixi environment; BBTools runs from the `bryce911/bbtools` container. See [docs/README.md](docs/README.md).
- A `bwa-mem2` index next to each short-read reference.
Inputs:
- `sample_sheet.tsv` with exactly the columns `sample_id`, `read_type`, `read1`, `read2`, `reference`; relative paths resolve against the sheet's directory.
- reads/*.fastq.gz or reads/*.fastq
- reference.fasta (optional)

## Output

- results/bio-reads-qc-mapping/run_manifest.json (validated rows, planned commands, and per-stage `status` after `--execute`)
- results/bio-reads-qc-mapping/<sample_id>/ with trimmed reads (`reads.fastq`, or `reads_R1.fastq` and `reads_R2.fastq`), `fastp.json`, `fastp.html`, `mapped.sam`, and the `qc.done` and `mapping.done` markers
- results/bio-reads-qc-mapping/mapping_stats.tsv (`mapping_status` is `planned` before `--execute`, then `completed` or `reused`, and `not_requested` for rows with no reference)
- stdout: the last line is one JSON envelope `{ok, skill, out, manifest, warnings}` (driver stdout contract in AGENTS.md)
- Sample sheet contract: [schemas/sample-sheet.schema.json](schemas/sample-sheet.schema.json)

## Quality Gates

- [ ] The sample sheet validates, and the plan covers every row exactly once.
- [ ] Post-QC read counts are plausible against the raw counts (`fastp.json` or `seqkit stats`).
- [ ] Mapping rate meets project thresholds, applied only to rows that supplied a reference.
- [ ] On execution failure, preserve logs and report the failed command; retry only after diagnosing the cause and recording the changed parameters. Report unmet biological thresholds as results; never tune parameters solely to pass a gate.
- [ ] Long-read QC records where trimming happened: basecaller or demultiplexer, `chopper`, `filtlong`, `Pychopper`, or a documented Porechop_ABI fallback.
- [ ] Huge ONT inputs have raw size and mtime recorded and no redundant full-file raw preflight.
- [ ] File type is checked by content, not suffix, before tools that expect gzip.
- [ ] Before accepting reused outputs downstream, run a light content check (`seqkit stats`, FASTQ header sniff, or gzip magic).

## Examples

The runnable fixture at `fixtures/sample_sheet.tsv` covers paired-end, single-end, and long reads, with mapping requested for two of the three rows.

## Troubleshooting

**Issue**: `Pychopper` failed during report or stat plotting but output FASTQs exist
**Solution**: Treat it as a recoverable post-processing failure. Confirm the classified FASTQ is non-empty and readable, fix any misleading `.gz` suffix, run `seqkit stats`, and resume downstream from the existing `Pychopper` outputs.

**Issue**: `bwa-mem2 mem` fails immediately on a new reference
**Solution**: The index is missing. Run `bwa-mem2 index reference.fasta` once, then rerun with `--execute`; completed QC stages are reused.
