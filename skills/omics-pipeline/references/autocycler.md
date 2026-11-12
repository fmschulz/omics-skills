# Autocycler v0.8.0

Autocycler builds a consensus long-read assembly for bacterial isolate genomes by comparing multiple independent assembly attempts. Use it when isolate closure and structural confidence matter more than producing a quick draft.

Last verified: 2026-11-11
Tool version/release checked: Autocycler v0.8.0 (GitHub release, 2026-10-02); Raven 1.8.3
Official docs/manual: https://github.com/rrwick/Autocycler/wiki
Release/source: https://github.com/rrwick/Autocycler/releases/tag/v0.8.0

## Official Documentation

- Website: https://github.com/rrwick/Autocycler
- Manual/wiki: https://github.com/rrwick/Autocycler/wiki
- Releases: https://github.com/rrwick/Autocycler/releases

## When to Use

- Bacterial or archaeal isolate genome, not a mixed-community metagenome.
- ONT or PacBio long reads with enough depth for several independent assemblies.
- The expected output is a complete or near-complete consensus assembly.

## When Not to Use

- Metagenomes, enrichment cultures, or samples with unresolved strain mixtures.
- Low-coverage datasets where independent assemblies are not stable.
- Routine draft assembly where Flye alone is sufficient.

## Workflow

1. QC reads and confirm isolate context.
2. Generate multiple independent draft assemblies with tools such as Flye, Raven, miniasm/minipolish, or other Autocycler-supported paths.
3. Run Autocycler to cluster, trim, resolve, and combine the assemblies.
4. Polish the consensus where appropriate.
5. Run assembly QC and confirm circularization, coverage, contamination, and domain routing.

## Changes since v0.6.2

- v0.7.0: `autocycler combine --reads` adds per-sequence read depths to the consensus (`>1 length=158261 depth=59.0`). `--depth_kmer` sets the k-mer size for it (default 19).
- v0.8.0: reads may be FASTQ or unaligned BAM (uBAM), and the tool runs about 7% faster.
- v0.6.3: `autocycler helper` gains Ilesta, and an empty cluster now triggers the `One or more clusters failed to fully resolve` message.

## Command Examples

All commands below ran on v0.8.0 on 2026-11-11, on simulated nanopore reads (60x of a 160 kb genome).

```bash
# Inspect installed version and command help.
autocycler --version
autocycler --help
```

```bash
# Create read subsets for multiple independent assemblies.
# `helper genome_size` runs Raven: put `raven` on PATH, or the command stops with "required program 'raven' not found".
# `subsample --min_read_depth` sets the minimum depth of a subset (default 25).
genome_size=$(autocycler helper genome_size --reads long_reads.fastq.gz --threads 16)
autocycler subsample \
  --reads long_reads.fastq.gz \
  --out_dir autocycler_subsampled \
  --genome_size "$genome_size"
```

```bash
# One draft assembly per subset and assembler; `helper` wraps the assembler (Flye and Raven shown).
mkdir -p assemblies
for i in 01 02 03 04; do
  for tool in flye raven; do
    autocycler helper $tool --reads autocycler_subsampled/sample_$i.fastq \
      --out_prefix assemblies/${tool}_$i --threads 16 --genome_size "$genome_size" --read_type ont_r10
  done
done
```

```bash
# Compress draft assemblies, then run the Autocycler consensus stages.
autocycler compress \
  --assemblies_dir assemblies \
  --autocycler_dir autocycler_out \
  --threads 16

autocycler cluster \
  --autocycler_dir autocycler_out

for c in autocycler_out/clustering/qc_pass/cluster_*; do
  autocycler trim \
    --cluster_dir "$c" \
    --threads 16

  autocycler resolve \
    --cluster_dir "$c"
done

# --reads is optional; it writes per-sequence read depths
autocycler combine \
  --autocycler_dir autocycler_out \
  --in_gfas autocycler_out/clustering/qc_pass/cluster_*/5_final.gfa \
  --reads long_reads.fastq.gz \
  --threads 16
```

`autocycler trim` and `combine` default to 8 threads, so pass `--threads` on a shared node. The glob takes only the `qc_pass` clusters; clusters that fail the QC sit in `autocycler_out/clustering/qc_fail/` (two of three on the tiny test set).

## Quality Checks

- Record every input assembler, version, seed, and parameter set.
- Inspect unresolved clusters or conflicting contigs before accepting a consensus.
- Confirm the final assembly is biologically plausible for the organism: genome size, GC content, coverage, and expected single-copy marker behavior.
- Do not carry Autocycler outputs into metagenome binning workflows without explicitly documenting why the sample is effectively clonal.
