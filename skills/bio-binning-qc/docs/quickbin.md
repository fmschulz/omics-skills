# QuickBin (BBTools) v39.52

High-fidelity metagenomic binning using neural networks with conservative contig merging.

## Official Documentation
- BBTools Homepage: https://jgi.doe.gov/data-and-tools/software-tools/bbtools/
- BBMap: https://bbmap.org/
- QuickBin: https://bbmap.org/tools/quickbin
- GitHub: https://github.com/bbushnell/BBTools
- Preprint: https://www.biorxiv.org/content/10.64898/2026.01.08.698506v3
- Version: 39.52

## Installation

**Download BBTools:**
```bash
wget https://sourceforge.net/projects/bbmap/files/latest/download -O BBMap.tar.gz
tar -xzf BBMap.tar.gz
export PATH=$PATH:$(pwd)/bbmap/
```

**Conda:**
```bash
conda install -c bioconda bbtools
```

**Docker:**
```bash
docker pull quay.io/biocontainers/bbtools
```

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
| `readthreads=` | Threads for processing SAM files | 4 |
| `maxsamples=` | Max SAM files to process concurrently | 8 |

### Stringency Presets

| Flag | Description |
|------|-------------|
| `xstrict` | Very high specificity (fewer, purer bins) |
| `strict` | High specificity |
| `normal` | Balanced (default) |
| `loose` | Higher sensitivity |
| `xloose` | Very high sensitivity (more, potentially mixed bins) |

## Common Usage Examples

### Basic binning with SAM files
```bash
quickbin.sh in=contigs.fasta out=bin%.fa \
  sample1.sam sample2.sam sample3.sam
```

### Using BAM files and per-bin output
```bash
quickbin.sh in=assembly.fasta out=bins/bin%.fa \
  reads=sample1.bam,sample2.bam,sample3.bam \
  readthreads=8
```

### Save coverage for fast reruns
```bash
# First run: compute and save coverage
quickbin.sh in=contigs.fasta out=bin%.fa \
  sample*.sam covout=coverage.txt

# Subsequent runs: reuse coverage (much faster)
quickbin.sh in=contigs.fasta out=bin%.fa \
  cov=coverage.txt cutoff=0.55
```

### High specificity binning (low contamination)
```bash
quickbin.sh in=contigs.fasta out=bin%.fa \
  sample*.bam xstrict
```

### High sensitivity binning (maximize recovery)
```bash
quickbin.sh in=contigs.fasta out=bin%.fa \
  sample*.bam xloose
```

### Custom neural network threshold
```bash
quickbin.sh in=contigs.fasta out=bin%.fa \
  sample*.sam cutoff=0.60
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
# Example with BBMap
bbmap.sh ref=contigs.fasta in=reads_1.fq.gz in2=reads_2.fq.gz \
  out=sample1.sam threads=16

# Example with minimap2
minimap2 -ax sr -t 16 contigs.fasta reads_1.fq.gz reads_2.fq.gz > sample1.sam
```

## Output Format

**With `%` in output pattern:** One file per bin
```
bin1.fa
bin2.fa
bin3.fa
...
```

**Without `%`:** Single file with bin numbers in headers
```
>bin_1_contig_001
ATCG...
>bin_1_contig_002
ATCG...
>bin_2_contig_001
ATCG...
```

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
3. **Threading**: Use `readthreads=` to parallelize SAM/BAM processing
4. **Sample limits**: `maxsamples=` controls concurrent file processing
5. **Incremental testing**: Start with `xstrict`, relax if completeness too low
6. **Memory**: Efficient; scales to large assemblies (tested on 10M+ contigs)

## Comparison with Other Binners

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
quickbin.sh in=contigs.fasta out=bins/bin%.fa sample*.bam xstrict

# Assess bacterial/archaeal bins
checkm2 predict --input bins/ --output-directory qc/ -t 16

# Check for contamination
gunc run --input_dir bins/ --db_file gunc_db --threads 16
```

## Common Issues

- **Too few bins**: Try `loose` or `xloose`, check coverage variation
- **Low completeness**: Reduce stringency (lower cutoff or use `loose`)
- **High contamination**: Increase stringency (`xstrict` or higher cutoff)
- **Slow processing**: Use `covout=` to save coverage, reuse in subsequent runs
- **Memory errors**: Process fewer samples concurrently with `maxsamples=`

## Advanced Options

### Coverage file format
The coverage file (`covout=`) contains per-contig GC and depth statistics, enabling rapid parameter tuning without reprocessing alignments.

### Combining with other binners
QuickBin can be used in ensemble binning approaches:
```bash
# Run multiple binners
metabat2 -i contigs.fasta -a depth.txt -o metabat/bin
semibin2 single_easy_bin -i contigs.fasta -b reads.bam -o semibin/
quickbin.sh in=contigs.fasta out=quickbin/bin%.fa sample*.bam xstrict

# Refine with DAS Tool or similar
```

## Citation

Bushnell B. (2026)
Deployable high-fidelity metagenome binning at scale with QuickBin.
*bioRxiv*. https://doi.org/10.64898/2026.01.08.698506
