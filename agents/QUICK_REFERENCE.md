# Omics Scientist Agent - Quick Reference

## One-Line Decision Guide

```
Question?  → bio-logic (reason about approach)
Raw Reads? → QC+Map → Assembly? → Genes → Annotation → Phylogeny → bio-logic → Report
Contigs?   → Bins → Genes → Annotation → Phylogeny → bio-logic → Report
Proteins?  → Annotation/Structure → Phylogeny → bio-logic → Report
```

**ALWAYS use bio-logic for: why, how, explain, interpret, design, hypothesis**

## Skill Selection Matrix

| You Have | You Want | Use This Skill |
|----------|----------|----------------|
| **Question/Problem** | **Scientific reasoning, interpretation** | **`/bio-logic`** |
| **Results** | **Biological interpretation** | **`/bio-logic`** |
| **Idea** | **Experimental design** | **`/bio-logic`** |
| FASTQ files | Quality metrics, mapped reads | `/bio-reads-qc-mapping` |
| Reads | Genome assembly | `/bio-assembly-qc` |
| Metagenome assembly | MAGs (bins) | `/bio-binning-qc` |
| Contigs/genomes | Gene sequences | `/bio-gene-calling` |
| Gene sequences | Function + taxonomy | `/bio-annotation-taxonomy` |
| Sequences/genomes | Phylogenetic tree | `/bio-phylogenomics` |
| Multiple genomes | Pangenome analysis | `/bio-protein-clustering-pangenome` |
| Protein sequences | 3D structures | `/bio-structure-annotation` |
| Contigs | Viral sequences | `/bio-viromics` |
| 16S/18S sequences | rRNA phylogeny | `/ssu-sequence-analysis` |
| Protein sequences | HMM/homology hits | `/hmm-mmseqs-workflow` |
| Messy FASTA files | Clean database | `/fasta-database-curator` |
| Reads | Filtered/stats | `/bb-skill` |
| Results | Statistical report | `/bio-stats-ml-reporting` |
| Error logs | Diagnosis | `/pipeline-debugger` |
| Nothing yet | Project setup | `/bio-foundation-housekeeping` |

## Keyword Triggers

| Keywords in User Query | Auto-Trigger Skill |
|------------------------|-------------------|
| **"why", "how", "explain", "interpret", "hypothesis", "design experiment", "reasoning", "mechanism", "because", "justify", "alternative", "conclude", "suggest", "evidence", "causal"** | **`/bio-logic`** |
| "raw reads", "FASTQ", "QC", "trim" | `/bio-reads-qc-mapping` |
| "assemble", "contigs", "N50", "QUAST" | `/bio-assembly-qc` |
| "binning", "MAGs", "CheckM" | `/bio-binning-qc` |
| "gene calling", "ORF", "Prodigal" | `/bio-gene-calling` |
| "annotate", "BLAST", "KEGG", "taxonomy" | `/bio-annotation-taxonomy` |
| "phylogeny", "tree", "alignment" | `/bio-phylogenomics` |
| "16S", "18S", "rRNA" | `/ssu-sequence-analysis` |
| "pangenome", "orthologs", "core genome" | `/bio-protein-clustering-pangenome` |
| "AlphaFold", "structure", "PDB" | `/bio-structure-annotation` |
| "viral", "phage", "VirSorter" | `/bio-viromics` |
| "HMM", "MMseqs2", "protein family" | `/hmm-mmseqs-workflow` |
| "deduplicate", "clean FASTA" | `/fasta-database-curator` |
| "BBMap", "dedupe", "k-mer" | `/bb-skill` |
| "report", "statistics", "figures" | `/bio-stats-ml-reporting` |
| "failed", "error", "debug" | `/pipeline-debugger` |
| "new project", "setup" | `/bio-foundation-housekeeping` |

## Quality Gates

| Step | Minimum Acceptable | Action if Failed |
|------|-------------------|------------------|
| Read QC | Q30, <5% adapters | Re-trim, filter |
| Coverage | >30x bacteria, >10x metagenome | Get more data or warn |
| Assembly N50 | >50kb bacteria, >5kb metagenome | Adjust parameters |
| MAG completeness | >50% draft, >90% HQ | Improve binning |
| MAG contamination | <10% draft, <5% HQ | Refine bins |
| Gene density | ~1 gene/kb bacteria | Check assembly |
| Annotation rate | >70% with hits | Check database |

## Common Workflows (Linear)

### 1. Bacterial Isolate (Start to Finish)
```bash
/bio-logic (reason about approach)
  ↓
/bio-foundation-housekeeping
  ↓
/bio-reads-qc-mapping (FASTQ → BAM + QC)
  ↓
/bio-assembly-qc (Reads → Contigs)
  ↓
/bio-gene-calling (Contigs → Genes)
  ↓
/bio-annotation-taxonomy (Genes → Functions)
  ↓
/bio-phylogenomics (Genome → Tree)
  ↓
/bio-logic (interpret results, formulate hypotheses)
  ↓
/bio-stats-ml-reporting (Results → Report)
```

### 2. Metagenome MAG Recovery
```bash
/bio-logic (design binning strategy, define quality gates)
  ↓
/bio-foundation-housekeeping
  ↓
/bio-reads-qc-mapping (if raw reads)
  ↓
/bio-assembly-qc (if no assembly)
  ↓
/bio-binning-qc (Contigs → MAGs)
  ↓
/bio-gene-calling (MAGs → Genes)
  ↓
/bio-annotation-taxonomy (Genes → Functions)
  ↓
/bio-phylogenomics (MAGs → Tree)
  ↓
/bio-logic (interpret ecology, metabolic roles, novelty)
  ↓
/bio-protein-clustering-pangenome (optional)
  ↓
/bio-stats-ml-reporting (Results → Report)
```

### 3. Viral Metagenome
```bash
/bio-viromics (Contigs → Viral sequences)
  ↓
/bio-gene-calling (Viral contigs → Genes)
  ↓
/bio-annotation-taxonomy (Genes → VOGs)
  ↓
/bio-phylogenomics (Viral genes → Tree)
  ↓
/bio-stats-ml-reporting (Results → Report)
```

### 4. Comparative Genomics
```bash
/bio-gene-calling (All genomes → Genes)
  ↓
/bio-protein-clustering-pangenome (Genes → Orthogroups)
  ↓
/bio-phylogenomics (Core genes → Tree)
  ↓
/bio-annotation-taxonomy (Accessory genes → Functions)
  ↓
/bio-stats-ml-reporting (Pangenome → Report)
```

### 5. Structure-Function
```bash
/bio-structure-annotation (Proteins → PDB)
  ↓
/hmm-mmseqs-workflow (Proteins → Homologs)
  ↓
/bio-annotation-taxonomy (optional, complementary)
  ↓
/bio-stats-ml-reporting (Structures → Report)
```

## Decision Tree (If-Then)

```
IF user_says("why" OR "how" OR "explain" OR "interpret")
  THEN use(/bio-logic)

IF user_asks("should I use X or Y?")
  THEN use(/bio-logic) for method selection reasoning

IF user_says("I have raw reads")
  AND NOT urgent
    THEN first(/bio-logic) to reason about approach
    THEN start_with(/bio-reads-qc-mapping)

IF user_says("I have an assembly")
  AND data_type == "metagenome"
    THEN start_with(/bio-binning-qc)
  AND data_type == "isolate"
    THEN start_with(/bio-gene-calling)

IF user_says("I have contigs") AND wants("find viruses")
  THEN start_with(/bio-viromics)

IF user_says("I have proteins") AND wants("structure")
  THEN start_with(/bio-structure-annotation)

IF user_says("I have proteins") AND wants("function")
  THEN start_with(/bio-annotation-taxonomy)

IF user_says("I have genomes") AND wants("compare")
  THEN start_with(/bio-protein-clustering-pangenome)

IF user_says("failed") OR "error" OR "debug"
  THEN start_with(/pipeline-debugger)

IF user_says("new project")
  THEN start_with(/bio-foundation-housekeeping)

IF results_are_unexpected
  THEN use(/bio-logic) to evaluate hypotheses

IF after_any_workflow_completes
  THEN use(/bio-logic) to interpret findings biologically
```

## Parameter Quick Guide

| Tool Type | Key Parameters | When to Adjust |
|-----------|----------------|----------------|
| Read QC | Quality threshold (Q30) | High error rate data |
| Assembly | k-mer size | Depends on coverage, read length |
| Assembly | --meta flag | ALWAYS for metagenomes |
| Binning | Min contig length (1500bp) | Low coverage metagenomes |
| Gene calling | --meta flag | Metagenomes (shorter genes) |
| Annotation | e-value (1e-5) | Very divergent organisms |
| Phylogeny | Bootstrap (1000) | Publication-quality trees |
| Phylogeny | Model selection (AUTO) | Let tool choose |

## Parallel Execution Opportunities

| Scenario | Parallelizable | How |
|----------|----------------|-----|
| Multiple samples | Yes | One workflow per sample |
| Gene calling on multiple genomes | Yes | One job per genome |
| Annotation of multiple MAGs | Yes | One job per MAG |
| Structure prediction | Yes | One job per protein |
| QC reports | Yes | Per-sample QC |

## Expected Runtime (Rough Estimates)

| Task | Small Dataset | Large Dataset |
|------|---------------|---------------|
| Read QC | 5-10 min | 30-60 min |
| Assembly (isolate) | 10-30 min | 1-3 hours |
| Assembly (metagenome) | 1-3 hours | 6-24 hours |
| Binning | 30 min - 2 hours | 4-12 hours |
| Gene calling | 5-15 min | 30-60 min |
| Annotation | 30 min - 2 hours | 4-12 hours |
| Phylogeny | 30 min - 2 hours | 6-24 hours |
| Structure (AlphaFold) | 10-20 min per protein | - |
| CheckM2 | 10-30 min | 1-3 hours |

Small = <1Gbp total data, Large = >10Gbp or >100 genomes

## Resource Requirements (Minimum)

| Task | RAM | Cores | Disk |
|------|-----|-------|------|
| Read QC | 4 GB | 4 | 2x input size |
| Assembly (isolate) | 8 GB | 8 | 10x input size |
| Assembly (metagenome) | 128 GB | 16 | 20x input size |
| Binning | 32 GB | 8 | 5x assembly size |
| Gene calling | 4 GB | 4 | 2x input size |
| Annotation | 16 GB | 8 | 5x input size |
| CheckM2 | 32 GB | 16 | 100 GB (database) |
| GTDB-Tk | 320 GB | 8 | 80 GB (database) |
| AlphaFold | 16 GB | 8 (GPU recommended) | 2.3 TB (database) |

## Common Errors & Fixes

| Error Message | Likely Cause | Fix |
|---------------|--------------|-----|
| "Out of memory" | Insufficient RAM | Reduce threads, use --meta mode |
| "Empty alignment" | No homologs found | Check sequence quality, use different database |
| "Low coverage" | Insufficient sequencing | Get more data or adjust expectations |
| "High contamination" | Co-assembly issues | Refine bins, use DAS Tool |
| "No bins produced" | Assembly too fragmented | Improve assembly or relax min contig length |
| "Gene calling failed" | Wrong mode (meta vs isolate) | Check --meta flag |
| "GTDB-Tk failed" | Database not found | Download GTDB database |

## Output File Guide

| Suffix | Content | Tool |
|--------|---------|------|
| `.fasta`, `.fa`, `.fna` | Nucleotide sequences | Various |
| `.faa` | Protein sequences | Gene calling |
| `.gff`, `.gff3` | Gene annotations | Gene calling |
| `.bam`, `.sam` | Aligned reads | Mapping |
| `.nwk`, `.treefile` | Phylogenetic tree | Phylogeny |
| `.aln` | Multiple alignment | Phylogeny |
| `.tsv` | Table (annotations, stats) | Various |
| `.html` | QC report | FastQC, MultiQC |
| `.pdf` | Figures | Reporting |
| `.pdb` | Protein structure | Structure prediction |

## When to Use `/get-available-resources`

Before starting:
- Large metagenome assembly (>100GB reads)
- Hundreds of genome annotations
- Structure prediction batch jobs
- GTDB-Tk (needs 320GB RAM)
- Long phylogenies (>1000 sequences)

## Integration with Other Omics Tools

| Task | Primary Skill | Secondary Skill |
|------|---------------|-----------------|
| Get JGI reference data | `/querying-jgi-lakehouse` | Then bio-* skills |
| Explore complex result files | `/exploratory-data-analysis` | After bio-* skills |
| Write manuscript | `/scientific-writing` | After `/bio-stats-ml-reporting` |
| Literature review | `/literature-review` | Before starting |
| Statistical tests | `/statistical-analysis` | With `/bio-stats-ml-reporting` |
| Custom plots | `/matplotlib` | After `/bio-stats-ml-reporting` |

## Agent Invocation

```bash
# Option 1: Direct invocation
claude --agent /path/to/omics-scientist.md

# Option 2: Copy to user dir
cp omics-scientist.md ~/.claude/agents/
claude --agent omics-scientist

# Option 3: In conversation
@agents/omics-scientist [your request]
```

## Remember

1. **USE BIO-LOGIC FOR ALL REASONING** (why, how, explain, interpret)
2. **Always start with project setup** (`/bio-foundation-housekeeping`)
3. **QC before analysis** (garbage in = garbage out)
4. **Validate at each step** (quality gates)
5. **Use appropriate mode** (--meta for metagenomes)
6. **Check resources first** (for big jobs)
7. **Trust the skills** (don't write custom scripts)
8. **Provide biological context** (helps parameter selection)
9. **Ask for interpretations** (bio-logic explains biology)
10. **Challenge assumptions** (request alternative explanations)

## Bio-Logic Quick Examples

### When to use bio-logic:

**Before Analysis:**
- "Should I use short or long reads?" → `/bio-logic`
- "What assembly strategy for this metagenome?" → `/bio-logic`
- "How many replicates do I need?" → `/bio-logic`

**During Analysis:**
- "Why is my N50 so low?" → `/bio-logic`
- "What does this contamination score mean?" → `/bio-logic`
- "Should I trust this bin?" → `/bio-logic`

**After Analysis:**
- "What do these annotations suggest?" → `/bio-logic`
- "Why are these organisms co-occurring?" → `/bio-logic`
- "What's the biological significance?" → `/bio-logic`

**Unexpected Results:**
- "Why E. coli genes in my archaeal MAG?" → `/bio-logic`
- "How to explain this phylogenetic placement?" → `/bio-logic`
- "Is this contamination or real?" → `/bio-logic`

