# QuickBin (BBTools) v39.85

High-fidelity metagenomic binning using neural networks with conservative contig merging.

Last verified: 2026-11-11
Tool version/release checked: QuickBin in BBTools v39.85 via `bryce911/bbtools:39.85` (digest `sha256:e697da46d8955a30256cc1c2a9ed8da362ad5a86ed16b6a41ab64ed03801a2a1`); flags and runs also checked on `bryce911/bbtools:40.05` (digest `sha256:b39c1c2a9bbbafefc1662d20607eece9ed4d4db72506760735062df3cd23f6ec`; newest GitHub release v40.01)
Official docs/manual: https://bbmap.org/tools/quickbin
Release/source: https://hub.docker.com/r/bryce911/bbtools/tags and https://github.com/bbushnell/BBTools

## Official Documentation
- BBTools Homepage: https://jgi.doe.gov/data-and-tools/software-tools/bbtools/
- BBMap: https://bbmap.org/
- QuickBin: https://bbmap.org/tools/quickbin
- GitHub: https://github.com/bbushnell/BBTools
- Preprint: https://www.biorxiv.org/content/10.64898/2026.01.08.698506v3
- Container tags: https://hub.docker.com/r/bryce911/bbtools/tags
- Version pinned: 39.85 (newest tag: 40.05; see "Tags 39.85 and 40.05")

## Installation

**Preferred container (Bryce Foster's official BBTools image):**
```bash
docker pull bryce911/bbtools:39.85
docker run --rm bryce911/bbtools:39.85 quickbin.sh --help
```

On 2026-11-11, Docker Hub reports `bryce911/bbtools:39.85` at digest `sha256:e697da46d8955a30256cc1c2a9ed8da362ad5a86ed16b6a41ab64ed03801a2a1` (unchanged since 2026-05-30). `latest` has moved on: it is `40.05` at digest `sha256:b39c1c2a9bbbafefc1662d20607eece9ed4d4db72506760735062df3cd23f6ec`. Pin the tag in workflow docs and record the digest in run provenance.

Without `-Xmx`, `quickbin.sh` took a 65 GB heap on a 247 GB host. Give `-Xmx<N>g` right after the script name on a shared node.

**Apptainer/Singularity:**
```bash
apptainer exec docker://bryce911/bbtools:39.85 quickbin.sh --help
```

Local BBTools installs are acceptable only when the container runtime is unavailable; record the local BBTools version and install path.

## Tags 39.85 and 40.05

On 2026-11-11 both tags ran the BAM-input commands of this page (`reads=`, `xstrict`, `covout=`, `readthreads=`, `maxsamples=`, output with and without `%`) on a mock community of four genomes and two BAM files made with bwa-mem2. Tag 39.85 also ran `cov=` with `cutoff=0.55`. The SAM-input examples and the `loose` and `xloose` presets were not run. The pack stays on 39.85 until the QuickBin and QuickClade pages move together, for these reasons:

- `threads=`, `readthreads=` and `maxsamples=` have the same text and defaults in both help outputs (`threads=auto`, `readthreads=4`, `maxsamples=8`). With `readthreads=1 maxsamples=1` and two BAM files both tags print `Merging into 1 samples (Modulo Mode)` and `concurrency=1`.
- The results differ. On the same input with `xstrict`, 39.85 wrote 6 bins and 40.05 wrote 3. 39.85 reports `Loaded 2 files and 0 reads` for BAM input and 40.05 reports 431,597 reads. Do not mix tags within one project.
- The 40.x images no longer contain the QuickClade reference `refseqA48_with_ribo.spectra.gz` (245 MB in the 39.85 image), and the `format=machine` output of 40.05 has 21 columns instead of 26 (no `ANI`, `WKID`, `KID`, `Completeness`, `KmerMatches`). See [../../tracking-taxonomy-updates/reference/tools.md](../../tracking-taxonomy-updates/reference/tools.md).

## Key Command-Line Flags

| Flag | Description | Default |
|------|-------------|---------|
| `in=<file>` | Input contigs (FASTA) | Required |
| `out=<pattern>` | Output bin pattern (use `%` for per-bin files) | Required |
| `reads=<files>` | SAM/BAM alignment files (comma-separated) | - |
| `cov=<file>` | Pre-computed coverage file | - |
| `covout=<file>` | Save coverage stats for reuse | - |
| `mincluster=` | Minimum cluster size | 50000 |
| `minseed=` | Minimum contig length for seed | 2500 |
| `cutoff=` | Neural network decision threshold | 0.52 |
| `threads=` | Worker threads (`threads=auto`) | all logical cores |
| `report=<file>` | Bin size, GC, depth and taxonomy table. Sends the bin k-mer spectra to a remote QuickClade server unless you pass `clade=f` | - |
| `clade=` | `clade=t` labels the bins with QuickClade (needs the network when `report=` is set) | `t` |
| `readthreads=` | SAM/BAM files loaded concurrently; lower uses less memory | 4 |
| `maxsamples=` | Above this many SAM/BAM files, QuickBin merges some into one logical sample to save memory | 8 |

### Stringency Presets

| Flag | Description |
|------|-------------|
| `xstrict` | Very high specificity (fewer, purer bins) |
| `ustrict`, `vstrict` | Between `xstrict` and `strict` |
| `strict` | High specificity |
| `normal` | Balanced (default); aims at under 1% contamination |
| `loose` | Higher sensitivity |
| `vloose`, `uloose` | Between `loose` and `xloose` |
| `xloose` | Very high sensitivity (more, potentially mixed bins) |

`strictness=<float>` sets the same scale finely (`normal`=1.0, `xstrict`=0.6, `strict`=0.9, `loose`=1.1, `xloose`=1.5; lower is stricter).

## Common Usage Examples

### Basic binning with SAM files
```bash
mkdir -p quickbin
docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD":/work -w /work \
  bryce911/bbtools:39.85 \
  quickbin.sh in=contigs.fasta out=quickbin/bin%.fa \
    sample1.sam sample2.sam sample3.sam covout=quickbin/coverage.txt
```

### Using BAM files and per-bin output
```bash
mkdir -p bins
docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD":/work -w /work \
  bryce911/bbtools:39.85 \
  quickbin.sh in=assembly.fasta out=bins/bin%.fa \
    reads=sample1.bam,sample2.bam,sample3.bam \
    threads=16
```

### Save coverage for fast reruns
```bash
# First run: compute and save coverage
mkdir -p quickbin
docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD":/work -w /work \
  bryce911/bbtools:39.85 \
  quickbin.sh in=contigs.fasta out=quickbin/bin%.fa \
    sample*.sam covout=quickbin/coverage.txt

# Subsequent runs: reuse coverage (much faster)
mkdir -p quickbin_rerun
docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD":/work -w /work \
  bryce911/bbtools:39.85 \
  quickbin.sh in=contigs.fasta out=quickbin_rerun/bin%.fa \
    cov=quickbin/coverage.txt cutoff=0.55
```

### High specificity binning (low contamination)
```bash
mkdir -p quickbin
docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD":/work -w /work \
  bryce911/bbtools:39.85 \
  quickbin.sh in=contigs.fasta out=quickbin/bin%.fa sample*.bam xstrict
```

### High sensitivity binning (maximize recovery)
```bash
mkdir -p quickbin
docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD":/work -w /work \
  bryce911/bbtools:39.85 \
  quickbin.sh in=contigs.fasta out=quickbin/bin%.fa sample*.bam xloose
```

### Custom neural network threshold
```bash
mkdir -p quickbin
docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD":/work -w /work \
  bryce911/bbtools:39.85 \
  quickbin.sh in=contigs.fasta out=quickbin/bin%.fa sample*.sam cutoff=0.60
```

## Input Requirements

**Contigs file:**
- FASTA format
- Minimum length: 2500 bp (default seed threshold)
- Shorter contigs can be included but won't seed clusters

**Coverage data:**
- Option 1: SAM/BAM files from read mapping
- Option 2: Pre-computed coverage file (generated with `covout=`)
- Multiple samples strongly recommended (3-10 optimal)

**Generating SAM/BAM files:**
```bash
# Example with BBMap; the QuickBin help recommends ambig=random mateqtag minid=0.9 maxindel=10
bbtools() {
  docker run --rm -u "$(id -u):$(id -g)" \
    -v "$PWD":/work -w /work \
    bryce911/bbtools:39.85 "$@"
}

bbtools bbmap.sh ref=contigs.fasta in=reads_1.fq.gz in2=reads_2.fq.gz \
  ambig=random mateqtag minid=0.9 maxindel=10 out=sample1.sam threads=16

# Example with minimap2
minimap2 -ax sr -t 16 contigs.fasta reads_1.fq.gz reads_2.fq.gz > sample1.sam
```

## Output Format

**With `%` in output pattern:** One file per bin, numbered from 0
```
bin0.fa
bin1.fa
bin2.fa
...
```

**Without `%`:** One file with all binned contigs. Both tags kept the original contig headers, with no bin number in them (`>NODE_1_length_159654_cov_18.992751`), so use `%` when you need the bin of each contig.

## Neural Network Threshold

The `cutoff` parameter controls binning stringency:

- **Higher values (0.55-0.70)**: Fewer false positive merges, higher purity, lower completeness
- **Default (0.52)**: Balanced precision and recall
- **Lower values (0.40-0.50)**: More merges, higher completeness, risk more contamination

Tune based on downstream requirements:
- **Strict QC (≤1% contamination)**: Use `xstrict` or `cutoff=0.60+`
- **MAG recovery**: Use default or slightly lower cutoff
- **Exploration**: Use `xloose` for maximum sensitivity

## Algorithm Features

QuickBin uses:
1. **GC content** - Compositional similarity
2. **Multi-sample coverage** - Differential abundance patterns
3. **Graph connectivity** - Assembly graph structure
4. **Neural network** - Final adjudication of merges

Conservative approach prioritizes **high-fidelity bins** (low contamination) over maximum recovery.

## Performance Tips

1. **Multiple samples**: 3-10 samples from same environment optimal
2. **Coverage optimization**: Save coverage with `covout=`, reuse with `cov=`
3. **Threading**: Set `threads=` to the allocated CPUs; `readthreads=` is the number of SAM/BAM files loaded at once
4. **Sample limits**: above `maxsamples=` files QuickBin merges samples; merging samples of the same depth or environment by hand is the better choice
5. **Incremental testing**: Start with `xstrict`, relax if completeness too low
6. **Memory**: Efficient; scales to large assemblies (tested on 10M+ contigs)

## Comparison with Other Binners

Binner choice and the independent benchmarks are in [binning.md](binning.md).

**QuickBin advantages:**
- Very high precision (low contamination)
- Fast (pretrained neural network, no EM iterations)
- Scalable to large datasets
- Conservative merging reduces chimeras

**Considerations:**
- May produce lower completeness than aggressive binners
- Requires multiple samples for best performance
- Optimized for beyond-MIMAG quality (≤1% contamination)

## Integration with QC Tools

```bash
# Run QuickBin
mkdir -p bins
docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD":/work -w /work \
  bryce911/bbtools:39.85 \
  quickbin.sh in=contigs.fasta out=bins/bin%.fa sample*.bam xstrict

# Assess bacterial/archaeal bins
checkm2 predict --input bins/ -x .fa --output-directory qc/ -t 16

# Check for contamination
GUNC_DB=$(find gunc_db -name '*.dmnd' | head -n 1)
gunc run --input_dir bins/ --db_file "$GUNC_DB" --out_dir gunc_qc/ --threads 16
```

## Common Issues

- **Too few bins**: Try `loose` or `xloose`, check coverage variation
- **Low completeness**: Reduce stringency (lower cutoff or use `loose`)
- **High contamination**: Increase stringency (`xstrict` or higher cutoff)
- **Slow processing**: Use `covout=` to save coverage, reuse in subsequent runs
- **Memory errors**: Lower `readthreads=` so fewer SAM/BAM files load at once

## Advanced Options

### Coverage file format
The coverage file (`covout=`) contains per-contig GC and depth statistics, enabling rapid parameter tuning without reprocessing alignments.

### Combining with other binners
QuickBin can be used in ensemble binning approaches:
```bash
# Run multiple binners
metabat2 -i contigs.fasta -a depth.txt -o metabat/bin
SemiBin2 single_easy_bin -i contigs.fasta -b reads.bam -o semibin/
mkdir -p quickbin
docker run --rm -u "$(id -u):$(id -g)" \
  -v "$PWD":/work -w /work \
  bryce911/bbtools:39.85 \
  quickbin.sh in=contigs.fasta out=quickbin/bin%.fa sample*.bam xstrict

# Refine with DAS Tool or similar
```

## Citation

Bushnell B, Villada JC. (2026)
Deployable high-fidelity metagenome binning at scale with QuickBin.
*Communications Biology*. https://doi.org/10.1038/s42003-026-10782-z
