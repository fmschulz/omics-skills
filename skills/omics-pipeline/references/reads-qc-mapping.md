# Reads QC and mapping

**Last verified:** 2026-05-30
**Tool version/release checked:** BBTools v39.85; minimap2 v2.31; Filtlong v0.3.1; Porechop_ABI source 0.5.1 / tag v0.5.0; fastp v1.3.7 (current on 2026-10-01)
**Official docs/manual:** https://bbmap.org/tools/bbduk ; https://bbmap.org/docs.html ; https://lh3.github.io/minimap2/minimap2.html ; https://github.com/rrwick/Filtlong/tree/v0.3.1#full-usage ; https://github.com/bonsai-team/Porechop_ABI ; https://github.com/OpenGene/fastp ; https://github.com/wdecoster/chopper ; https://github.com/nanoporetech/dorado
**Release/source:** https://hub.docker.com/r/bryce911/bbtools/tags ; https://github.com/lh3/minimap2/releases/tag/v2.31 ; https://github.com/rrwick/Filtlong/releases/tag/v0.3.1 ; https://github.com/bonsai-team/Porechop_ABI/tags

Shared rules (large ONT reads, environment, threads, scheduler) are in [../SKILL.md](../SKILL.md). This page holds only the defaults and traps of this stage.

## Use when

Raw FASTQ needs adapter, quality or contaminant handling, or QC-passed reads need mapping and coverage. Inputs per sample: a read type (`paired_short`, `single_short` or `long`), the read files, and an optional reference. No reference means no mapping, which is not a failure.

## Tool choice

| Case | Default | Use the alternative when |
| --- | --- | --- |
| Short-read QC and trimming | `fastp`, default adapter and quality trimming | k-mer contaminant, spike-in or host removal: BBDuk |
| Long-read QC from signal or BAM | Dorado trimming at basecalling or demultiplexing | - |
| Long-read QC from FASTQ only | `chopper` (quality, length, end trimming) | assembly input selection: `filtlong`; full-length cDNA: `Pychopper` |
| ONT adapter discovery | none | `Porechop_ABI` as a fallback only; record why |
| Short-read mapping | `bwa-mem2 mem` | BBMap for BBTools-based work; GPU: Parabricks `fq2bam` |
| Long-read mapping | `minimap2 -ax map-ont` | HiFi: `map-hifi`; PacBio CLR: `map-pb`; GPU: Parabricks `minimap2` |

## Rules a model would not guess

- Run BBTools only from the `bryce911/bbtools:39.85` container. Everything else comes from the pinned pixi environment.
- `filtlong` stops with `Error: no thresholds set` when no threshold is given, and the shell redirect has by then left an empty output file. Set at least one of `--min_length`, `--keep_percent` or `--target_bases` per project and record it. Filtlong is single-threaded and has no thread flag.
- Filtlong v0.3.0 renamed `--illumina_1` and `--illumina_2` to `--short_1` and `--short_2`. Use v0.3.1 names.
- `bwa-mem2 mem` fails at once on a reference without an index. Run `bwa-mem2 index` first.
- Mapping writes SAM. Sort and index it, then get per-reference coverage with `samtools coverage` or CoverM.
- `Pychopper` can write plain FASTQ under a `.gz` name. Give its outputs `.fastq` names and check gzip magic bytes before `gzip -t`. Rename mislabeled legacy outputs before resuming.
- `Pychopper` report plotting can fail after the reads are written. If the classified, unclassified, rescued and read-stats outputs exist and are non-empty, resume downstream from them.
- ONT cDNA for eukaryotic gene calling: orient with `Pychopper`, map splice-aware (`minimap2 -ax splice`) to each candidate draft genome, and keep the full per-genome mapped-fraction table even when one draft wins. Add a StringTie long-read GTF and transcript FASTA, and RNA-Bloom when useful. Summarize in `gene_calling_evidence.tsv` (`sample_id`, `evidence_type`, `genome_id`, `path`, `notes`).
- GPU mapping runs only through the scheduler on a GPU node. Check it against the CPU path on a small subset first, and record tool, version and GPU device in `tasks/METHODS.md`. The `mm2-fast` and `mm2-gb` forks sit on minimap2 v2.24, older than the version above.

## Commands

```bash
# Short reads, paired (single-end: drop --in2/--out2, output reads.fastq)
fastp --thread $THREADS --in1 $R1 --in2 $R2 --out1 $OUT/reads_R1.fastq --out2 $OUT/reads_R2.fastq \
  --json $OUT/fastp.json --html $OUT/fastp.html

# Long reads (no thread flag)
filtlong --min_length $MIN_LENGTH $LONG > $OUT/reads.fastq   # one threshold is required; or --keep_percent P, --target_bases B

# Mapping, only for rows with a reference
bwa-mem2 index $REF
bwa-mem2 mem -t $THREADS $REF $OUT/reads_R1.fastq $OUT/reads_R2.fastq > $OUT/mapped.sam
minimap2 -t $THREADS -ax map-ont $REF $OUT/reads.fastq > $OUT/mapped.sam
samtools sort -@ $THREADS -o $OUT/mapped.bam $OUT/mapped.sam && samtools index $OUT/mapped.bam
samtools coverage $OUT/mapped.bam > $OUT/coverage.tsv
```

The lines above were covered by tests. The BBTools, `chopper` and Porechop_ABI lines below come from the tool guides and were not tested here.

```bash
bbtools() { docker run --rm -u "$(id -u):$(id -g)" -v "$PWD":/work -w /work bryce911/bbtools:39.85 "$@"; }
bbtools bbduk.sh -Xmx1g threads=$THREADS in1=$R1 in2=$R2 out1=c1.fq out2=c2.fq ref=adapters.fa \
  ktrim=r k=23 mink=11 hdist=1 qtrim=rl trimq=20 minlength=50 tpe tbo     # adapters and quality
bbtools bbduk.sh -Xmx1g threads=$THREADS in=r.fq out=f.fq ref=phix174_ill.ref.fa.gz k=31 hdist=1   # contaminant
bbtools bbmap.sh threads=$THREADS ref=$REF in1=c1.fq in2=c2.fq out=mapped.sam
chopper --threads $THREADS --quality 10 --minlength 1000 < raw.fastq.gz | gzip > filtered.fastq.gz
porechop_abi -i raw.fastq -o trimmed.fastq -t $THREADS
```

## QC gates to record

- Post-QC read counts against raw counts (`fastp.json` or `seqkit stats`).
- Mapping rate, for rows with a reference only: the cutoff chosen for this project, the observed rate and pass or fail. A failure is reported, not tuned away.
- Long-read QC: where trimming happened (basecaller or demultiplexer, `chopper`, `filtlong`, `Pychopper`, or a Porechop_ABI fallback with its reason).
- Reused outputs pass a light content check (`seqkit stats`, FASTQ header sniff or gzip magic) before downstream use.

## Outputs

The agent writes these. A restartable project driver follows the `bioinformatics-project` skill.

- `results/reads-qc-mapping/<sample_id>/`: `reads_R1.fastq` and `reads_R2.fastq` (or `reads.fastq`), `fastp.json`, `fastp.html`, `mapped.sam`, and the `qc.done` and `mapping.done` markers.
- `results/reads-qc-mapping/mapping_stats.tsv`: `sample_id`, `mapping_status` (`completed`, `reused`, `failed`, or `not_requested` when no reference), `reference`.
- `results/reads-qc-mapping/run_manifest.json`: the commands run and the status of each step, also after a failure.
