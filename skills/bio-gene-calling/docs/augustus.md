# AUGUSTUS

Eukaryotic gene prediction with probabilistic modeling and external evidence integration.

## Official Documentation
- GitHub: https://github.com/Gaius-Augustus/Augustus
- Web interface: http://bioinf.uni-greifswald.de/augustus/
- User guide: https://github.com/Gaius-Augustus/Augustus/blob/master/docs/RUNNING-AUGUSTUS.md

## Installation

```bash
# Ubuntu/Debian
sudo apt install augustus augustus-data augustus-doc

# From source
git clone https://github.com/Gaius-Augustus/Augustus.git
cd Augustus
make augustus

# Add to PATH
export PATH=$HOME/Augustus/bin:$HOME/Augustus/scripts:$PATH
export AUGUSTUS_CONFIG_PATH=$HOME/Augustus/config/
```

## Basic Usage

```bash
augustus [parameters] --species=SPECIES queryfile.fa > output.gff
```

## Key Command-Line Flags

### Required Parameters
- `--species=NAME` - Species parameter set (see `config/species/`)

### Strand and Gene Model Options
- `--strand=both|forward|backward` - Report genes on specific strands
- `--genemodel=partial|intronless|complete|atleastone|exactlyone` - Gene completeness
- `--singlestrand=true` - Allow overlapping genes on opposite strands

### Evidence Integration
- `--hintsfile=FILE` - External evidence (GFF format)
- `--extrinsicCfgFile=FILE` - Hint source weights
- `--softmasking=1` - Treat lowercase as repeats

### Output Control
- `--protein=on|off` - Output protein sequences
- `--codingseq=on|off` - Output CDS sequences
- `--gff3=on|off` - Use GFF3 format
- `--UTR=on|off` - Predict UTRs (limited species)
- `--outfile=FILE` - Write to file instead of stdout

### Alternative Transcripts
- `--sample=N` - Posterior sampling (default: 100)
- `--alternatives-from-sampling=true|false` - Report probabilistic isoforms
- `--alternatives-from-evidence=true|false` - Evidence-based isoforms

## Common Usage Examples

### Basic Prediction

```bash
augustus --species=human genome.fa > predictions.gff
```

### With RNA-Seq Evidence

```bash
augustus \
    --species=arabidopsis \
    --hintsfile=rnaseq.gff \
    --softmasking=1 \
    genome.fa > predictions.gff
```

### With Protein Sequences

```bash
augustus \
    --species=human \
    --protein=on \
    --codingseq=on \
    --gff3=on \
    genome.fa > predictions.gff3
```

### Alternative Transcripts

```bash
augustus \
    --species=human \
    --alternatives-from-sampling=true \
    --sample=200 \
    genome.fa > predictions.gff
```

### Protein Profile-Based

```bash
msa2prfl.pl alignment.aln > family.prfl
augustus --proteinprofile=family.prfl genome.fa > predictions.gff
```

## Input/Output Formats

**Input:**
- FASTA format (uncompressed)
- Letters other than A,C,G,T interpreted as unknown
- Digits and whitespace ignored

**Output:**
- GTF format (GFF-like)
- One line per exon
- Fields: sequence, source, feature, start, end, score, strand, frame, attributes

## Available Species Parameters

90+ species supported, including:
- Vertebrates: human, mouse, chicken, zebrafish
- Invertebrates: drosophila, caenorhabditis
- Plants: arabidopsis, maize, rice
- Fungi: aspergillus, candida, neurospora
- Protists: toxoplasma, plasmodium

List available species:
```bash
ls $AUGUSTUS_CONFIG_PATH/species/
```

## Performance Tips

### Genome Preparation
- Use softmasked FASTA (repeats in lowercase)
- Split large genomes into scaffolds for parallelization
- Remove ambiguous sequences (N-runs)

### Evidence Integration
- RNA-Seq hints dramatically improve accuracy
- Protein homology helps in poorly conserved regions
- Weight hint sources in extrinsicCfgFile

### Computational Performance
- AUGUSTUS is single-threaded per sequence
- Parallelize by running multiple scaffolds simultaneously
- Memory usage scales with sequence length

### Training Custom Species
- Requires high-quality gene structures
- Use BRAKER for automated training
- Manual training needs 500-1000 genes

### Quality Control
- Check start/stop codons
- Verify splice sites (GT-AG canonical)
- Compare to RNA-Seq coverage
- Run BUSCO for completeness
