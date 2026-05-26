# Autocycler

Autocycler builds a consensus long-read assembly for bacterial isolate genomes by comparing multiple independent assembly attempts. Use it when isolate closure and structural confidence matter more than producing a quick draft.

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

## Quality Checks

- Record every input assembler, version, seed, and parameter set.
- Inspect unresolved clusters or conflicting contigs before accepting a consensus.
- Confirm the final assembly is biologically plausible for the organism: genome size, GC content, coverage, and expected single-copy marker behavior.
- Do not carry Autocycler outputs into metagenome binning workflows without explicitly documenting why the sample is effectively clonal.
