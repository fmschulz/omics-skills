# Omics Scientist Agent - Example Usage

This document provides real-world examples of using the omics-scientist agent.

## Example 1: De Novo Bacterial Genome Assembly & Annotation

### Scenario
You have Illumina paired-end reads from a novel Bacillus isolate and want a complete genome analysis.

### Input Files
```
data/
├── sample_R1.fastq.gz
└── sample_R2.fastq.gz
```

### Conversation

```
You: I have Illumina paired-end reads from a Bacillus isolate in data/sample_R*.fastq.gz.
     Please perform complete genome assembly and annotation.

Omics Scientist:
I'll perform a complete bacterial genome workflow:

0. Scientific Reasoning & Strategy
   → /bio-logic
   - Justify assembly approach (single isolate = non-meta mode)
   - Determine QC thresholds based on downstream goals
   - Plan validation strategy for assembly quality

1. Project Setup
   → /bio-foundation-housekeeping
   Creates: project structure, conda environments, data catalog

2. Read QC & Quality Assessment
   → /bio-reads-qc-mapping
   - FastQC/MultiQC for quality metrics
   - Estimate genome coverage
   - Check for contamination

3. Genome Assembly
   → /bio-assembly-qc
   - SPAdes assembly optimized for bacterial isolate
   - QUAST for assembly statistics
   - N50, L50, genome completeness

4. Gene Calling
   → /bio-gene-calling
   - Prodigal for ORF prediction
   - tRNA/rRNA prediction

5. Functional Annotation & Taxonomy
   → /bio-annotation
   - DIAMOND against UniProt
   - KEGG/COG functional categories
   - GTDB-Tk for taxonomy placement

6. Phylogenetic Analysis
   → /bio-phylogenomics
   - Extract marker genes
   - Phylogenetic placement in Bacillus tree

7. Biological Interpretation
   → /bio-logic
   - Interpret phylogenetic placement (closest relatives)
   - Infer metabolic capacity from annotations
   - Formulate hypotheses about ecological niche
   - Identify unique genomic features

8. Final Report
   → /bio-stats-ml-reporting
   - Assembly statistics
   - Annotation summary
   - Taxonomic assignment
   - Publication-ready figures

Proceeding with step 1...
```

### Expected Outputs

```
results/
├── 01_qc/
│   ├── multiqc_report.html
│   └── coverage_estimate.txt
├── 02_assembly/
│   ├── contigs.fasta
│   ├── scaffolds.fasta
│   └── quast_report/
├── 03_genes/
│   ├── genes.fna
│   ├── genes.faa
│   └── genes.gff
├── 04_annotation/
│   ├── functional_annotation.tsv
│   ├── kegg_pathways.txt
│   └── gtdbtk_taxonomy.tsv
├── 05_phylogeny/
│   ├── marker_genes.aln
│   └── phylogenetic_tree.nwk
└── final_report.pdf
```

---

## Example 2: Metagenomic MAG Recovery from Soil Sample

### Scenario
You have an existing metagenomic assembly and want to recover high-quality metagenome-assembled genomes (MAGs).

### Input Files
```
data/
├── metagenome_contigs.fasta
├── reads_R1.fastq.gz
└── reads_R2.fastq.gz
```

### Conversation

```
You: I have a soil metagenome assembly (data/metagenome_contigs.fasta) and the original
     reads. Please recover and annotate high-quality MAGs.

Omics Scientist:
Perfect! I'll perform MAG recovery and characterization:

0. Scientific Reasoning & Strategy
   → /bio-logic
   - Evaluate assembly fragmentation vs binning success likelihood
   - Choose binning algorithms based on community complexity
   - Define MAG quality thresholds (draft vs HQ)
   - Plan downstream analysis based on research questions

1. Binning & Refinement
   → /bio-binning-qc
   - Map reads back to contigs for coverage
   - MetaBAT2, MaxBin2, CONCOCT binning
   - DAS Tool refinement
   - CheckM2 quality assessment
   - Filter for HQ MAGs (>90% complete, <5% contamination)

2. Gene Calling per MAG
   → /bio-gene-calling
   - Prodigal for each HQ MAG

3. Functional Annotation
   → /bio-annotation
   - Annotate genes in all MAGs
   - GTDB-Tk for taxonomy
   - KEGG metabolic reconstruction

4. Phylogenomic Placement
   → /bio-phylogenomics
   - Place MAGs in GTDB reference tree
   - Identify novelty

5. Comparative Analysis
   → /bio-protein-clustering-pangenome
   - Compare MAGs within similar taxa
   - Core/accessory gene analysis

6. Biological Interpretation
   → /bio-logic
   - What does MAG taxonomy reveal about soil community?
   - What metabolic functions suggest about ecosystem processes?
   - Are there novel lineages? What's their significance?
   - What ecological interactions can we infer?
   - Formulate testable hypotheses

7. Final Report
   → /bio-stats-ml-reporting
   - MAG statistics table
   - Taxonomic distribution
   - Metabolic potential summary
   - Phylogenetic placement figures

Starting with binning...
```

### Expected Outputs

```
results/
├── bins/
│   ├── bin.001.fa (HQ MAG)
│   ├── bin.002.fa (HQ MAG)
│   ├── ...
│   └── bin_quality.tsv
├── checkm2/
│   └── quality_report.tsv
├── genes/
│   ├── bin.001.genes.faa
│   ├── bin.002.genes.faa
│   └── ...
├── annotation/
│   ├── bin.001.annotations.tsv
│   ├── gtdbtk_taxonomy.tsv
│   └── kegg_pathways_per_bin.tsv
├── phylogeny/
│   ├── gtdb_placement.nwk
│   └── mag_tree.pdf
├── pangenome/
│   ├── orthogroups.tsv
│   └── pangenome_matrix.tsv
└── MAG_report.pdf
```

---

## Example 3: Viral Metagenome Analysis

### Scenario
Analyze a viral fraction from an ocean sample to identify and characterize viral populations.

### Input Files
```
data/
├── viral_assembly.fasta
└── viral_reads.fastq.gz
```

### Conversation

```
You: I have a viral metagenome assembly from an ocean sample. Please identify and
     characterize viral contigs.

Omics Scientist:
Great! I'll perform comprehensive viral metagenome analysis:

1. Viral Contig Identification
   → /bio-viromics
   - VirSorter2 for viral sequence detection
   - VIBRANT for viral prediction
   - CheckV for quality assessment
   - Taxonomy with vContact2

2. Gene Calling
   → /bio-gene-calling
   - Prodigal (meta mode) for viral genes
   - Specialized viral gene callers

3. Functional Annotation
   → /bio-annotation
   - DIAMOND against viral protein databases
   - VOG (Viral Orthologous Groups)
   - Identify AMGs (auxiliary metabolic genes)

4. Phylogenetic Analysis
   → /bio-phylogenomics
   - Viral marker gene phylogeny
   - Compare to RefSeq viral genomes

5. Clustering & Taxonomy
   → /bio-protein-clustering-pangenome
   - Cluster viral genomes (95% ANI)
   - Identify viral populations

6. Final Report
   → /bio-stats-ml-reporting
   - Viral diversity metrics
   - Taxonomic composition
   - AMG functional potential
   - Host prediction (if CRISPR spacers available)

Beginning viral identification...
```

---

## Example 4: 16S rRNA Amplicon Analysis

### Scenario
Analyze 16S rRNA sequences from a novel bacterial isolate to determine phylogenetic placement.

### Input Files
```
data/
├── 16S_sequence.fasta
```

### Conversation

```
You: I have a 16S rRNA sequence from a novel Actinobacteria isolate. Where does it
     place phylogenetically?

Omics Scientist:
I'll place your 16S sequence using phylogenomic alignment and tree building:

→ /bio-phylogenomics
This will:
1. Validate your 16S sequence quality
2. Align against reference sequences
3. Build a phylogenetic tree with bootstrap support
4. Report closest neighbors and novelty signals

Processing your sequence...
```

---

## Example 5: Comparative Genomics of Pathogen Outbreak

### Scenario
You have 100 E. coli genomes from a suspected outbreak and need to determine relatedness and identify virulence factors.

### Input Files
```
data/genomes/
├── strain001.fasta
├── strain002.fasta
├── ...
└── strain100.fasta
```

### Conversation

```
You: I have 100 E. coli genomes from a suspected outbreak. Please perform comparative
     genomics to assess relatedness and identify virulence factors.

Omics Scientist:
I'll perform comprehensive outbreak comparative genomics:

1. Gene Calling (Parallel)
   → /bio-gene-calling
   - Prodigal on all 100 genomes (parallel execution)
   - Ensures consistent gene prediction

2. Pangenome Analysis
   → /bio-protein-clustering-pangenome
   - OrthoFinder for ortholog clustering
   - Core genome (genes in all strains)
   - Accessory genome (variable genes)
   - Singleton analysis

3. Core Genome Phylogeny
   → /bio-phylogenomics
   - Concatenated core gene alignment
   - Maximum likelihood tree (IQ-TREE)
   - Bootstrap support values
   - Identifies outbreak cluster

4. Functional Annotation
   → /bio-annotation
   - Annotate all genes
   - Focus on virulence-associated families
   - Antimicrobial resistance genes (as available)

5. Domain-based Screening
   → /bio-annotation
   - Pfam/InterPro domain scans
   - Identify pathogenicity-related domains

6. Comparative Report
   → /bio-stats-ml-reporting
   - SNP distance matrix
   - Phylogenetic tree with metadata
   - Virulence factor presence/absence
   - AMR gene distribution
   - Statistical association with outbreak

This will take some time with 100 genomes. Proceeding with parallel gene calling...
```

---

## Example 6: Protein Structure & Function Prediction

### Scenario
You have hypothetical proteins from a MAG that lack homology to known proteins.

### Input Files
```
data/
└── hypothetical_proteins.faa
```

### Conversation

```
You: I have 15 hypothetical proteins with no BLAST hits. Can we predict structures
     and infer function?

Omics Scientist:
Absolutely! I'll use structure-based annotation for these hypothetical proteins:

1. Structure Prediction
   → /bio-structure-annotation
   - ESMFold/AlphaFold structure prediction
   - Confidence scores per residue
   - Generate PDB files

2. Structure-based Annotation
   → /bio-structure-annotation (continued)
   - Search against PDB database (Foldseek)
   - Identify structural homologs
   - Functional inference from structure

3. Complementary Sequence Analysis
   → /bio-annotation
   - Domain-based annotation (InterPro/Pfam)
   - Distant homology hints from profile matches

4. Domain Architecture
   → /bio-annotation
   - Pfam domain annotation
   - Conserved domain database search

5. Final Report
   → /bio-stats-ml-reporting
   - Structure-function predictions
   - Confidence assessments
   - Domain architectures
   - PyMOL structure figures

Starting structure prediction (this may take 10-20 minutes)...
```

---

## Example 7: Troubleshooting Failed Pipeline

### Scenario
Your previous metagenomic analysis failed during the binning step.

### Conversation

```
You: My binning job failed with this error: [error log]. Can you help?

Omics Scientist:
I'll diagnose the pipeline failure by reviewing logs and inputs:
1. Parse the error logs
2. Trace the error through pipeline phases
3. Identify the root cause
4. Check resource constraints (memory, disk)
5. Validate input file formats
6. Suggest fixes with specific commands

After diagnosis, I can:
- Re-run the failed step with corrected parameters
- Resume the pipeline from the last successful checkpoint
- Modify workflow to avoid the issue

Analyzing your error log...
```

---

## Example 8: Taxonomy Update Scan

### Scenario
You need the most recent GTDB and NCBI taxonomy changes and their pipeline impact.

### Conversation

```
You: What changed recently in GTDB vs NCBI taxonomy, and will it break my pipeline?

Omics Scientist:
I'll run a versioned update scan:

→ /tracking-taxonomy-updates
This will:
1. Pull authoritative release notes
2. Summarize changes with dates and IDs
3. Flag taxid merges/deletions and naming changes
4. Provide action items for pipeline compatibility

Compiling a versioned summary now...
```

---

## Example 9: Scientific Reasoning & Interpretation (bio-logic)

### Scenario
Unexpected results require interpretation and hypothesis formation.

### Conversation

```
You: I found genes for nitrogen fixation in a MAG classified as E. coli. How is this possible?

Omics Scientist:
This requires scientific reasoning to evaluate alternative explanations:

→ /bio-logic
I'll systematically evaluate hypotheses:

**Hypothesis 1: Contamination**
- Lab contamination (unlikely if controls clean)
- Reagent contamination (check DNA extraction kit lot)
- Computational contamination (binning error)
Evidence needed: CheckM contamination score, tetranucleotide frequency, GC content deviation

**Hypothesis 2: Horizontal Gene Transfer (HGT)**
- E. coli can acquire nitrogen fixation genes via HGT
- Look for: mobility genes nearby, GC content anomaly, phylogenetic incongruence
Evidence: Gene synteny, phylogeny of nif genes vs 16S, insertion sites

**Hypothesis 3: Misclassification**
- MAG may not actually be E. coli
- Taxonomic assignment based on partial 16S or few markers
Evidence: ANI to E. coli genomes, GTDB-Tk full classification, marker gene consistency

**Hypothesis 4: Novel E. coli Lineage**
- Rare but precedented (e.g., photosynthetic E. coli discovered)
Evidence: Multiple independent samples, isolation confirmation, functional validation

**Recommended Next Steps:**
1. /bio-binning-qc refinement (check contamination metrics)
2. /bio-phylogenomics (nif gene phylogeny + whole genome tree)
3. /bio-annotation (examine genomic context of nif genes)
4. /bio-logic (synthesize evidence, rank hypotheses by likelihood)

Based on reasoning, most likely explanations in order:
1. Binning error (check first - easiest to rule out)
2. HGT (biologically plausible)
3. Misclassification (check taxonomy)
4. Novel lineage (requires extraordinary evidence)

Shall we investigate systematically?
```

### Example 10: Experimental Design with bio-logic

```
You: I want to prove that this organism can degrade plastics. How should I design the experiment?

Omics Scientist:
→ /bio-logic

**Experimental Design Reasoning:**

**1. Hypothesis Formulation**
- Null: Organism cannot degrade plastic
- Alternative: Organism degrades plastic at measurable rate

**2. Evidence Hierarchy**
- Genomic (weakest): Presence of putative plastic-degrading genes
- Transcriptomic (weak): Gene expression in plastic presence
- Proteomic (moderate): Protein production
- Biochemical (strong): Enzyme activity assays
- Phenotypic (strongest): Plastic mass loss, growth on plastic

**3. Experimental Design**
Controls needed:
- Negative: Sterile media + plastic (abiotic degradation)
- Negative: Organism without plastic (baseline metabolism)
- Positive: Known plastic degrader (method validation)

Treatments:
- Test organism + plastic (multiple plastic types)
- Test organism + plastic degradation products (confirm utilization)

Measurements:
- Plastic mass loss (gravimetric)
- Plastic chemical structure (FTIR, NMR)
- Degradation products (GC-MS, LC-MS)
- Growth (CFU, OD600)
- Gene expression (RT-qPCR of putative genes)
- Enzyme activity (purified proteins)

Replication:
- Biological replicates: n≥3 independent cultures
- Technical replicates: n≥2 per measurement
- Power analysis: achieve 80% power to detect 20% mass loss

Time course:
- Sample at: 0, 1, 3, 7, 14, 30 days
- Track degradation kinetics

**4. Confounds to Control**
- Temperature (affects plastic properties)
- Media composition (carbon source availability)
- Plastic surface area (standardize)
- Biofilm formation (can complicate interpretation)
- Contamination by other degraders

**5. Statistical Analysis**
- ANOVA for multi-group comparison
- Regression for degradation kinetics
- Correct for multiple testing

Would you like me to help design specific protocols or analyze genomic evidence first?
```

### Example 11: Method Selection Reasoning

```
You: Should I use short-read or long-read sequencing for my metagenome project?

Omics Scientist:
→ /bio-logic

**Decision Requires Reasoning About:**

**Project Goals Analysis:**
1. What's the primary objective?
   - Draft MAGs? → Short-reads sufficient
   - Complete MAG genomes? → Long-reads essential
   - Strain variation? → Long-reads beneficial
   - Functional potential only? → Short-reads fine

**Trade-off Analysis:**

| Factor | Short-read (Illumina) | Long-read (Nanopore/PacBio) |
|--------|----------------------|----------------------------|
| Cost | $500-1000/sample | $1500-3000/sample |
| Throughput | Very high (50-100Gb) | Moderate (20-50Gb) |
| Accuracy | 99.9% | 95-99.5% |
| Assembly contiguity | Fragmented (N50: 1-50kb) | Contiguous (N50: 100kb-1Mb) |
| Strain resolution | Poor | Excellent |
| GC bias | Moderate | Low |
| Repeat resolution | Poor | Excellent |
| DNA input | Low (1-10ng) | High (1-5μg) |

**Recommendation Logic:**
IF goal = draft MAGs for diversity survey
   AND budget limited
   AND DNA limited
   THEN use short-read

IF goal = complete genomes
   OR need to resolve strain variation
   OR highly repetitive genomes expected
   THEN use long-read

IF budget allows:
   BEST = hybrid approach (short + long)
   - Short-read for depth/accuracy
   - Long-read for scaffolding
   - Get benefits of both

**For your metagenome:**
Can you clarify:
1. What's your main research question?
2. What's your budget per sample?
3. How much DNA can you extract?
4. Do you need complete genomes or drafts?

This will guide the optimal sequencing strategy.
```

---

## Tips for Effective Agent Interaction

### 1. Be Specific About Data Type
```
✅ "I have Illumina paired-end reads (2x150bp)"
❌ "I have sequencing data"
```

### 2. Mention Biological Context
```
✅ "Thermophilic archaeon from hot spring, high GC content expected"
❌ "Here's a genome"
```

### 3. State Your Goals Clearly
```
✅ "I need high-quality MAGs (>90% complete, <5% contamination) for metabolic reconstruction"
❌ "Do metagenomics"
```

### 4. Provide File Paths Explicitly
```
✅ "/data/project/reads_R1.fastq.gz"
❌ "the reads file"
```

### 5. Mention Computational Constraints
```
✅ "I have 32GB RAM and 8 cores available"
❌ (Assumes unlimited resources)
```

### 6. Ask for Explanations
```
✅ "Why did you choose MetaBAT2 over CONCOCT?"
✅ "What does this N50 value mean for assembly quality?"
```

### 7. Request Checkpoint Reviews
```
✅ "Show me QC results before proceeding to assembly"
✅ "Let me review the bin quality before annotation"
```

---

## Common Workflows Quick Reference

| Task | Primary Skill | Follow-up Skills |
|------|--------------|------------------|
| Bacterial genome from reads | bio-reads-qc-mapping | assembly-qc → gene-calling → bio-annotation |
| MAG recovery | bio-binning-qc | gene-calling → bio-annotation → phylogenomics |
| Viral metagenomics | bio-viromics | gene-calling → bio-annotation |
| 16S phylogeny | bio-phylogenomics | - |
| Comparative genomics | bio-protein-clustering-pangenome | phylogenomics → stats-ml-reporting |
| Structure prediction | bio-structure-annotation | bio-annotation |
