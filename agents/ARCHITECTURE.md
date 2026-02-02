# Omics Scientist Agent - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     OMICS SCIENTIST AGENT                         │
│                   (Computational Biologist AI)                    │
└─────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
        ┌───────────────────┐     ┌──────────────────┐
        │   BIO-LOGIC       │     │  TECHNICAL       │
        │   (Reasoning)     │◄───►│  SKILLS          │
        │   Foundation      │     │  (Execution)     │
        └───────────────────┘     └──────────────────┘
                 │                         │
                 │                         │
        ┌────────┴────────┐       ┌────────┴────────┐
        ▼                 ▼       ▼                 ▼
   Hypothesis      Experimental   Data         Analysis
   Formation       Design        Generation    Workflows
```

## Three-Layer Architecture

### Layer 1: Reasoning (Bio-Logic)
**Purpose**: Scientific thinking, hypothesis formation, interpretation

**When Active**:
- BEFORE workflows (justify approach)
- DURING workflows (interpret unexpected results)
- AFTER workflows (derive biological insights)

**Capabilities**:
- Hypothesis formation & testing
- Experimental design
- Causal reasoning
- Evidence evaluation
- Method selection justification
- Result interpretation
- Alternative explanation generation
- Confound identification

**Trigger Keywords**: why, how, explain, interpret, hypothesis, design, reasoning, mechanism, justify, evidence, causal

### Layer 2: Execution (Bio-* Technical Skills)
**Purpose**: Run bioinformatics tools, generate data

**Skill Categories**:
1. **Foundation**: Project setup, database curation
2. **Data Processing**: QC, mapping, filtering
3. **Assembly**: Genome/metagenome assembly
4. **Binning**: MAG recovery
5. **Annotation**: Gene calling, functional annotation, taxonomy
6. **Analysis**: Phylogenomics, pangenomics, structure prediction
7. **Specialized**: Viromics, SSU analysis, HMM searches
8. **Reporting**: Statistical analysis, ML, figures

**Outputs**: Files, tables, trees, structures, QC reports

### Layer 3: Integration (Orchestration)
**Purpose**: Coordinate reasoning + execution in coherent workflows

**Pattern**:
```
User Question
    ↓
Bio-Logic (reason about approach)
    ↓
Technical Skills (execute)
    ↓
Bio-Logic (interpret results)
    ↓
Response to User
```

## Skill Interaction Patterns

### Pattern 1: Method Selection
```
┌──────────────┐
│ User Question│ "Should I use short or long reads?"
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ /bio-logic           │ Evaluate trade-offs:
│                      │ - Cost vs quality
│                      │ - Contiguity needs
│                      │ - Assembly goals
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ RECOMMENDATION       │ "Use long-reads because..."
└──────────────────────┘
```

### Pattern 2: Standard Workflow
```
┌──────────────┐
│ User Request │ "Assemble and annotate genome"
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ /bio-logic           │ Justify assembly strategy
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ /bio-foundation-     │ Project setup
│  housekeeping        │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ /bio-reads-qc-       │ QC + mapping
│  mapping             │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ /bio-assembly-qc     │ Assembly
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ /bio-gene-calling    │ Gene prediction
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ /bio-annotation-     │ Functional annotation
│  taxonomy            │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ /bio-phylogenomics   │ Phylogenetic placement
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ /bio-logic           │ Interpret results:
│                      │ - Phylogenetic position
│                      │ - Metabolic capacity
│                      │ - Ecological role
│                      │ - Evolutionary insights
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ /bio-stats-ml-       │ Final report
│  reporting           │
└──────────────────────┘
```

### Pattern 3: Troubleshooting
```
┌──────────────┐
│ Unexpected   │ "E. coli genes in Archaea MAG"
│ Result       │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ /bio-logic           │ Generate hypotheses:
│                      │ 1. Contamination
│                      │ 2. HGT
│                      │ 3. Misclassification
│                      │ 4. Annotation error
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ /bio-binning-qc      │ Check contamination
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ /bio-phylogenomics   │ Gene phylogeny
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ /bio-logic           │ Evaluate evidence,
│                      │ rank hypotheses
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Conclusion           │ "Most likely: HGT because..."
└──────────────────────┘
```

### Pattern 4: Experimental Design
```
┌──────────────┐
│ User Goal    │ "Prove organism fixes nitrogen"
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│ /bio-logic           │ Design experiment:
│                      │ - Formulate null hypothesis
│                      │ - Define controls
│                      │ - Plan measurements
│                      │ - Calculate power
│                      │ - Identify confounds
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│ Experimental Plan    │ Detailed protocol
└──────────────────────┘
```

## Data Flow

```
                        INPUT
                          │
                ┌─────────┴─────────┐
                ▼                   ▼
          Raw Reads            Assemblies
                │                   │
                ▼                   │
         ┌────────────┐             │
         │   QC       │             │
         │  /bio-reads│             │
         │  -qc-      │             │
         │  mapping   │             │
         └─────┬──────┘             │
               │                    │
               ▼                    │
         ┌────────────┐             │
         │  Assembly  │◄────────────┘
         │  /bio-     │
         │  assembly- │
         │  qc        │
         └─────┬──────┘
               │
               ▼
        ┌─────────────┐
        │  Binning    │ (if metagenome)
        │  /bio-      │
        │  binning-qc │
        └──────┬──────┘
               │
               ▼
        ┌─────────────┐
        │ Gene Calling│
        │ /bio-gene-  │
        │ calling     │
        └──────┬──────┘
               │
        ┌──────┴──────┐
        ▼             ▼
   ┌─────────┐   ┌──────────┐
   │Annotation│  │Structure│
   │/bio-     │  │/bio-    │
   │annotation│  │structure│
   └────┬─────┘  └────┬────┘
        │             │
        └──────┬──────┘
               │
               ▼
        ┌─────────────┐
        │ Phylogeny   │
        │ /bio-       │
        │ phylogenomics│
        └──────┬──────┘
               │
               ▼
        ┌─────────────┐
        │ /bio-logic  │ ← Interpretation
        │ (Reasoning) │
        └──────┬──────┘
               │
               ▼
        ┌─────────────┐
        │  Reporting  │
        │  /bio-stats-│
        │  ml-        │
        │  reporting  │
        └─────────────┘
               │
               ▼
           OUTPUT
```

## Decision Matrix

| User Input Type | First Skill | Follow-up Skills | Final Skill |
|----------------|-------------|------------------|-------------|
| **Question ("why", "how")** | bio-logic | N/A | N/A |
| **Raw reads** | bio-logic → bio-foundation | reads-qc → assembly → genes → annotation | bio-logic → reporting |
| **Assembly (isolate)** | bio-logic | gene-calling → annotation → phylogeny | bio-logic → reporting |
| **Assembly (metagenome)** | bio-logic | binning → gene-calling → annotation | bio-logic → reporting |
| **Genes** | bio-logic | annotation → phylogeny | bio-logic → reporting |
| **Proteins (unknown)** | bio-logic | structure → annotation | bio-logic → reporting |
| **Multiple genomes** | bio-logic | gene-calling → pangenome → phylogeny | bio-logic → reporting |
| **Unexpected result** | bio-logic | (hypothesis-specific) | bio-logic |
| **Experimental design** | bio-logic | N/A | N/A |

## Keyword Recognition System

```
User Input
    │
    ▼
┌───────────────────────┐
│ Keyword Detection     │
└───────┬───────────────┘
        │
        ├─ "why", "how", "explain" ──────► /bio-logic
        │
        ├─ "raw reads", "FASTQ" ─────────► /bio-reads-qc-mapping
        │
        ├─ "assemble", "contigs" ────────► /bio-assembly-qc
        │
        ├─ "binning", "MAGs" ────────────► /bio-binning-qc
        │
        ├─ "annotate", "function" ───────► /bio-annotation-taxonomy
        │
        ├─ "phylogeny", "tree" ──────────► /bio-phylogenomics
        │
        ├─ "viral", "phage" ─────────────► /bio-viromics
        │
        └─ "structure", "AlphaFold" ─────► /bio-structure-annotation
```

## Quality Gates & Checkpoints

```
Workflow Stage          Quality Gate            Action if Failed
────────────────────────────────────────────────────────────────
Read QC                 Q30, <5% adapters       Re-trim, filter
                        ↓
                      PASS? ──NO──► /bio-logic (troubleshoot)
                        │ YES
                        ▼
Assembly                N50 > target            Adjust parameters
                        ↓
                      PASS? ──NO──► /bio-logic (evaluate)
                        │ YES
                        ▼
Binning (if meta)       >50% complete           Refine bins
                        <10% contam
                        ↓
                      PASS? ──NO──► /bio-logic (interpret)
                        │ YES
                        ▼
Gene Calling            ~1 gene/kb              Check assembly
                        ↓
                      PASS? ──NO──► /bio-logic (diagnose)
                        │ YES
                        ▼
Annotation              >70% with hits          Check database
                        ↓
                      PASS? ──NO──► /bio-logic (evaluate)
                        │ YES
                        ▼
Final Report
```

## Agent State Machine

```
                    ┌──────────┐
                    │  IDLE    │
                    └────┬─────┘
                         │
                    User Input
                         │
                    ┌────▼─────────────────┐
                    │  INPUT ANALYSIS      │
                    │  (keyword detection) │
                    └────┬─────────────────┘
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        ┌───────────┐         ┌─────────┐
        │ REASONING │         │TECHNICAL│
        │ MODE      │         │ MODE    │
        │(bio-logic)│         │(bio-*)  │
        └─────┬─────┘         └────┬────┘
              │                    │
              └─────────┬──────────┘
                        │
                   ┌────▼─────┐
                   │SYNTHESIS │
                   │(bio-logic│
                   │interpret)│
                   └────┬─────┘
                        │
                   ┌────▼─────┐
                   │ REPORT   │
                   └────┬─────┘
                        │
                   ┌────▼─────┐
                   │  IDLE    │
                   └──────────┘
```

## Skill Dependency Graph

```
                     bio-logic (Universal - can be called anytime)
                           │
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
bio-foundation      (reasoning layer)    (interpretation)
        │
        ▼
bio-reads-qc-mapping
        │
        ├──────────────┐
        ▼              ▼
bio-assembly-qc    Direct Mapping
        │              Analysis
        ├────────┐
        ▼        ▼
   bio-binning-qc  bio-gene-calling
        │              │
        └──────┬───────┘
               ▼
        bio-gene-calling
               │
        ┌──────┴──────────────┐
        ▼                     ▼
bio-annotation-taxonomy  bio-structure-annotation
        │                     │
        ├─────────────────────┤
        │                     │
        ▼                     ▼
bio-phylogenomics      bio-protein-clustering
        │                     │
        └──────┬──────────────┘
               ▼
           bio-logic
        (interpretation)
               │
               ▼
     bio-stats-ml-reporting
```

## Agent Capabilities Matrix

| Capability | Bio-Logic | Technical Skills | Integration |
|-----------|-----------|------------------|-------------|
| **Hypothesis Formation** | ✓✓✓ | - | ✓ |
| **Experimental Design** | ✓✓✓ | - | ✓ |
| **Method Selection** | ✓✓✓ | - | ✓ |
| **Data Generation** | - | ✓✓✓ | ✓ |
| **Quality Control** | ✓ | ✓✓✓ | ✓ |
| **Result Interpretation** | ✓✓✓ | ✓ | ✓ |
| **Causal Reasoning** | ✓✓✓ | - | ✓ |
| **Evidence Evaluation** | ✓✓✓ | - | ✓ |
| **Alternative Explanations** | ✓✓✓ | - | ✓ |
| **Confound Identification** | ✓✓✓ | - | ✓ |
| **Mechanistic Models** | ✓✓✓ | ✓ | ✓ |
| **Prediction** | ✓✓✓ | ✓ | ✓ |

✓✓✓ = Primary capability
✓ = Supporting capability
- = Not applicable

## Information Flow

```
┌─────────────┐
│ User Input  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│ Agent Understanding Layer   │
│ - Parse intent              │
│ - Identify keywords         │
│ - Classify request type     │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Reasoning Layer (bio-logic) │
│ - Evaluate approach         │
│ - Justify decisions         │
│ - Formulate hypotheses      │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Execution Layer (bio-*)     │
│ - Run bioinformatics tools  │
│ - Generate data             │
│ - Validate quality          │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Interpretation (bio-logic)  │
│ - Synthesize results        │
│ - Derive biological insights│
│ - Generate new hypotheses   │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Response to User            │
│ - Summary of findings       │
│ - Biological interpretation │
│ - Recommendations           │
└─────────────────────────────┘
```

## Bio-Logic Coverage Map

Bio-logic is integrated at **every critical decision point**:

```
Project Start           → bio-logic (justify overall approach)
Method Selection        → bio-logic (evaluate options)
Before Each Workflow    → bio-logic (plan strategy)
Quality Gate Failure    → bio-logic (troubleshoot)
Unexpected Result       → bio-logic (evaluate hypotheses)
After Each Workflow     → bio-logic (interpret findings)
Final Synthesis         → bio-logic (biological insights)
```

## Conclusion

The architecture ensures:
1. **Scientific reasoning** guides all decisions (bio-logic)
2. **Technical execution** generates reliable data (bio-* skills)
3. **Seamless integration** creates coherent workflows
4. **Quality gates** ensure rigor at every step
5. **Biological interpretation** transforms data into knowledge

