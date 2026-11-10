---
name: bio-reads-qc-mapping
description: QC, trim, and map short or long reads with a restartable driver. Use when processing raw FASTQ, removing adapters or contaminants, or computing mapping and coverage statistics.
disable-model-invocation: true
---

# Bio Reads QC Mapping

Validate a read sample sheet, run read QC and trimming, and map reads to an optional reference with a restartable driver.

Shared pipeline rules: read `~/.agents/skills/omics-pipeline/SKILL.md` first (in a plugin install, `../omics-pipeline/SKILL.md` from this file).

## Instructions

Tool guides and versions: [docs/README.md](docs/README.md).

1. Validate `sample_sheet.tsv` against `schemas/sample-sheet.schema.json` and inspect the plan before running anything:

   ```bash
   uv run --script ~/.agents/skills/bio-reads-qc-mapping/scripts/run_reads_qc_mapping.py \
     sample_sheet.tsv --out results/bio-reads-qc-mapping --threads 4
   # Inspect run_manifest.json, then execute the same plan through the scheduler:
   uv run --script ~/.agents/skills/bio-reads-qc-mapping/scripts/run_reads_qc_mapping.py \
     sample_sheet.tsv --out results/bio-reads-qc-mapping --threads 16 --execute
   ```

   `read_type` must be `paired_short`, `single_short`, or `long`. Mapping runs only for rows with a non-empty `reference`; a missing reference is not a mapping failure. The driver reuses a stage only when its declared outputs are non-empty and the stage's `.done` marker exists, so a rerun with `--execute` skips completed QC stages.
2. Know what the driver runs, and adapt the plan when the defaults do not fit:
   - Short reads: `fastp` with default adapter and quality trimming. Use BBDuk (BBTools container) instead when you need k-mer contaminant, spike-in, or host removal ([docs/bbduk.md](docs/bbduk.md)).
   - Long reads: `filtlong` with no thresholds, which passes every read through. Add `--min_length`, `--keep_percent`, or `--target_bases` for the project ([docs/filtlong.md](docs/filtlong.md)).
   - Short-read mapping: `bwa-mem2 mem`. Build the index first with `bwa-mem2 index reference.fasta`; the driver does not, and `mem` fails at once on a new reference without it.
   - Long-read mapping: `minimap2 -ax map-ont`. For PacBio HiFi use `map-hifi`, and for PacBio CLR use `map-pb`.
   - The driver writes SAM. Sort and index it (`samtools sort`, `samtools index`), then compute per-reference coverage with `samtools coverage` or CoverM.
3. For long reads, use basecaller-aware QC first. For ONT, prefer Dorado trimming during basecalling or demultiplexing when starting from POD5 or BAM. For FASTQ-only input, use `chopper` for quality, length, and end trimming, or `filtlong` v0.3.1 when selecting reads for assembly (v0.3.0 renamed the long options to `--short_1` / `--short_2`). Use `Pychopper` for full-length cDNA. Use `Porechop_ABI` only as a documented fallback for adapter discovery, and record why. The large-ONT preflight rule is in the router.
   - `Pychopper` can write plain FASTQ even when the output path ends in `.gz`. Give its outputs plain `.fastq` names unless you compress them yourself, and check gzip magic bytes before running `gzip -t`. Rename mislabeled legacy outputs to `.fastq` before resuming.
   - `Pychopper` report plotting can fail after the reads are written. If the classified, unclassified, rescued, and read-stats outputs exist and are non-empty, resume downstream from them instead of rerunning `Pychopper`.
4. ONT cDNA or other transcriptome reads for eukaryotic gene calling: [references/ont-cdna-evidence.md](references/ont-cdna-evidence.md).
5. Optional GPU mapping (Parabricks `fq2bam`, and `minimap2` with the `lr:hq` preset): [references/gpu-mapping.md](references/gpu-mapping.md).

## Input Requirements

- BBTools runs from the `bryce911/bbtools` container; other tools come from the pinned pixi environment ([docs/README.md](docs/README.md)).
- `sample_sheet.tsv` with exactly the columns `sample_id`, `read_type`, `read1`, `read2`, `reference`; relative paths resolve against the sheet's directory. The fixture `fixtures/sample_sheet.tsv` covers paired-end, single-end and long reads, with mapping requested for two of three rows.
- Reads as `reads/*.fastq.gz` or `reads/*.fastq`; a `bwa-mem2` index next to each short-read reference.

## Output

- results/bio-reads-qc-mapping/run_manifest.json (validated rows, planned commands, and per-stage `status` after `--execute`)
- results/bio-reads-qc-mapping/<sample_id>/ with trimmed reads (`reads.fastq`, or `reads_R1.fastq` and `reads_R2.fastq`), `fastp.json`, `fastp.html`, `mapped.sam`, and the `qc.done` and `mapping.done` markers
- results/bio-reads-qc-mapping/mapping_stats.tsv (`mapping_status` is `planned` before `--execute`, then `completed` or `reused`, and `not_requested` for rows with no reference)
- Sample sheet contract: [schemas/sample-sheet.schema.json](schemas/sample-sheet.schema.json)

## Quality Gates

- [ ] The sample sheet validates, and the plan covers every row exactly once.
- [ ] Post-QC read counts are compared with the raw counts (`fastp.json` or `seqkit stats`).
- [ ] Mapping rate, for rows that supplied a reference only: record the cutoff chosen for this project, the observed rate and the outcome (pass or fail). A failure is reported, not tuned away.
- [ ] Long-read QC records where trimming happened: basecaller or demultiplexer, `chopper`, `filtlong`, `Pychopper`, or a documented Porechop_ABI fallback.
- [ ] Reused outputs pass a light content check (`seqkit stats`, FASTQ header sniff, or gzip magic) before downstream use.
