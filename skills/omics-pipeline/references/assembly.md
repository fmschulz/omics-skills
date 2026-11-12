# Assembly and assembly QC

**Last verified:** 2026-11-11
**Tool version/release checked:** SPAdes v4.3.0; Flye v2.9.6; Autocycler v0.8.0 (with Raven 1.8.3 for `helper`); QUAST v5.3.0; metaMDBG v1.4; myloasm v0.7.0 (release notes only, not run)
**Official docs/manual:** https://github.com/ablab/spades#manual ; https://github.com/fenderglass/Flye/blob/2.9.6/docs/USAGE.md ; https://github.com/rrwick/Autocycler/wiki ; http://quast.sourceforge.net/docs/manual.html ; https://github.com/GaetanBenoitDev/metaMDBG ; https://github.com/bluenote-1577/myloasm
**Release/source:** https://github.com/ablab/spades/releases/tag/v4.3.0 ; https://github.com/mikolmogorov/Flye/releases/tag/2.9.6 ; https://github.com/rrwick/Autocycler/releases/tag/v0.8.0 ; https://github.com/ablab/quast/releases/tag/quast_5.3.0 ; https://github.com/GaetanBenoitDev/metaMDBG/releases

Shared rules (large ONT reads, `.tmp` then `mv`, environment, threads, scheduler, failure handling) are in [../SKILL.md](../SKILL.md). This page holds only the defaults and traps of this stage.

## Use when

QC-passed reads need turning into contigs, with contiguity metrics. Per sample you need: a mode (`short_isolate`, `long_isolate`, `short_metagenome`, `long_metagenome` or `hifi_metagenome`), the read files, the read-QC status (assemble only samples that passed read QC; see [reads-qc-mapping.md](reads-qc-mapping.md)), and for long reads the platform (`ont`, `pacbio-clr` or `pacbio-hifi`).

## Tool choice

| Case | Default | Use the alternative when |
| --- | --- | --- |
| Illumina isolate | `spades.py --isolate` | hybrid with long reads: SPAdes `--pacbio` or `--nanopore`, or Flye plus short-read polishing |
| Illumina metagenome | `metaspades.py` | - |
| ONT or PacBio CLR isolate | Flye | complete bacterial consensus from several independent assemblies: Autocycler ([autocycler.md](autocycler.md)) |
| PacBio HiFi isolate | `flye --pacbio-hifi` | same Autocycler case |
| ONT or CLR metagenome | metaFlye (`flye --meta`) | ONT R10.4+: nanoMDBG, which is `metaMDBG asm --in-ont` (rule below); runtime-bound on very large or diverse data: myloasm, if the read profile fits |
| HiFi metagenome | metaMDBG | keep metaFlye as a comparator when one sample fails |

## Rules a model would not guess

- Flye needs the read chemistry. Map `read_platform` to the flag: `ont` gives `--nano-hq`, `pacbio-clr` gives `--pacbio-raw`, `pacbio-hifi` gives `--pacbio-hifi`. `--nano-hq` on CLR reads uses the wrong error model. Refuse a long-read row without a platform. `hifi_metagenome` takes only `pacbio-hifi` or an empty value.
- Short-read `contigs.fasta` is a copy of SPAdes `scaffolds.fasta`, not SPAdes `contigs.fasta`. Flye gives `assembly.fasta`. metaMDBG gives `contigs.fasta.gz`, which must be decompressed. Every sample ends with one non-empty `contigs.fasta` before QC or routing.
- Autocycler only for a clonal isolate with enough depth for several independent assemblies. It is not for mixed communities. Record every input assembler run.
- metaMDBG recovered up to twice as many circularized high-quality MAGs as metaFlye on HiFi data (Benoit et al. 2024, *Nature Biotechnology*, https://doi.org/10.1038/s41587-023-01983-6).
- nanoMDBG, the metaMDBG mode for ONT R10.4+ simplex reads (`metaMDBG asm --in-ont`), reconstructed up to twice as many high-quality MAGs as metaFlye in its authors' benchmark, with a third of the CPU time and memory (Benoit et al. (2026) *Nature Communications* https://doi.org/10.1038/s41467-026-69760-y). Not independently benchmarked: metaFlye stays the default.
- After a Flye or metaFlye failure or interruption, read `flye.log` and the stage files first. If the output directory is intact, resume in place with `--resume` or `--resume-from`. Delete a large partial assembly only when the logs or missing stage files show corruption. SPAdes resumes with `--continue`.
- Check free disk before assembly. Flye needs about 50 to 100 times the input size.
- The SPAdes commands below ran on v4.3.0 (2026-06-14). It adds a low-memory `--frugal` mode; its release notes list no removed options, and `--isolate`, `--continue`, `--pacbio` and `--nanopore` are still in `spades.py --help`.
- Flye creates only the last level of `--out-dir` and stops with `FileNotFoundError` when the parent is missing. SPAdes creates the whole path. Run `mkdir -p $OUT` first.
- QUAST 5.3.0 imports `distutils`, which Python 3.12 removed. In a Python 3.13 environment `quast.py` stops with `No module named 'distutils'` until `setuptools` is in the environment.
- Run domain routing (shared rule 1) on every `contigs.fasta` before any downstream genome, MAG, viral or eukaryotic workflow.
- Record the exact command, version, thread count and RAM ceiling of each run.

## Commands

All lines ran on 2026-11-11 on simulated reads (ART paired reads, Badread nanopore and HiFi-like reads from phage and small bacterial genomes), except `--pacbio-raw` and `--pacbio-hifi` for Flye, which only appear in `flye --help`.

```bash
mkdir -p $OUT   # Flye does not create parent directories
# short_isolate (source: $OUT/assembler/scaffolds.fasta)
spades.py --isolate -1 $R1 -2 $R2 -t $THREADS -o $OUT/assembler
# short_metagenome (source: scaffolds.fasta)
metaspades.py -1 $R1 -2 $R2 -t $THREADS -o $OUT/assembler
# long_isolate; $FLAG is --nano-hq, --pacbio-raw or --pacbio-hifi (source: assembly.fasta)
flye $FLAG $READS --threads $THREADS --out-dir $OUT/assembler
# long_metagenome: the same line plus --meta
flye $FLAG $READS --threads $THREADS --out-dir $OUT/assembler --meta
# hifi_metagenome (source: contigs.fasta.gz)
metaMDBG asm --in-hifi $READS --threads $THREADS --out-dir $OUT/assembler

# Normalize to one contigs.fasta per sample, via .tmp
cp $OUT/assembler/scaffolds.fasta $OUT/contigs.fasta.tmp               # SPAdes; or assembly.fasta for Flye
gzip -dc $OUT/assembler/contigs.fasta.gz > $OUT/contigs.fasta.tmp      # metaMDBG
mv $OUT/contigs.fasta.tmp $OUT/contigs.fasta

# QC: isolates
quast.py $OUT/contigs.fasta -t $THREADS -o $OUT/quast
# QC: metagenomes, reference-free. --max-ref-number 0 stops MetaQUAST from downloading SILVA and NCBI references.
metaquast.py $OUT/contigs.fasta --max-ref-number 0 -t $THREADS -o $OUT/quast

# Resume Flye in place
flye $FLAG $READS --threads $THREADS --out-dir $OUT/assembler --resume
```

## QC gates to record

- Every assembler output is normalized to a non-empty per-sample `contigs.fasta` before QC or routing.
- Per sample from `quast/report.tsv`: contig count, total length, N50 and largest contig, against the project's thresholds for assembly size range and N50. An unmet threshold is reported as a result.
- Free disk was checked before assembly.
- Flye or metaFlye logs were read before any resume, rerun or clean.
- For an Autocycler consensus: each input assembler run is recorded and the sample is confirmed not to be a mixed community.
- Hybrid SPAdes, Autocycler and myloasm runs are done by hand: record the exact commands and versions.

## Outputs

The agent writes these. A restartable project driver follows the `bioinformatics-project` skill. `<run>` is the dated run directory `results/<date>_<name>/` that `bioinformatics-project` defines.

- `<run>/assembly/<sample_id>/assembler/`: raw assembler output.
- `<run>/assembly/<sample_id>/contigs.fasta`: the normalized assembly.
- `<run>/assembly/<sample_id>/quast/report.tsv`: QUAST or MetaQUAST metrics.
- `<run>/assembly/run_manifest.json`: validated rows, commands run, and the status of each step, also after a failure.
