---
name: bio-gene-calling
description: Predict genes and count tRNA and rRNA genes in assemblies. Use when calling CDS in prokaryotic, viral, or eukaryotic assemblies, or when an ncRNA census is needed before annotation.
disable-model-invocation: true
---

# Bio Gene Calling

Call genes and annotate basic features for prokaryotes, viruses, and eukaryotes.

Shared pipeline rules: read `~/.agents/skills/omics-pipeline/SKILL.md` first (in a plugin install, `../omics-pipeline/SKILL.md` from this file).

## Instructions

Tool guides and versions: [docs/README.md](docs/README.md).

1. Validate the assembly and tool manifests, then generate a per-assembly execution plan:

   ```bash
   uv run --script ~/.agents/skills/bio-gene-calling/scripts/run_gene_calling.py \
     assemblies.tsv --tool-manifest tool-manifest.json \
     --out results/bio-gene-calling --threads 8
   # Inspect run_manifest.json, then execute or resume the same plan
   # (through the scheduler on HPC; match --threads to the allocated CPUs):
   uv run --script ~/.agents/skills/bio-gene-calling/scripts/run_gene_calling.py \
     assemblies.tsv --tool-manifest tool-manifest.json \
     --out results/bio-gene-calling --threads 8 --execute
   ```

   The tool manifest must pin the BRAKER4 repository commit, Snakefile checksum, container-lock checksum, and every Rfam model checksum. The driver records input FASTA checksums, routes each assembly by domain, writes idempotent BRAKER4 `samples.csv` and `config.ini` files, uses absolute covariance-model paths, and writes the default and relaxed ncRNA census rows. `--threads` (default 8) sets the thread count of every tool. Execution writes `<output>.done` for each declared output after its tool exits 0, and reuses a step only when every output is non-empty and has its marker, so a partial file from a killed job is rerun. A tRNAscan-SE run that exits 0 without a table counts as zero tRNAs and writes an empty `trnascan.tsv` with its marker; an empty table without that marker is rerun. Execution replaces pending ncRNA counts with parsed tRNAscan-SE and Infernal counts.
2. Select gene caller by organism class:
   - Bacteria and Archaea: **Pyrodigal**. Set `mode` to `single` for an isolate genome (training needs at least 20 kbp of sequence) or `metagenome` for MAGs, short contigs, and mixed input.
   - Viruses, including giant and alternative-code viruses: the **Prodigal-GV** model set in metagenomic mode. The driver runs **pyrodigal-gv**, which bundles the prodigal-gv 2.11.0 models. When results must match ViroSync or another pipeline that pins the standalone `prodigal-gv` 2.11.0 binary, use that binary with `-p meta` (ViroSync builds it with a node-capacity patch through `pixi run setup-prodigal-gv`) and record which implementation produced the calls.
   - Eukaryotes: **BRAKER4** as the current upstream workflow. Pin the tested repository commit, workflow checksum, and container lock in provenance. BRAKER4 is a Snakemake workflow; do not invoke the legacy `braker.pl` entry point for a BRAKER4 run. Keep BRAKER3 only for a documented legacy reproduction.
3. For eukaryotic or protist drafts with ONT cDNA or other transcriptome reads, build the transcript evidence bundle first: `~/.agents/skills/bio-reads-qc-mapping/references/ont-cdna-evidence.md` (it also holds the recovery steps and the `gene_calling_evidence.tsv` columns).
4. Run gene calling and produce per-assembly GFF/protein/CDS outputs. BRAKER4 emits compressed results under `output/{sample}/results/`; Pyrodigal and pyrodigal-gv emit the normalized uncompressed paths recorded in the run manifest.
5. Run tRNA and rRNA detection on every assembly and report counts per class. Zero hits at default and relaxed thresholds are required results; never leave ncRNA presence or absence unstated.
   - tRNA: tRNAscan-SE with the domain flag (`-B` bacteria, `-A` archaea, `-E` eukaryotes, `-G` viruses). Without a flag it uses eukaryotic models. Use ARAGORN when tmRNA is needed.
   - rRNA: Infernal `cmsearch` against the relevant Rfam covariance models. Pick the model set by domain of life:
     - Bacteria: RF00177 (SSU 16S), RF02541 (LSU 23S), RF00001 (5S).
     - Archaea: RF01959 (SSU 16S), RF02540 (LSU 23S), RF00001 (5S).
     - Eukaryotes: RF01960 (SSU 18S), RF02543 (LSU 28S), RF00002 (5.8S), RF00001 (5S).
     - Viruses: no domain-specific set. The census records an explicit "not screened" rRNA row; screen host-domain models when host contamination is suspected.
     The default run is `cmsearch --rfam --cut_ga --nohmmonly`. The relaxed run drops `--cut_ga` and counts only hits that pass the inclusion E-value (`!` in the tblout `inc` column). Record both results.
6. Summarize gene count, gene density, coding fraction, ORF length distribution, unusually long ORFs, overlapping genes, tRNAs, rRNAs, and other features that may affect downstream discovery.
7. Flag gene-calling anomalies relative to the inferred group and data type, including patterns that could hide interesting biology or indicate artifacts.
8. Keep `ncRNA_census.tsv` with columns: assembly, class (tRNA/rRNA/tmRNA/other), tool, model (Rfam accession when applicable), threshold (default/relaxed), count, notes. The driver writes it; add tmRNA or other ncRNA rows when you run those screens. The file is required even when all counts are zero.

## Input Requirements

Tools come from the project's pinned pixi environment (`docs/README.md`).

- `assemblies.tsv` with `assembly_id`, `domain`, `mode`, and `fasta`.
- `tool-manifest.json` with pinned caller versions; BRAKER4 commit, Snakefile, and container-lock checksums; and per-model Rfam checksums.
- Optional transcript evidence: the bundle from step 3 (ONT cDNA or long-read RNA FASTQ, RNA-Bloom transcript FASTA, splice-aware BAM/BAI, StringTie GTF and transcript FASTA, `gene_calling_evidence.tsv`).

## Output

Written by the driver:
- results/bio-gene-calling/run_manifest.json with tool pins, input checksums, per-assembly gene-model, protein, and CDS paths, and step status.
- results/bio-gene-calling/ncRNA_census.tsv
- Per-assembly tool outputs: `genes.gff3`, `proteins.faa`, `cds.fna`, `trnascan.tsv`, and `{model}.{threshold}.tbl` with the matching `.cmsearch.txt` log.
- BRAKER4 `samples.csv`, `config.ini`, and compressed `output/{sample}/results/braker.{gff3,aa,codingseq}.gz` paths for eukaryotic assemblies.

Written by the agent from those outputs:
- results/bio-gene-calling/gene_metrics.tsv
- results/bio-gene-calling/gene_calling_discovery_flags.tsv
- results/bio-gene-calling/gene_calling_evidence.tsv (agent-authored, when transcript evidence is used)
- results/bio-gene-calling/logs/

## Quality Gates

- [ ] Contigs are non-empty with a DNA alphabet, and start and stop codons of called genes are checked.
- [ ] Every assembly has its own output directory and input checksum in `run_manifest.json`; no caller output is silently shared across assemblies.
- [ ] A repeated planning run leaves identical BRAKER4 configuration unchanged, and `--execute` records every step as completed or reused.
- [ ] `--threads` equals the allocated CPUs for `--execute` and BRAKER4 runs.
- [ ] `ncRNA_census.tsv` exists and records the tRNAscan-SE count, default and relaxed results for every Rfam rRNA model, explicit zero counts, and the not-screened row for viruses.
- [ ] Gene metrics include discovery-relevant flags for unusual ORFs, gene density, coding fraction, and tRNA or rRNA features; specialized inputs use a literature or tool-supported mode, or the reason is documented.
- [ ] With transcript evidence, the mapping summaries show which draft genome is supported, and every evidence path is recorded in the bundle.
