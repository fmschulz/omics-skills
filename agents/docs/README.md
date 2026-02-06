# Omics Skills Agents

This directory contains specialized agent personas for bioinformatics and omics data analysis.

## Available Agents

### Omics Scientist (`omics-scientist.md`)

Expert computational biologist specializing in genomics, metagenomics, phylogenomics, and comparative genomics. Automatically selects and orchestrates the appropriate bio-* skills for complex omics workflows.

**Use this agent when:**
- Processing raw sequencing data (Illumina, Nanopore, PacBio)
- Assembling genomes or metagenomes
- Recovering MAGs from metagenomic data
- Performing functional annotation and taxonomy assignment
- Building phylogenetic trees
- Conducting comparative genomics and pangenome analysis
- Analyzing viral sequences
- Predicting protein structures
- Any multi-step bioinformatics workflow

### DataViz Artist (`dataviz-artist.md`)

Expert data visualization specialist combining design principles with technical execution to create compelling, beautiful, and actionable visualizations. Automatically selects appropriate tools for notebooks, static plots, or interactive dashboards.

**Use this agent when:**
- Creating publication-quality static figures
- Building interactive dashboards for data exploration
- Developing reproducible analysis notebooks
- Web scraping data for visualization
- Any data visualization task requiring design expertise

### Science Writer (`science-writer.md`)

Expert scientific writer and editor specializing in publication-quality manuscripts for peer-reviewed journals. Automatically orchestrates literature search, evidence evaluation, and prose generation with rigorous quality standards.

**Use this agent when:**
- Writing or editing manuscript sections (Abstract, Introduction, Methods, Results, Discussion)
- Conducting comprehensive literature reviews
- Evaluating research methodology and evidence quality
- Managing references with DOI validation
- Documenting computational pipelines for Methods sections
- Reviewing manuscripts for scientific rigor and writing quality
- Adapting manuscripts to different target venues

## How to Use

### Method 1: Direct Invocation (Recommended)

When starting a Claude Code session, specify the agent:

```bash
cd /path/to/your/omics/project
claude --agent /path/to/omics-skills/agents/omics-scientist.md
```

### Method 2: Copy to User Agents Directory

```bash
# Copy the agent to your user agents directory
cp omics-scientist.md ~/.claude/agents/

# Then invoke it:
claude --agent omics-scientist
```

### Method 3: Reference in Conversation

Start a normal Claude Code session and reference the agent:

```bash
claude
```

Then in the conversation:
```
@agents/omics-scientist I have Illumina reads from a bacterial metagenome.
I need to assemble, bin, and annotate MAGs.
```

## Agent Capabilities

The omics-scientist agent has access to the full skill set in this repository:

| Skill | Purpose | Inputs | Outputs |
|-------|---------|--------|---------|
| `bio-logic` | Scientific reasoning | Questions, data, results | Hypotheses, interpretations, designs |
| `bio-foundation-housekeeping` | Project setup | Project name | Scaffold, environments, schemas |
| `bio-reads-qc-mapping` | Read processing | FASTQ files | QC reports, BAM, coverage |
| `bio-assembly-qc` | Genome assembly | Reads | Contigs, assembly QC |
| `bio-binning-qc` | MAG recovery | Contigs + reads | Binned genomes, QC metrics |
| `bio-gene-calling` | Gene prediction | Contigs/genomes | Gene sequences, GFF |
| `bio-annotation` | Functional annotation | Gene sequences | Annotations, taxonomy inference |
| `bio-phylogenomics` | Phylogenetic analysis | Sequences/genomes | Alignments, trees |
| `bio-protein-clustering-pangenome` | Comparative genomics | Multiple genomes | Orthogroups, pangenome |
| `bio-structure-annotation` | Structure prediction | Protein sequences | PDB files, annotations |
| `bio-viromics` | Viral analysis | Contigs | Viral sequences, taxonomy |
| `bio-stats-ml-reporting` | Analysis & reporting | Results | Reports, models, figures |
| `bio-workflow-methods-docwriter` | Methods documentation | Pipeline artifacts | METHODS.md, workflow summary |
| `bio-prefect-dask-nextflow` | Workflow orchestration | Pipeline requirements | Runnable scaffold |
| `jgi-lakehouse` | JGI metadata access | Query parameters | Project/taxon metadata |
| `tracking-taxonomy-updates` | Taxonomy reconciliation | Scope + sources | Versioned updates |
| `polars-dovmed` | Literature search | Search queries | PMC papers, DOIs, metadata |
| `science-writing` | Manuscript writing | Outline, citations | Publication-ready text |
| `agent-browser` | Web automation | URLs, targets | Screenshots, scraped data |
| `notebook-ai-agents-skill` | Notebooks | Data + goals | Marimo-first notebooks |
| `beautiful-data-viz` | Figures | Data | Publication-ready charts |
| `plotly-dashboard-skill` | Dashboards | Data + requirements | Interactive apps |

## Example Workflows

### Workflow 1: Bacterial Isolate Genome

```
User: I have paired-end Illumina reads (R1.fq, R2.fq) from a Pseudomonas isolate.
      Complete genome analysis needed.

Agent:
0. /bio-logic (reason about approach - assembly strategy, QC thresholds)
1. /bio-foundation-housekeeping (setup project)
2. /bio-reads-qc-mapping (QC + assess coverage)
3. /bio-assembly-qc (assemble genome)
4. /bio-gene-calling (predict genes)
5. /bio-annotation (functional annotation + GTDB taxonomy)
6. /bio-phylogenomics (place in Pseudomonas tree)
7. /bio-logic (interpret placement, metabolic capacity, evolutionary insights)
8. /bio-stats-ml-reporting (generate final report)
```

### Workflow 2: Metagenomic MAG Recovery

```
User: I have a soil metagenome assembly (contigs.fasta) and raw reads.
      I want to recover high-quality MAGs.

Agent:
0. /bio-logic (design binning strategy, define quality thresholds)
1. /bio-binning-qc (bin contigs, refine, QC)
2. /bio-gene-calling (call genes in HQ MAGs)
3. /bio-annotation (annotate MAGs, assign taxonomy)
4. /bio-phylogenomics (phylogenetic placement)
5. /bio-logic (interpret MAG ecology, metabolic roles, novelty)
6. /bio-protein-clustering-pangenome (compare MAGs, build pangenome)
7. /bio-stats-ml-reporting (comparative analysis report)
```

### Workflow 3: Viral Metagenomics

```
User: I have a viral metagenome assembly. Find and characterize viral contigs.

Agent:
1. /bio-viromics (identify viral contigs, classify)
2. /bio-gene-calling (call viral genes)
3. /bio-annotation (annotate viral proteins)
4. /bio-phylogenomics (viral phylogeny)
5. /bio-stats-ml-reporting (viral diversity report)
```

### Workflow 4: Comparative Genomics

```
User: I have 50 Salmonella genomes. Perform pangenome analysis.

Agent:
1. /bio-gene-calling (ensure consistent gene calls)
2. /bio-protein-clustering-pangenome (cluster orthologs, pangenome matrix)
3. /bio-phylogenomics (core genome phylogeny)
4. /bio-annotation (annotate accessory genes)
5. /bio-stats-ml-reporting (pangenome statistics, figures)
```

## Advanced Usage

### Parallel Workflow Execution

The agent can orchestrate parallel skill execution for independent steps:

```
User: I have 10 bacterial genomes that need annotation.

Agent: [Launches 10 parallel /bio-annotation skills]
```

### Quality Gate Enforcement

The agent automatically validates quality at each step:

- **Read QC**: >Q30, <5% adapter contamination
- **Assembly**: N50, misassemblies, completeness
- **MAG QC**: Completeness >50%, contamination <10%
- **Annotation**: >70% genes with hits

If quality gates fail, the agent will:
1. Alert you to the issue
2. Suggest remediation steps
3. Re-check inputs and logs before retrying

### Reproducibility

All skills used by the agent enforce:
- Containerized environments (Docker/Singularity)
- Parameter logging
- Provenance tracking
- Version-controlled workflows

## Integration with Other Skills

The omics-scientist agent can seamlessly integrate with:

- `/jgi-lakehouse` - Fetch reference data from JGI
- `/bio-workflow-methods-docwriter` - Document workflow runs
- `/tracking-taxonomy-updates` - Reconcile taxonomy updates
- `/science-writing` - Generate manuscripts from results
- `/polars-dovmed` - Literature discovery
- `/agent-browser` - Web data retrieval
- `/beautiful-data-viz` - Publication figures
- `/plotly-dashboard-skill` - Interactive dashboards
- `/notebook-ai-agents-skill` - Marimo-first analysis notebooks (Jupyter legacy)

## Tips

1. **Ask "why" and "how" questions liberally** - Triggers `/bio-logic` for scientific reasoning
2. **Always start new projects with bio-foundation-housekeeping** - Sets up proper structure
3. **Trust the agent's workflow suggestions** - Based on best practices
4. **Provide input/output file paths explicitly** - Avoids ambiguity
5. **Mention biological context** - Helps agent optimize parameters and reasoning
6. **Request interpretations** - Agent uses `/bio-logic` to explain biological rationale
7. **Challenge assumptions** - Ask for alternative explanations or experimental designs

## Troubleshooting

**Q: Agent not using the right skill?**
A: Be specific with keywords (see keyword mapping in agent file). For reasoning/interpretation, use words like "why", "how", "explain", "interpret"

**Q: Pipeline failed mid-workflow?**
A: Agent will review logs and suggest fixes

**Q: Need custom parameters?**
A: Explicitly request them - agent will pass to skill

**Q: Want to skip a step?**
A: Tell the agent (e.g., "I already have assemblies, start with gene calling")

## Contributing

To add new skills or modify workflows:
1. Edit `omics-scientist.md`
2. Update keyword mappings
3. Add to decision tree
4. Update this README

## Support

For issues with:
- **Agent behavior**: Edit `omics-scientist.md` system prompt
- **Skill execution**: Refer to skill-specific documentation
- **Claude Code**: See https://github.com/anthropics/claude-code
