---
name: bio-assembly-qc
description: Assemble isolate genomes or metagenomes and run QUAST/MetaQUAST with a restartable driver. Use when turning QC-passed reads into contigs and checking assembly contiguity.
disable-model-invocation: true
---

# Bio Assembly QC

Assemble isolate genomes or metagenomes from QC-passed reads, normalize the assembler output to one `contigs.fasta` per sample, and run QUAST or MetaQUAST.

Shared pipeline rules: read `~/.agents/skills/omics-pipeline/SKILL.md` first (in a plugin install, `../omics-pipeline/SKILL.md` from this file).

## Instructions

Tool guides and versions: [docs/README.md](docs/README.md).

1. Validate the assembly manifest and inspect a restartable execution plan before starting expensive work:

   ```bash
   uv run --script ~/.agents/skills/bio-assembly-qc/scripts/run_assembly_qc.py \
     assemblies.tsv --out results/bio-assembly-qc --threads 4
   # Inspect run_manifest.json, then execute the same plan through the scheduler:
   uv run --script ~/.agents/skills/bio-assembly-qc/scripts/run_assembly_qc.py \
     assemblies.tsv --out results/bio-assembly-qc --threads 16 --execute
   ```

   The driver rejects samples whose upstream `read_qc_status` is not `passed`. It runs SPAdes (`--isolate`), metaSPAdes, Flye/metaFlye, or metaMDBG by mode, passes `--threads` to every tool (default 4; SPAdes otherwise uses 16), normalizes the assembler output to per-sample `contigs.fasta`, and chooses QUAST or MetaQUAST from the mode. It reuses a stage only when its declared outputs are non-empty and its `.done` marker exists.
2. Select an assembler based on read type, genome or metagenome scope, and sample diversity:
   - Illumina short-read isolates and hybrid assemblies: SPAdes. Use `metaSPAdes` for short-read metagenomes.
   - Long-read bacterial isolates (PacBio CLR, ONT): Flye for the draft assembly. Use Autocycler when a complete bacterial consensus genome is needed from several independent long-read assemblies; do not use it for mixed communities.
   - Long-read metagenomes: Flye in `--meta` mode (metaFlye) as the baseline for ONT and CLR communities.
   - HiFi metagenomes: metaMDBG. In its benchmark it recovered up to twice as many circularized high-quality MAGs as metaFlye on HiFi data (see [docs/README.md](docs/README.md)). Keep metaFlye as a comparator when a per-sample failure is suspected.
   - Very large or diverse long-read datasets where runtime limits the work: myloasm, when its read profile matches the dataset.
   - The driver does not run Autocycler, hybrid SPAdes, or myloasm. Run those by hand and record the exact commands and versions.
3. Record the exact CLI, version, thread count, and RAM ceiling of each run. For very large ONT or metagenome FASTQs, filter first and follow the large-ONT rule in the router.
   - Write long-running filter and assembly outputs to `.tmp`, verify them, then `mv`. Resume skips an existing final output only after sanity checks; when they fail, use a tool-supported overwrite option or remove the corrupt output before rerunning.
   - After a Flye or metaFlye failure or interruption, inspect `flye.log` and the stage files first. When the output directory is structurally intact, resume with `--resume` or `--resume-from` in that directory. Delete a large partial assembly only when the logs or missing stage files show corruption.
4. Summarize the QUAST or MetaQUAST `report.tsv` per sample (contig count, total length, N50, largest contig) against project thresholds.
5. Run the router's domain routing on every `contigs.fasta` before choosing downstream genome, MAG, viral or eukaryotic workflows, and review the table first.

## Input Requirements

- Tools from the project's pinned pixi environment ([docs/README.md](docs/README.md)); enough disk and RAM for the chosen assembler.
- Reads as `reads/*.fastq.gz` or `reads/*.fastq` (raw or filtered).
- `assemblies.tsv` with `sample_id`, `mode`, `read1`, `read2`, `read_qc_status`, and `read_platform`; supported modes are `short_isolate`, `long_isolate`, `short_metagenome`, `long_metagenome`, and `hifi_metagenome`. `read_platform` is required for `long_isolate` and `long_metagenome`, and selects the Flye error model: `ont` gives `--nano-hq`, `pacbio-clr` gives `--pacbio-raw`, `pacbio-hifi` gives `--pacbio-hifi`. Leave it empty for short-read modes; `hifi_metagenome` accepts only `pacbio-hifi` or an empty value. `fixtures/assemblies.tsv` is the planning fixture for all modes.

## Output

- results/bio-assembly-qc/run_manifest.json (validated rows, planned commands, and per-stage `status` after `--execute`)
- results/bio-assembly-qc/<sample_id>/assembler/ (raw assembler output)
- results/bio-assembly-qc/<sample_id>/contigs.fasta (normalized assembly)
- results/bio-assembly-qc/<sample_id>/quast/report.tsv (QUAST or MetaQUAST metrics)

## Quality Gates

- [ ] Every assembler output is normalized to a non-empty per-sample `contigs.fasta` before QC or routing.
- [ ] Free disk space is checked before assembly.
- [ ] Assembly size range and N50 are reported per sample against the project thresholds.
- [ ] Resume guards require the stage `.done` marker before reusing a non-empty output.
- [ ] Flye or metaFlye logs are inspected before a resume, rerun or clean.
- [ ] For an Autocycler consensus, each input assembler run is recorded and the sample is confirmed not to be a mixed community.
