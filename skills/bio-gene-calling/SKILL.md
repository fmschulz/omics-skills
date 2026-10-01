---
name: bio-gene-calling
description: Predict genes and count tRNA and rRNA genes in assemblies. Use when calling CDS in prokaryotic, viral, or eukaryotic assemblies, or when an ncRNA census is needed before annotation.
---

# Bio Gene Calling

Call genes and annotate basic features for prokaryotes, viruses, and eukaryotes.

## Instructions

Tool guides and versions: [docs/README.md](docs/README.md).

1. Validate the assembly and tool manifests, then generate a per-assembly execution plan:

   ```bash
   uv run --script skills/bio-gene-calling/scripts/run_gene_calling.py \
     assemblies.tsv --tool-manifest tool-manifest.json \
     --out results/bio-gene-calling --threads 8
   # Inspect run_manifest.json, then execute or resume the same plan
   # (inside an sbatch job on HPC; match --threads to --cpus-per-task):
   uv run --script skills/bio-gene-calling/scripts/run_gene_calling.py \
     assemblies.tsv --tool-manifest tool-manifest.json \
     --out results/bio-gene-calling --threads 8 --execute
   ```

   The tool manifest must pin the BRAKER4 repository commit, Snakefile checksum, container-lock checksum, and every Rfam model checksum. The driver records input FASTA checksums, routes each assembly by domain, writes idempotent BRAKER4 `samples.csv` and `config.ini` files, uses absolute covariance-model paths, and writes the default and relaxed ncRNA census rows. `--threads` (default 8) sets the thread count of every tool. Execution reuses non-empty declared outputs. A tRNAscan-SE run that exits 0 without a table counts as zero tRNAs and writes `trnascan.tsv.done`; an empty table without that marker is rerun. Execution replaces pending ncRNA counts with parsed tRNAscan-SE and Infernal counts.
2. Select gene caller by organism class:
   - Bacteria and Archaea: **Pyrodigal** v3.7+. Set `mode` to `single` for an isolate genome (training needs at least 20 kbp of sequence) or `metagenome` for MAGs, short contigs, and mixed input.
   - Viruses, including giant and alternative-code viruses: the **Prodigal-GV** model set in metagenomic mode. The driver runs **pyrodigal-gv** v0.3+, which bundles the prodigal-gv 2.11.0 models. When results must match ViroSync or another pipeline that pins the standalone `prodigal-gv` 2.11.0 binary, use that pinned binary with `-p meta` and record which implementation produced the calls. ViroSync builds prodigal-gv 2.11.0 with a node-capacity patch through `pixi run setup-prodigal-gv`.
   - Eukaryotes: **BRAKER4** as the current upstream workflow. Pin the tested repository commit, workflow checksum, and container lock in provenance. BRAKER4 is a Snakemake workflow; do not invoke the legacy `braker.pl` entry point for a BRAKER4 run. Keep BRAKER3 only for a documented legacy reproduction.
3. For eukaryotic/protist drafts with ONT cDNA or other transcriptome reads, build a transcript evidence bundle before gene calling:
   - Orient/filter full-length ONT cDNA reads with the `Pychopper` guidance in `/bio-reads-qc-mapping`, including plain `.fastq` output handling and resume from existing classified reads after report-plotting failures.
   - Map transcript reads splice-aware to each candidate draft genome with minimap2 (`-ax splice` family settings appropriate to the organism/data), sort/index BAMs, and compute a per-genome mapped fraction table.
   - Use the best-supported draft genome as the primary evidence target, but keep the full mapping table because it documents sample/genome assignment and cross-sample ambiguity.
   - Produce StringTie long-read GTF/transcript FASTA and, when useful, a reference-free transcript assembly such as RNA-Bloom. Summarize these paths in a `gene_calling_evidence.tsv` bundle with columns: sample_id, evidence_type, genome_id, path, notes. The bundle should be directly usable by BRAKER4 or another eukaryote-aware caller.
4. Run gene calling and produce per-assembly GFF/protein/CDS outputs. BRAKER4 emits compressed results under `output/{sample}/results/`; Pyrodigal and pyrodigal-gv emit the normalized uncompressed paths recorded in the run manifest.
5. Run tRNA and rRNA detection on every assembly and report counts per class. Zero hits at default and relaxed thresholds are required results; never leave ncRNA presence or absence unstated.
   - tRNA: tRNAscan-SE v2.0.12+ with the domain flag (`-B` bacteria, `-A` archaea, `-E` eukaryotes, `-G` viruses). Without a flag it uses eukaryotic models. Use ARAGORN v1.2.41+ when tmRNA is needed.
   - rRNA: Infernal v1.1.5+ `cmsearch` against the relevant Rfam covariance models. Pick the model set by domain of life:
     - Bacteria: RF00177 (SSU 16S), RF02541 (LSU 23S), RF00001 (5S).
     - Archaea: RF01959 (SSU 16S), RF02540 (LSU 23S), RF00001 (5S).
     - Eukaryotes: RF01960 (SSU 18S), RF02543 (LSU 28S), RF00002 (5.8S), RF00001 (5S).
     - Metazoan mitochondria, when applicable: RF02555 (12S), RF02546 (16S).
     - Viruses: no domain-specific set. The census records an explicit "not screened" rRNA row; screen host-domain models when host contamination is suspected.
     The default run is `cmsearch --rfam --cut_ga --nohmmonly`. The relaxed run drops `--cut_ga` and counts only hits that pass the inclusion E-value (`!` in the tblout `inc` column). Record both results.
6. For viral or otherwise specialized genomes, choose the gene caller and mode from tool documentation and the literature-derived analysis playbook for the inferred group; record the rationale.
7. Summarize gene count, gene density, coding fraction, ORF length distribution, unusually long ORFs, overlapping genes, tRNAs, rRNAs, and other features that may affect downstream discovery.
8. Flag gene-calling anomalies relative to the inferred group and data type, including patterns that could hide interesting biology or indicate artifacts.
9. Keep `ncRNA_census.tsv` with columns: assembly, class (tRNA/rRNA/tmRNA/other), tool, model (Rfam accession when applicable), threshold (default/relaxed), count, notes. The driver writes it; add tmRNA or other ncRNA rows when you run those screens. The file is required even when all counts are zero.

## Input Requirements

Prerequisites:
- Tools declared in the project's pinned Pixi environment. See `docs/README.md` for expected tools.
- Input contigs or bins are available.
Inputs:
- `assemblies.tsv` with `assembly_id`, `domain`, `mode`, and `fasta`.
- `tool-manifest.json` with pinned caller versions; BRAKER4 commit, Snakefile, and container-lock checksums; and per-model Rfam checksums.
- Optional transcript evidence: ONT cDNA/long-read RNA FASTQ, RNA-Bloom transcript FASTA, splice-aware BAM/BAI, StringTie GTF/transcript FASTA, and `gene_calling_evidence.tsv`.

## Output

Written by the driver:
- results/bio-gene-calling/run_manifest.json with tool pins, input checksums, per-assembly gene-model, protein, and CDS paths, and step status.
- results/bio-gene-calling/ncRNA_census.tsv
- Per-assembly tool outputs: `genes.gff3`, `proteins.faa`, `cds.fna`, `trnascan.tsv`, and `{model}.{threshold}.tbl` with the matching `.cmsearch.txt` log.
- BRAKER4 `samples.csv`, `config.ini`, and compressed `output/{sample}/results/braker.{gff3,aa,codingseq}.gz` paths for eukaryotic assemblies.

Written by the agent from those outputs:
- results/bio-gene-calling/gene_metrics.tsv
- results/bio-gene-calling/gene_calling_discovery_flags.tsv
- results/bio-gene-calling/gene_calling_evidence.tsv (when transcript evidence is used)
- results/bio-gene-calling/logs/
- stdout: the last line is one JSON envelope `{ok, skill, out, manifest, warnings}` (driver stdout contract in AGENTS.md)

## Quality Gates

- [ ] Gene count sanity checks pass.
- [ ] Start/stop codon checks pass.
- [ ] On execution failure, preserve logs and report the failed command; retry only after diagnosing the cause and recording the changed parameters. Report unmet biological thresholds as results; never tune parameters solely to pass a gate.
- [ ] Verify contigs are non-empty and DNA alphabet.
- [ ] `--execute` and BRAKER4 runs go through `sbatch` on HPC, with `--threads` equal to the allocated CPUs.
- [ ] Verify outputs contain expected feature types.
- [ ] Every assembly has its own output directory and input checksum in `run_manifest.json`; no caller output is silently shared across assemblies.
- [ ] A repeated planning run leaves identical BRAKER4 configuration unchanged, and `--execute` records every step as completed or reused.
- [ ] Specialized inputs use a literature/tool-supported gene-calling mode or document why not.
- [ ] Gene metrics include discovery-relevant flags for unusual ORFs, gene density, coding fraction, and tRNA/RNA features.
- [ ] `ncRNA_census.tsv` exists and records the tRNAscan-SE count, default and relaxed results for every Rfam rRNA model, explicit zero counts, and the not-screened row for viruses.
- [ ] For eukaryotic/protist transcript evidence, mapping summaries show which draft genome is supported and whether competing drafts have negligible, ambiguous, or substantial mapping.
- [ ] Transcript evidence paths are recorded in a bundle with enough detail for BRAKER4 or another caller to consume them reproducibly.

## Troubleshooting

**Issue**: ONT cDNA evidence workflow failed after `Pychopper` but classified reads exist
**Solution**: Follow `/bio-reads-qc-mapping` recovery guidance: verify/rename plain FASTQ outputs, run lightweight stats, resume mapping/StringTie/RNA-Bloom, and keep the failure plus resume command in the methods record.
