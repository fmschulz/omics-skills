# Gene calling and ncRNA census

**Last verified:** 2026-11-11
**Tool version/release checked:** Pyrodigal v3.7.1; pyrodigal-gv v0.3.2 (prodigal-gv 2.11.0 models); BRAKER4 v0.6.0-beta (upstream README of 2026-11-11, workflow not run); legacy BRAKER v3.0.8; Infernal v1.1.5; tRNAscan-SE v2.0.13; Tiberius (preprint, not run)
**Official docs/manual:** https://pyrodigal.readthedocs.io/en/stable/ ; https://github.com/althonos/pyrodigal-gv#readme ; https://github.com/Gaius-Augustus/BRAKER4 ; http://eddylab.org/infernal/Userguide.pdf ; http://lowelab.ucsc.edu/tRNAscan-SE/
**Release/source:** https://github.com/althonos/pyrodigal/releases/tag/v3.7.1 ; https://github.com/althonos/pyrodigal-gv/releases/tag/v0.3.2 ; https://github.com/Gaius-Augustus/BRAKER/releases/tag/v3.0.8 ; https://github.com/Gaius-Augustus/BRAKER4/releases/tag/v0.6.0-beta ; https://github.com/EddyRivasLab/infernal ; https://github.com/UCSC-LoweLab/tRNAscan-SE/releases/tag/v2.0.13

Read the shared rules in [../SKILL.md](../SKILL.md) first. They cover domain routing, hypotheses, failures, environment, threads and the scheduler.

## Use when

Call CDS in prokaryotic, viral or eukaryotic assemblies, and count tRNA and rRNA genes before annotation. Inputs: one FASTA per assembly, its domain (`bacteria`, `archaea`, `virus`, `eukaryota`) from the routing table, and for prokaryotes the mode (`single` for an isolate, `metagenome` for MAGs, short contigs or mixed input). Eukaryotes may add transcript evidence.

## Tool choice

| Case | Default | Alternative |
| --- | --- | --- |
| Bacteria, archaea | Pyrodigal | none |
| Viruses, including giant and alternative-code viruses | pyrodigal-gv, metagenomic mode ([pyrodigal-gv.md](pyrodigal-gv.md)) | Standalone `prodigal-gv` 2.11.0 with `-p meta`, when results must match a pipeline that pins it (ViroSync) |
| Eukaryotes | BRAKER4 (Snakemake workflow) | BRAKER3 only for a documented legacy reproduction; Tiberius as a GPU alternative (rule below) |
| tRNA | tRNAscan-SE with the domain flag | ARAGORN when tmRNA is needed |
| rRNA | Infernal `cmsearch` with Rfam models ([infernal.md](infernal.md)) | none; barrnap is retired |

Rfam models by domain:

| Domain | SSU | LSU | 5S | 5.8S |
| --- | --- | --- | --- | --- |
| Bacteria | RF00177 | RF02541 | RF00001 | none |
| Archaea | RF01959 | RF02540 | RF00001 | none |
| Eukaryotes | RF01960 | RF02543 | RF00001 | RF00002 |
| Viruses | no set | no set | no set | no set |

## Rules a model would not guess

- Pyrodigal `single` mode needs at least 20 kbp of sequence to train. Use `meta` otherwise.
- Pyrodigal `single` mode assumes translation table 11 unless you pass `-g`. On a *Mycoplasmoides genitalium* assembly (table 4) it called 995 proteins, against 527 with `-g 4`. Pass `-g` for a known non-standard code. `meta` mode picked table 4 for the long contigs of the same assembly.
- pyrodigal-gv uses its viral models only in metagenomic mode. Record which implementation made the calls: pyrodigal-gv or the standalone binary.
- BRAKER4 is a Snakemake workflow. Do not call the legacy `braker.pl` for a BRAKER4 run. Pin the repository commit, the Snakefile checksum and the container-lock checksum.
- BRAKER4 reads `samples.csv` with columns `sample_name`, `genome`, `genome_masked`, `protein_fasta`, `bam_files`, `fastq_r1`, `fastq_r2`, `sra_ids`, `varus_genus`, `varus_species`, `isoseq_bam`, `isoseq_fastq`, `busco_lineage`, `reference_gtf`. `sample_name`, `genome` and `busco_lineage` (for example `eukaryota_odb12`) are required in v0.6.0-beta; a row with only those three is a genome-only (ES) run. The legacy guide ranks genome-only (ES) lowest in accuracy. Fill the evidence columns when evidence exists.
- BRAKER4 binds only `/home` into its containers in the upstream example. Add `--singularity-args "-B <dir>"` when the genome or evidence files sit elsewhere.
- Tiberius, a deep-learning ab initio gene finder that needs no extrinsic evidence, has lineage models for Mesangiospermae, Fungi, Vertebrata, Insecta, Chlorophyta and Bacillariophyta. In its authors' preprint it approaches BRAKER3 accuracy in Mesangiospermae, Fungi, Bacillariophyta and Chlorophyta and runs about 80 times faster on a GPU (Gabriel et al. (2026) *bioRxiv* https://doi.org/10.64898/2026.04.24.720536). It is a preprint and not independently benchmarked: BRAKER4 stays the default.
- Set `run_ncrna = 0` in the BRAKER4 `config.ini`. The ncRNA census comes from tRNAscan-SE and Infernal.
- For eukaryotic or protist drafts with ONT cDNA or other transcript reads, build the transcript evidence bundle first (the ONT cDNA rule in [reads-qc-mapping.md](reads-qc-mapping.md)). Record every evidence path.
- tRNAscan-SE uses eukaryotic models when you give no flag. Always pass the domain flag: `-B`, `-A`, `-E`, or `-G` (general model, used for viruses because they carry host-derived tRNA genes).
- tRNAscan-SE `-H` is the score breakdown. Pseudogene checking is on by default and `-D` turns it off. `--thread` defaults to all threads, so set it.
- A tRNAscan-SE run that exits 0, prints `No tRNAs found.` and leaves a 0-byte output file (no header) counts as zero tRNAs. A failed run with an empty table is not a zero count: rerun it.
- `cmsearch` runs once per model and per threshold. The default run uses `--cut_ga`. The relaxed run drops it, and you count only hits with `!` in the tblout `inc` column (hits marked `?` are not counted). Record both.
- Viruses have no domain-specific rRNA set. Write an explicit "not screened" row. Screen host-domain models only if host contamination is suspected.
- An expected marker or RNA class that is absent is a result. Zero hits at default and relaxed thresholds is a required result, never silence.
- A killed job can leave a non-empty partial table. Treat an output as finished only after the tool exited 0.

## Commands

The Pyrodigal, pyrodigal-gv, tRNAscan-SE and `cmsearch` lines ran on 2026-11-11 on a *M. genitalium* assembly and phage lambda. The BRAKER4 block follows the upstream README and was not run.

```bash
# Bacteria, archaea: MODE is single or meta
pyrodigal -i $CONTIGS -o $OUT/genes.gff3 -a $OUT/proteins.faa -d $OUT/cds.fna \
  -f gff -p $MODE -j $THREADS

# Viruses
pyrodigal-gv -i $CONTIGS -o $OUT/genes.gff3 -a $OUT/proteins.faa -d $OUT/cds.fna \
  -f gff -p meta -j $THREADS

# Eukaryotes: $WORK holds samples.csv and config.ini
snakemake --snakefile $BRAKER4_SNAKEFILE --directory $WORK --cores $THREADS \
  --use-singularity --singularity-prefix $WORK/.singularity_cache \
  --latency-wait 120 --restart-times 3
# config.ini:
#   [paths]
#   samples_file = $WORK/samples.csv
#   augustus_config_path = $WORK/augustus_config
#   [parameters]
#   run_ncrna = 0

# tRNA: FLAG is -B, -A, -E or -G
tRNAscan-SE $FLAG -Q --thread $THREADS -o $OUT/trnascan.tsv $CONTIGS

# rRNA: once per Rfam model, default then relaxed. CM is the absolute path of the
# model file, MODEL its name without directory and suffix (RF00177).
# One model: curl -L https://rfam.org/family/RF00177/cm -o RF00177.cm
MODEL=$(basename "$CM" .cm)
cmsearch --rfam --nohmmonly --cpu $THREADS --cut_ga \
  -o $OUT/$MODEL.default.cmsearch.txt --tblout $OUT/$MODEL.default.tbl $CM $CONTIGS
cmsearch --rfam --nohmmonly --cpu $THREADS \
  -o $OUT/$MODEL.relaxed.cmsearch.txt --tblout $OUT/$MODEL.relaxed.tbl $CM $CONTIGS
```

## QC gates to record

- Contigs are non-empty with a DNA alphabet. Start and stop codons of called genes are checked.
- Each assembly has its own output directory and input checksum. No caller output is shared across assemblies.
- `--threads` and `--cores` equal the allocated CPUs.
- `ncRNA_census.tsv` has the tRNAscan-SE count, default and relaxed results for every Rfam rRNA model, explicit zero counts, and the "not screened" row for viruses. Rfam release and model checksums are recorded.
- Gene metrics carry flags for unusual ORFs, gene density, coding fraction, and tRNA or rRNA features. Specialized inputs use a literature or tool-supported mode, or the reason is documented.
- With transcript evidence, the mapping summaries show which draft genome the evidence supports.

## Outputs

The agent writes these files. A restartable project driver follows the `bioinformatics-project` skill. All files sit under `<run>/gene-calling/`, where `<run>` is the dated run directory `results/<date>_<name>/` that `bioinformatics-project` defines.

- `<assembly>/`: `genes.gff3`, `proteins.faa`, `cds.fna`, `trnascan.tsv`, and for each Rfam model and threshold `{model}.{threshold}.tbl` with its `.cmsearch.txt` log.
- Eukaryotes: `<assembly>/braker4/samples.csv`, `config.ini`, and `output/{sample}/results/braker.{gff3,aa,codingseq}.gz`.
- `ncRNA_census.tsv`: columns `assembly`, `class` (tRNA, rRNA, tmRNA, other), `tool`, `model` (Rfam accession when it applies), `threshold` (default or relaxed), `count`, `notes`. Rows: one tRNA row per assembly (`model` `all`), one rRNA row per model and threshold, one "not screened" row for viruses (`model` `none`, `threshold` and `count` `NA`). Add tmRNA or other rows when you run those screens. The file is required even when all counts are zero.
- `gene_metrics.tsv`: gene count, gene density, coding fraction, ORF length distribution, unusually long ORFs, overlapping genes, tRNA and rRNA counts.
- `gene_calling_discovery_flags.tsv`: anomalies against the inferred group and data type.
- `gene_calling_evidence.tsv`: only when transcript evidence is used.
- `logs/`.
