# Autocycler v0.6.2

Autocycler builds a consensus long-read assembly for bacterial isolate genomes by comparing multiple independent assembly attempts. Use it when isolate closure and structural confidence matter more than producing a quick draft.

Last verified: 2026-05-30
Tool version/release checked: Autocycler v0.6.2 (GitHub release, 2026-04-14)
Official docs/manual: https://github.com/rrwick/Autocycler/wiki
Release/source: https://github.com/rrwick/Autocycler/releases/tag/v0.6.2

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

## Command Examples

```bash
# Inspect installed version and command help.
autocycler --version
autocycler --help
```

```bash
# Create read subsets for multiple independent assemblies.
genome_size=$(autocycler helper genome_size --reads long_reads.fastq.gz --threads 16)
autocycler subsample \
  --reads long_reads.fastq.gz \
  --out_dir autocycler_subsampled \
  --genome_size "$genome_size"
```

```bash
# Compress draft assemblies, then run the Autocycler consensus stages.
autocycler compress \
  --assemblies_dir assemblies \
  --autocycler_dir autocycler_out

autocycler cluster \
  --autocycler_dir autocycler_out

for c in autocycler_out/clustering/qc_pass/cluster_*; do
  autocycler trim \
    --cluster_dir "$c"

  autocycler resolve \
    --cluster_dir "$c"
done

autocycler combine \
  --autocycler_dir autocycler_out \
  --in_gfas autocycler_out/clustering/qc_pass/cluster_*/5_final.gfa
```

## Quality Checks

- Record every input assembler, version, seed, and parameter set.
- Inspect unresolved clusters or conflicting contigs before accepting a consensus.
- Confirm the final assembly is biologically plausible for the organism: genome size, GC content, coverage, and expected single-copy marker behavior.
- Do not carry Autocycler outputs into metagenome binning workflows without explicitly documenting why the sample is effectively clonal.
