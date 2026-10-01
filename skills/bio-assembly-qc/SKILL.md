---
name: bio-assembly-qc
description: Assemble isolate genomes or metagenomes and run QUAST/MetaQUAST with a restartable driver. Use when turning QC-passed reads into contigs and checking assembly contiguity.
---

# Bio Assembly QC

Assemble isolate genomes or metagenomes from QC-passed reads, normalize the assembler output to one `contigs.fasta` per sample, and run QUAST or MetaQUAST.

## Instructions

Tool guides and versions: [docs/README.md](docs/README.md).

1. Validate the assembly manifest and inspect a restartable execution plan before starting expensive work:

   ```bash
   uv run --script skills/bio-assembly-qc/scripts/run_assembly_qc.py \
     assemblies.tsv --out results/bio-assembly-qc --threads 4
   # Inspect run_manifest.json, then execute the same plan on a compute node:
   uv run --script skills/bio-assembly-qc/scripts/run_assembly_qc.py \
     assemblies.tsv --out results/bio-assembly-qc --threads 16 --execute
   ```

   The driver rejects samples whose upstream `read_qc_status` is not `passed`. It runs SPAdes (`--isolate`), metaSPAdes, Flye/metaFlye, or metaMDBG by mode, passes `--threads` to every tool (default 4; SPAdes otherwise uses 16), normalizes the assembler output to per-sample `contigs.fasta`, and chooses QUAST or MetaQUAST from the mode. It reuses a stage only when its declared outputs are non-empty and its `.done` marker exists. Run `--execute` through the scheduler (`sbatch`) for anything beyond the fixtures, not on a login node.
2. Select an assembler based on read type, genome/metagenome scope, and sample diversity:
   - Illumina short-read isolates and hybrid assemblies: SPAdes v4.0.0+ (v4.3.0 current). Use `metaSPAdes` for short-read metagenomes.
   - Long-read bacterial isolates (PacBio CLR, ONT): Flye v2.9.5+ for the draft assembly. Use Autocycler v0.6+ when a complete bacterial consensus genome is needed from several independent long-read assemblies; do not use it for mixed communities.
   - Long-read metagenomes: Flye v2.9.5+ in `--meta` mode (metaFlye) as the baseline for ONT and CLR communities.
   - HiFi metagenomes: metaMDBG v1.1+. In its benchmark it recovered up to twice as many circularized high-quality MAGs as metaFlye on HiFi data (see [docs/README.md](docs/README.md)). Keep metaFlye as a comparator when a per-sample failure is suspected.
   - Very large or diverse long-read datasets where runtime limits the work: myloasm, when its read profile matches the dataset.
   - The driver does not run Autocycler, hybrid SPAdes, or myloasm. Run those by hand and record the exact commands and versions.
3. Run assembly with resource-aware settings and record exact CLI, version, thread count, and RAM ceiling.
   - For very large ONT/metagenome FASTQs, use `/bio-reads-qc-mapping` guidance for filtering and avoid redundant full-file raw-read preflights before filtering. Record raw file metadata (`stat` path, size, mtime), optionally run a small sampled check, and write `seqkit stats` after each produced read set.
   - Use atomic output patterns for long-running filters and assemblies: write to `.tmp`, verify non-empty/readable output, then `mv` into the final path. Resume mode should skip existing final outputs only after sanity checks; when checks fail, use a tool-supported overwrite option or remove the corrupt final output before rerunning.
   - For Flye/metaFlye failures or interrupted jobs, prefer `--resume` or `--resume-from` in the existing output directory when the prior run is structurally intact. Do not delete a large partial assembly unless logs or missing stage files show it is corrupted.
4. Summarize the QUAST v5.3+ or MetaQUAST `report.tsv` per sample (contig count, total length, N50, largest contig) against project thresholds.
5. For every produced `contigs.fasta`, invoke `/tracking-taxonomy-updates` to run the BBTools-container QuickClade `percontig` domain screen before choosing downstream genome/MAG/viral/eukaryotic workflows.
6. Use the QuickClade domain routing table to decide the next step:
   - Bacteria/Archaea -> `/bio-gene-calling`, `/bio-annotation`, and GTDB-Tk taxonomy assignment.
   - Viral or virus-like -> `/bio-viromics` before prokaryotic MAG tooling.
   - Eukaryota -> eukaryote-aware gene/QC workflows and EukCC where bins or genomes are present.
   - Mixed/low-confidence -> split or flag contigs before domain-specific analysis.

## Input Requirements

Prerequisites:
- Tools declared in the project's pinned Pixi environment. See `docs/README.md` for expected tools.
- Sufficient disk and RAM for chosen assembler.
Inputs:
- reads/*.fastq.gz or reads/*.fastq (raw or filtered reads; verify actual compression by content when suffixes are suspect).
- `assemblies.tsv` with `sample_id`, `mode`, `read1`, `read2`, `read_qc_status`, and `read_platform`; supported core modes are `short_isolate`, `long_isolate`, `short_metagenome`, `long_metagenome`, and `hifi_metagenome`. `read_platform` is required for `long_isolate` and `long_metagenome`, and selects the Flye error model: `ont` gives `--nano-hq`, `pacbio-clr` gives `--pacbio-raw`, `pacbio-hifi` gives `--pacbio-hifi`. Leave it empty for short-read modes; `hifi_metagenome` accepts only `pacbio-hifi` or an empty value.

## Output

- results/bio-assembly-qc/run_manifest.json (validated rows, planned commands, and per-stage `status` after `--execute`)
- results/bio-assembly-qc/<sample_id>/assembler/ (raw assembler output)
- results/bio-assembly-qc/<sample_id>/contigs.fasta (normalized assembly)
- results/bio-assembly-qc/<sample_id>/quast/report.tsv (QUAST or MetaQUAST metrics)
- results/bio-assembly-qc/domain_routing.tsv (written by the `/tracking-taxonomy-updates` QuickClade step, not by the driver)
- stdout: the last line is one JSON envelope `{ok, skill, out, manifest, warnings}` (driver stdout contract in AGENTS.md)

## Quality Gates

- [ ] Assembly size range and N50 distribution meet project thresholds.
- [ ] Every assembler output is normalized to a non-empty per-sample `contigs.fasta` before QC or downstream routing.
- [ ] On execution failure, preserve logs and report the failed command; retry only after diagnosing the cause and recording the changed parameters. Report unmet biological thresholds as results; never tune parameters solely to pass a gate.
- [ ] Verify reads are present and readable. If `gzip -t` fails on a `.gz`-named file, inspect magic bytes or file type before labeling it corrupt; it may be plain FASTQ with the wrong suffix.
- [ ] Check available disk space before assembly.
- [ ] For large ONT/metagenome inputs, raw file metadata and post-filter `seqkit stats` are recorded without redundant full-file raw preflight scans.
- [ ] Long-running filter outputs use `.tmp` plus atomic rename, and resume guards require a stage `.done` marker before reusing non-empty outputs.
- [ ] Flye/metaFlye logs are inspected before deciding whether to resume, rerun, or clean a partial output directory.
- [ ] For Autocycler isolate consensus, record each input assembler/run and confirm the sample is not a mixed community.
- [ ] QuickClade `percontig` domain screen completed or the reason for skipping it is explicitly recorded.
- [ ] Domain routing table is reviewed before selecting MAG, viral, bacterial/archaeal, or eukaryotic downstream tools.

## Examples

Use `fixtures/assemblies.tsv` as the executable short-read, long-read, and metagenome planning fixture.

## Troubleshooting

**Issue**: Large ONT assembly workflow appears stalled before assembly
**Solution**: Check whether the script is doing a raw full-file preflight (`gzip -t`, raw `seqkit stats`) instead of productive filtering. For urgent routing/assembly, replace raw full scans with metadata plus sampled checks, then run filtering and post-filter stats.

**Issue**: Flye job timed out or was interrupted
**Solution**: Inspect `flye.log` and stage files. If the output directory is intact, resubmit with Flye resume options rather than restarting from scratch.
