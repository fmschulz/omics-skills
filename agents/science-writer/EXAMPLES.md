# Science Writer Agent - Example Workflows

This document provides detailed examples of using the science-writer agent across various scientific writing scenarios.

## Example 1: Complete Literature Review

### Scenario
Write a comprehensive literature review on CRISPR-Cas systems in thermophilic archaea for the Introduction section of a research paper.

### Input Requirements
```
- Topic: CRISPR-Cas systems in thermophilic archaea
- Target: Nature Microbiology
- Format: 2-3 paragraphs with validated DOIs
- Requirements: Broad context → specific focus → knowledge gap
```

### Conversation

```
You: Write a literature review on CRISPR-Cas systems in thermophilic archaea.
     Target: Nature Microbiology Introduction section.

Science Writer:
I'll create a comprehensive, evidence-based literature review using a systematic approach:

Step 1: Literature Discovery
→ /polars-dovmed

Searching 2.4M PMC papers with advanced patterns:
{
  "primary_queries": {
    "crispr_systems": [
      ["CRISPR-Cas9"],
      ["CRISPR-Cas12"],
      ["Cas proteins", "CRISPR"],
      ["CRISPR arrays"]
    ],
    "organisms": [
      ["Sulfolobus"],
      ["Pyrococcus"],
      ["Thermococcus"],
      ["thermophilic", "archaea"],
      ["hyperthermophilic"]
    ],
    "disqualifying_terms": [
      ["bacteria", "bacterial"],
      ["eukaryote"],
      ["mammalian"]
    ]
  },
  "identifier_patterns": {
    "genbank": ["\\b[A-Z]{4}\\d{5,8}\\b"]
  },
  "extract_matches": "primary",
  "max_results": 100
}

Found: 87 papers (2015-2025)
- Peak years: 2019 (12 papers), 2021 (15 papers), 2023 (18 papers)
- Key journals: Nature, Cell, PNAS, mBio, Nucleic Acids Research
- Extracted 234 GenBank accessions

Top 10 papers by relevance:
1. PMC8901234 - "CRISPR-Cas evolution in hyperthermophiles" (Nature 2023) - doi:10.1038/s41586-023-xxxxx
2. PMC8765432 - "Sulfolobus CRISPR adaptation at 80°C" (Cell 2022) - doi:10.1016/j.cell.2022.xxxxx
3. PMC8654321 - "Thermostable Cas9 from Thermococcus" (Science 2021) - doi:10.1126/science.abcxxxx
...

Step 2: Evidence Evaluation
→ /bio-logic

Evaluating top 10 papers:

Paper 1 (Nature 2023):
- Design: Comparative genomics (150 archaeal genomes)
- Strengths: Large sample, phylogenetic controls
- Evidence Quality: HIGH (comprehensive, well-controlled)
- Claim Assessment: Evolutionary claims appropriately matched to comparative evidence

Paper 2 (Cell 2022):
- Design: Experimental (in vitro + in vivo)
- Strengths: RCT design, biochemical validation
- Evidence Quality: HIGH (experimental manipulation, controls)
- Limitations: Single organism (Sulfolobus solfataricus)

Paper 3 (Science 2021):
- Design: Protein characterization
- Strengths: Thermostability assays, crystal structure
- Evidence Quality: MODERATE to HIGH (solid characterization, limited generalization)

Overall synthesis:
- Strong consensus on CRISPR prevalence in thermophilic archaea
- Experimental validation of thermostable Cas proteins
- Knowledge gap: Adaptation dynamics at extreme temperatures remain understudied

Step 3: Writing (Two-Stage Process)

Stage 1 - Outline:
```
Background: CRISPR-Cas discovery and function
- Original discovery in bacteria (Ishino 1987, PMC...)
- Adaptive immunity mechanism (Barrangou 2007, PMC..., doi:10.1126/science.xxxxx)
- Cite: 2-3 seminal papers with DOIs

Thermophilic archaea context
- CRISPR prevalence (Shah 2023, PMC8901234, doi:10.1038/s41586-023-xxxxx)
- Thermostable Cas proteins (Li 2021, PMC8654321, doi:10.1126/science.abcxxxx)
- High temperatures pose unique challenges (Zillig 2022, PMC8765432, doi:10.1016/j.cell.2022.xxxxx)
- Cite: 4-5 recent high-impact papers

Knowledge gap
- Adaptation dynamics poorly understood at >80°C
- Protospacer acquisition rates unknown
- Ecological role in thermal environments unclear
- Only 2 studies (cite both with DOIs)

Research question
- Lead into your study: "Here we investigate..."
```

Stage 2 - Flowing Prose:
→ /science-writing

CRISPR-Cas (Clustered Regularly Interspaced Short Palindromic Repeats and CRISPR-associated proteins) systems provide adaptive immunity against mobile genetic elements in bacteria and archaea (Barrangou et al., 2007; Marraffini & Sontheimer, 2010). These systems function through three distinct phases: adaptation (acquisition of foreign DNA fragments as spacers), expression (transcription of CRISPR arrays), and interference (targeted degradation of invading nucleic acids) (Hille et al., 2018). While CRISPR-Cas systems have been extensively characterized in mesophilic bacteria, recent comparative genomic analyses reveal that they are particularly prevalent in thermophilic and hyperthermophilic archaea, with >60% of sequenced Sulfolobus and Pyrococcus genomes harboring active CRISPR-Cas loci (Shah et al., 2023). The extreme thermal environments inhabited by these organisms—often exceeding 80°C and reaching up to 121°C in deep-sea hydrothermal vents—impose unique constraints on nucleic acid stability and protein function (Zillig et al., 2022). Consequently, archaeal Cas proteins have evolved remarkable thermostability, with Thermococcus-derived Cas9 retaining >80% activity at 90°C compared to <5% for Streptococcus orthologs (Li et al., 2021).

Despite this growing knowledge of CRISPR-Cas system prevalence and thermostable Cas protein biochemistry, the dynamics of CRISPR adaptation in extreme thermal environments remain poorly understood. Only two studies have examined protospacer acquisition rates in hyperthermophiles, both limited to Sulfolobus solfataricus cultures maintained at 78°C (Erdmann & Garrett, 2012; Manica et al., 2013), leaving open questions about how adaptation proceeds at the upper temperature limits of life. Furthermore, the ecological significance of CRISPR-mediated immunity in thermal environments—where viral infection dynamics differ substantially from temperate ecosystems—has not been systematically investigated. Here, we address these gaps by characterizing CRISPR adaptation kinetics in Pyrococcus furiosus across a temperature range of 80-105°C and examining the ecological distribution of CRISPR spacers in metagenomes from diverse hydrothermal systems.

Validation:
✓ Complete paragraphs (no bullets)
✓ Transitions between sentences ("While", "Consequently", "Despite")
✓ Proper tense (present for established facts, past for prior studies)
✓ All DOIs validated via CrossRef API
✓ Appropriate hedging ("suggests", "remain poorly understood")
✓ Broad → specific → gap structure
✓ Accessible for Nature Microbiology audience

References (validated):
1. Barrangou, R., et al. (2007). Science, 315(5819), 1709-1712. doi:10.1126/science.1138140
2. Marraffini, L.A., & Sontheimer, E.J. (2010). Nature Reviews Genetics, 11(3), 181-190. doi:10.1038/nrg2749
3. Hille, F., et al. (2018). Cell, 172(6), 1239-1259. doi:10.1016/j.cell.2017.11.032
4. Shah, S.A., et al. (2023). Nature, 617(7960), 319-325. doi:10.1038/s41586-023-05943-6
5. Zillig, W., et al. (2022). Cell, 185(15), 2801-2817. doi:10.1016/j.cell.2022.06.027
6. Li, Y., et al. (2021). Science, 372(6546), eabd9848. doi:10.1126/science.abd9848
7. Erdmann, S., & Garrett, R.A. (2012). PNAS, 109(36), 14440-14445. doi:10.1073/pnas.1209034109
8. Manica, A., et al. (2013). Molecular Microbiology, 87(5), 1088-1099. doi:10.1111/mmi.12154
```

### Expected Outputs
```
outputs/
├── literature_review.md     (final prose with DOI-validated references)
├── literature_search_results.csv  (87 PMC papers with metadata)
├── evidence_ratings.md      (GRADE ratings for key papers)
└── references.bib          (formatted bibliography)
```

---

## Example 2: Methods Section for Computational Pipeline

### Scenario
Document a Nextflow nf-core/rnaseq pipeline run for the Methods section of a transcriptomics paper.

### Input Requirements
```
- Pipeline: nf-core/rnaseq v3.12.0
- Workflow artifacts: work/ directory, pipeline_info/, params.json
- Target: Genome Research (detailed Methods in main text)
```

### Conversation

```
You: Document this Nextflow RNA-seq pipeline for Methods section.
     Files are in ./nf-core-rnaseq-run/

Science Writer:
I'll create a reproducible Methods section from your workflow artifacts:

→ /bio-workflow-methods-docwriter

Step 1: Inventory evidence files
Found:
✓ work/ directory (command scripts, logs)
✓ pipeline_info/software_versions.yml
✓ pipeline_info/execution_report.html
✓ params.json
✓ nextflow.config
✓ results/multiqc/multiqc_report.html

Step 2: Build run_manifest.yaml
```yaml
run_metadata:
  pipeline_name: "nf-core/rnaseq"
  pipeline_version: "3.12.0"
  pipeline_revision: "abc123def"
  execution_date: "2025-01-15"
  executor: "slurm"

software_versions:
  FastQC: "0.11.9"
  Trim Galore: "0.6.7"
  Cutadapt: "4.4"
  STAR: "2.7.10a"
  Salmon: "1.10.1"
  MultiQC: "1.14"

key_parameters:
  reads: "data/*.fastq.gz"
  genome: "GRCh38"
  aligner: "star_salmon"
  pseudo_aligner: "salmon"
  trimmer: "trimgalore"

workflow_steps:
  - name: "Quality Control"
    tool: "FastQC"
    version: "0.11.9"
    inputs: ["Raw FASTQ files"]
    outputs: ["QC reports"]
    command: "fastqc --threads 4 --outdir results/fastqc sample_R1.fastq.gz sample_R2.fastq.gz"

  - name: "Read Trimming"
    tool: "Trim Galore"
    version: "0.6.7"
    inputs: ["Raw reads"]
    outputs: ["Trimmed FASTQ", "trimming reports"]
    command: "trim_galore --paired --fastqc --quality 20 --length 20 sample_R1.fastq.gz sample_R2.fastq.gz"

  - name: "Alignment"
    tool: "STAR"
    version: "2.7.10a"
    inputs: ["Trimmed reads", "GRCh38 genome index"]
    outputs: ["BAM files", "alignment logs"]
    command: "STAR --genomeDir star_index --readFilesIn trimmed_R1.fq.gz trimmed_R2.fq.gz --readFilesCommand zcat --outSAMtype BAM SortedByCoordinate --outBAMsortingThreadN 8 --quantMode TranscriptomeSAM"
    qc_gate: "Uniquely mapped reads >70%"

  - name: "Quantification"
    tool: "Salmon"
    version: "1.10.1"
    inputs: ["Transcriptome BAM from STAR"]
    outputs: ["Gene-level counts", "TPM values"]
    command: "salmon quant --libType A --alignments transcriptome.bam --targets transcripts.fa --output salmon_quant"
```

Step 3: Validate manifest
✓ Schema validation passed
✓ All required fields present
✓ No version strings marked as NOT CAPTURED

Step 4: Draft METHODS.md

**Workflow Summary** (top of Methods section):
```
RNA-seq data processing followed the nf-core/rnaseq pipeline (version 3.12.0).
Raw reads underwent quality control (FastQC v0.11.9), adapter trimming (Trim
Galore v0.6.7), and alignment to the GRCh38 reference genome using STAR v2.7.10a.
Transcript-level abundances were quantified using Salmon v1.10.1 in alignment-based
mode, and gene-level counts were aggregated for differential expression analysis.
Quality control metrics were aggregated using MultiQC v1.14. All samples passed QC
thresholds (>70% uniquely mapped reads, >20M total reads).
```

**Detailed Methods**:

Then → /science-writing to polish prose:

## RNA Sequencing and Data Processing

Paired-end RNA sequencing libraries were processed using the nf-core/rnaseq pipeline
version 3.12.0 (Ewels et al., 2020). Raw sequencing reads in FASTQ format underwent
quality assessment using FastQC version 0.11.9 (Andrews, 2010) to evaluate per-base
quality scores, GC content distribution, and adapter contamination. Reads were
subsequently trimmed using Trim Galore version 0.6.7, which integrates Cutadapt 4.4
(Martin, 2011) for adapter removal and quality trimming. Trimming parameters were
set to remove bases with quality scores <20 and discard reads shorter than 20 bp
after trimming.

Trimmed reads were aligned to the human reference genome (GRCh38.p13) using STAR
version 2.7.10a (Dobin et al., 2013) in two-pass mode. STAR was configured to output
coordinate-sorted BAM files and transcriptome-aligned BAM files simultaneously using
the --quantMode TranscriptomeSAM parameter. Alignment quality was assessed by
examining the percentage of uniquely mapped reads, with samples achieving <70% unique
mapping excluded from downstream analysis. Gene-level quantification was performed
using Salmon version 1.10.1 (Patro et al., 2017) operating in alignment-based mode
on the transcriptome BAM files produced by STAR. Salmon parameters included automatic
library type detection (--libType A) and bias correction for sequence-specific and
GC-content biases.

Quality control metrics across all samples were aggregated using MultiQC version 1.14
(Ewels et al., 2016). All samples included in the analysis met the following quality
thresholds: >20 million total reads, >70% uniquely mapped reads, and <10% duplication
rate. Raw sequencing data have been deposited in the Gene Expression Omnibus under
accession GSE123456.

## Reproducibility

The complete analysis can be reproduced using the following command:
```bash
nextflow run nf-core/rnaseq \
  -revision 3.12.0 \
  -profile docker \
  --input samplesheet.csv \
  --genome GRCh38 \
  --aligner star_salmon \
  --pseudo_aligner salmon \
  -params-file params.json
```

Container images (Docker) were used to ensure software version consistency. The
specific container digest for the STAR alignment step was
docker://nfcore/rnaseq:3.12.0@sha256:abc123def456. The pipeline configuration,
parameters, and software versions are provided in Supplementary Data 1.

References:
1. Ewels, P.A., et al. (2020). Nat Biotechnol, 38(3), 276-278. doi:10.1038/s41587-020-0439-x
2. Andrews, S. (2010). FastQC: A Quality Control Tool for High Throughput Sequence Data.
3. Martin, M. (2011). EMBnet.journal, 17(1), 10-12. doi:10.14806/ej.17.1.200
4. Dobin, A., et al. (2013). Bioinformatics, 29(1), 15-21. doi:10.1093/bioinformatics/bts635
5. Patro, R., et al. (2017). Nat Methods, 14(4), 417-419. doi:10.1038/nmeth.4197
6. Ewels, P., et al. (2016). Bioinformatics, 32(19), 3047-3048. doi:10.1093/bioinformatics/btw354
```

Quality Gates Passed:
✓ Every step has: purpose, inputs, outputs, command, tool+version
✓ Reproducibility section includes: pinned version, container info, full command
✓ Workflow summary at top
✓ All tool citations included
✓ Past tense used throughout

```

### Expected Outputs
```
outputs/
├── METHODS.md               (publication-ready Methods section)
├── run_manifest.yaml        (machine-readable workflow metadata)
├── workflow_summary.txt     (5-12 line plain language summary)
└── references.bib          (tool citations with DOIs)
```

---

## Example 3: Manuscript Review (Methodology + Writing)

### Scenario
Review a submitted manuscript for both methodological rigor and writing quality before journal submission.

### Conversation

```
You: Review this RCT manuscript on vitamin D supplementation for depression.
     Assess methodology and writing quality.

Science Writer:
I'll conduct a comprehensive review covering both scientific rigor and prose quality:

Step 1: Methodological Evaluation
→ /bio-logic

## Summary
Randomized controlled trial (n=200) testing vitamin D supplementation (4000 IU/day)
vs placebo for major depressive disorder over 12 weeks. Primary outcome: PHQ-9 score change.

## Methodology Assessment

### Study Design
✓ Randomized, double-blind, placebo-controlled (appropriate for causal claim)
✓ Sample size justified (power analysis: 80% power to detect 3-point PHQ-9 difference)
✓ Primary outcome pre-registered (ClinicalTrials.gov NCT12345678)

### Critical Concerns
❌ **Attrition bias**: 35% dropout (70/200), differential by group
   - Intervention: 45/100 (45%) dropout
   - Placebo: 25/100 (25%) dropout
   - χ² test: p<0.001 (significant differential attrition)
   - **Impact**: Threatens validity - if dropouts differ systematically, effect estimate biased

❌ **No intention-to-treat (ITT) analysis**: Only completers analyzed (n=130)
   - Missing data not addressed
   - No sensitivity analyses (e.g., multiple imputation, worst-case scenario)
   - **Impact**: Violates RCT best practices, inflates effect size

### Important Concerns
⚠️ **Single-site study**: Single hospital in Seattle
   - Limits generalizability to other populations/climates
   - Baseline vitamin D levels may differ by geography

⚠️ **No baseline vitamin D measurement**: Cannot assess if effect varies by deficiency status
   - Literature suggests efficacy primarily in deficient individuals
   - Potential effect modification not explored

### Minor Issues
- No blinding success assessment (participants may guess assignment based on side effects)
- No reporting of adverse events
- Follow-up limited to 12 weeks (long-term effects unknown)

## Statistical Analysis Assessment

✓ **Appropriate tests**: Linear mixed models for repeated measures
✓ **Effect sizes reported**: Cohen's d = 0.52 (medium effect)
✓ **Confidence intervals**: 95% CIs provided

❌ **Multiple comparisons not addressed**:
   - 3 secondary outcomes + 5 subgroup analyses = 8 tests
   - No Bonferroni or FDR correction
   - **Impact**: Increased Type I error rate

## Evidence Rating (GRADE)

**Initial Level**: HIGH (RCT)

**Downgraded for**:
- Risk of bias (attrition bias, no ITT) → -1
- Imprecision (single site, narrow population) → -1

**Final Rating**: LOW

## Claim Assessment

**Authors claim**: "Vitamin D supplementation significantly reduces depressive symptoms"

**Claim strength**: Too strong for the evidence
- "Significantly reduces" implies robust, generalizable effect
- High attrition + no ITT analysis undermines confidence
- Single-site limits generalizability

**Appropriate claim**: "Vitamin D supplementation was associated with reduced
depressive symptoms among completers in this single-site trial, though high
differential attrition limits causal inference."

## Bottom Line
Promising but inconclusive due to differential attrition and lack of ITT analysis.
Results suggest potential benefit but require replication with better retention
and robust missing data handling.

---

Step 2: Writing Quality Assessment
→ /science-writing

## IMRAD Structure
✓ Follows IMRAD format
⚠️ Methods section lacks detail on randomization procedure
⚠️ Results section interpretation creeps into Discussion

## Paragraph Flow & Transitions
❌ **Introduction paragraph 3**: Jumps abruptly from mechanism to study aims
   - Missing transition between vitamin D biochemistry and research question
   - Suggested: "Despite these mechanistic insights, clinical evidence remains limited..."

❌ **Discussion paragraph 2**: Bullet points instead of prose
   - Lines 287-294: Five bullet points listing limitations
   - **Fix**: Convert to flowing paragraph with transitions

## Tense Consistency
✓ Abstract: Correct (past for methods/results, present for conclusions)
✓ Introduction: Correct (present for background, past for prior studies)
❌ **Results section line 145**: Present tense ("These data show...")
   - Should be past tense ("These data showed...")
✓ Discussion: Generally correct

## Citation Formatting
⚠️ **DOI validation issues** (CrossRef API):
- Reference 12: DOI invalid (doi:10.1234/missing) → does not resolve
- Reference 23: Title mismatch (cited: "Vitamin D and mood", actual: "Vitamin D metabolism")
- Reference 34: Missing DOI (journal article from 2022 should have DOI)

✓ **Style consistency**: AMA format correct (superscript numbers)

## Nomenclature
✓ Scientific names correctly italicized
✓ Gene names in correct format (*VDR*, not VDR)
✓ Units with proper spacing (4000 IU, not 4000IU)

## Reporting Guidelines (CONSORT)
❌ **Missing CONSORT flow diagram** (required for RCT)
⚠️ **Blinding procedures**: Vague description (line 78: "participants were blinded")
   - Should specify: who prepared allocations, who administered, who assessed outcomes
✓ **Primary outcome**: Clearly defined
❌ **Sample size calculation**: Not reported in main text (only mentions "powered")

## Specific Writing Issues

**Line 34** (Introduction):
- Original: "Due to the fact that depression is a major public health problem..."
- Improved: "Because depression is a major public health problem..." (concise)

**Line 112** (Methods):
- Original: "We performed an analysis of the data..."
- Improved: "We analyzed the data..." (strong verb)

**Line 203** (Results):
- Original: "The mean PHQ-9 score was 18.3 at baseline and was reduced to 12.1 at week 12."
- Improved: "Mean PHQ-9 scores decreased from 18.3 at baseline to 12.1 at week 12." (active, clearer)

**Line 287-294** (Discussion - **CRITICAL**):
```
Original (bullet points):
This study has several limitations:
• Small sample size from single site
• High dropout rate
• No long-term follow-up
• Homogeneous population
• Baseline vitamin D not measured
```

Improved (flowing prose):
```
This study has several limitations that affect interpretation. First, the single-site
design and relatively small sample (n=200) limit generalizability to broader
populations. Second, the high and differential dropout rate (45% in the vitamin D
group vs 25% in placebo) introduces potential attrition bias, particularly given that
we did not perform intention-to-treat analysis. Third, the 12-week follow-up period
precludes assessment of long-term efficacy and safety. Fourth, our predominantly
White, urban, Seattle-based sample may not represent populations with different
baseline vitamin D status due to geographic or genetic factors. Finally, the absence
of baseline vitamin D measurements prevented us from examining whether treatment
efficacy varies by deficiency status, a question that prior literature suggests may
be important.
```

## Quality Checklist
- [ ] Complete paragraphs only (FAIL - Discussion has bullets)
- [x] Appropriate tense
- [ ] All DOIs validated (FAIL - 3 issues found)
- [ ] CONSORT compliance (PARTIAL - missing flow diagram)
- [x] Nomenclature correct
- [ ] Sufficient Methods detail for replication (PARTIAL - randomization vague)

---

Step 3: Structured Review Deliverable

## Overall Assessment

### Strengths
- Rigorous RCT design with appropriate placebo control
- Pre-registered primary outcome
- Validated depression scale (PHQ-9)
- Effect sizes and confidence intervals reported
- Clear research question

### Critical Concerns (threaten main conclusions)
1. **Differential attrition bias**: 45% vs 25% dropout undermines causal inference
2. **No ITT analysis**: Only completers analyzed, violates RCT standards
3. **Overclaimed**: "Significantly reduces" too strong given evidence quality

### Important Issues (affect interpretation)
1. **Multiple comparisons uncorrected**: 8 tests without adjustment
2. **Single-site**: Limits generalizability
3. **Missing baseline vitamin D**: Cannot assess effect modification
4. **CONSORT incomplete**: Missing flow diagram, vague blinding description

### Writing Quality Issues
1. **Bullet points in Discussion** (lines 287-294): Must convert to prose
2. **DOI validation failures**: 3 references need correction
3. **Tense error** (line 145): "show" → "showed"
4. **Wordiness**: Several instances of unnecessary phrases

### Minor Issues
- No adverse events reported
- Limited mechanistic exploration
- Follow-up duration short

## Evidence Rating
**GRADE Level**: LOW (downgraded from HIGH due to attrition bias and imprecision)

## Recommendations

### For Authors (before submission)
1. **Perform ITT analysis** with multiple imputation for missing data
2. **Add CONSORT flow diagram** (mandatory for RCT reporting)
3. **Revise claims** to match evidence strength (suggest "associated with" rather than "reduces")
4. **Convert all bullet points to flowing paragraphs** (Discussion limitations)
5. **Correct DOI errors** using CrossRef API validation
6. **Add detail to Methods**: Randomization procedure, blinding protocol
7. **Adjust for multiple comparisons** or clearly label analyses as exploratory

### For Reviewers/Editors
- Request attrition analysis and ITT results before acceptance
- Verify CONSORT compliance
- Consider requesting replication given limited generalizability

## Decision Recommendation
**Major Revision** - Promising findings but critical methodological and reporting issues
must be addressed before publication.

```

### Expected Outputs
```
outputs/
├── review_report.md          (structured critique with evidence rating)
├── methodological_critique.md (detailed bias assessment)
├── writing_quality_report.md  (specific line-by-line suggestions)
├── doi_validation_report.txt  (CrossRef API results)
└── revised_discussion.md      (example prose for bullet point section)
```

---

## Example 4: Reference Management and DOI Validation

### Scenario
Validate and format a bibliography with 50 references, checking DOIs and formatting in Vancouver style.

### Conversation

```
You: Validate all DOIs in my reference list (references.txt) and format in Vancouver style.

Science Writer:
→ /science-writing (CrossRef API validation)

Step 1: Parse reference list
Found: 50 references

Step 2: Extract DOIs and validate
Running CrossRef API validation...

Results:
✓ Valid DOIs: 42/50 (84%)
❌ Invalid DOIs: 3
⚠️ Missing DOIs: 5

## DOI Validation Report

### Invalid DOIs (DO NOT RESOLVE)
1. Reference 12: doi:10.1234/missing
   - CrossRef API: 404 Not Found
   - Possible issue: Typo in DOI
   - Suggested action: Check original paper, verify DOI

2. Reference 23: doi:10.5678/wrongdoi
   - CrossRef API: 404 Not Found
   - Possible issue: Incorrect DOI entered
   - Suggested action: Look up paper by title

3. Reference 34: doi:10.9012/retracted
   - CrossRef API: 200 OK but marked as RETRACTED
   - ⚠️ WARNING: This paper has been retracted (2023-08-15)
   - Reason: "Data fabrication"
   - Suggested action: Remove citation or cite retraction notice

### Missing DOIs (papers that should have DOIs)
4. Reference 5: Smith et al., J Clin Endocrinol Metab, 2022
   - No DOI provided
   - CrossRef lookup by title: doi:10.1210/clinem/dgac456
   - ✓ Found and validated

5. Reference 18: Jones et al., Lancet, 2021
   - No DOI provided
   - CrossRef lookup by title: doi:10.1016/S0140-6736(21)01234-5
   - ✓ Found and validated

6. Reference 29: Lee et al., Nature, 2023
   - No DOI provided
   - CrossRef lookup by title: doi:10.1038/s41586-023-06543-2
   - ✓ Found and validated

7. Reference 37: Chen et al., Cell, 2020
   - No DOI provided
   - CrossRef lookup by title: doi:10.1016/j.cell.2020.08.012
   - ✓ Found and validated

8. Reference 44: Wilson et al., PNAS, 2019
   - No DOI provided
   - CrossRef lookup by title: MULTIPLE MATCHES
   - Manual disambiguation needed

### Title Mismatches (DOI resolves but title differs)
9. Reference 15:
   - Cited title: "Vitamin D and mood disorders"
   - Actual title (from CrossRef): "Vitamin D metabolism and neuropsychiatric outcomes"
   - doi:10.1002/jnr.24567 (valid)
   - Suggested action: Update title to match publication

Step 3: Format references in Vancouver style

Example output (first 5):

1. Anglin RE, Samaan Z, Walter SD, McDonald SD. Vitamin D deficiency and depression
in adults: systematic review and meta-analysis. Br J Psychiatry. 2013;202:100-7.
doi:10.1192/bjp.bp.111.106666

2. Spedding S. Vitamin D and depression: a systematic review and meta-analysis
comparing studies with and without biological flaws. Nutrients. 2014;6(4):1501-18.
doi:10.3390/nu6041501

3. Jorde R, Kubiak J. No improvement in depressive symptoms by vitamin D
supplementation: results from a randomised controlled trial. J Intern Med.
2018;284(4):4
05-22. doi:10.1111/joim.12759

4. Okereke OI, Reynolds CF 3rd, Mischoulon D, et al. Effect of long-term vitamin D3
supplementation vs placebo on risk of depression or clinically relevant depressive
symptoms and on change in mood scores: a randomized clinical trial. JAMA.
2020;324(5):471-80. doi:10.1001/jama.2020.10224

5. Vellekkatt F, Menon V. Efficacy of vitamin D supplementation in major depression:
a meta-analysis of randomized controlled trials. J Postgrad Med. 2019;65(2):74-80.
doi:10.4103/jpgm.JPGM_571_17

Step 4: Generate corrected bibliography

Delivered files:
1. references_vancouver.txt - All 50 references in Vancouver format
2. doi_validation_report.txt - Detailed validation results
3. corrections_needed.md - List of references requiring manual review
4. references.bib - BibTeX format with validated metadata

Summary:
- 42 references: ✓ Valid, formatted correctly
- 3 references: ❌ Invalid DOI, need correction
- 5 references: ✓ Added missing DOIs
- 1 reference: ⚠️ RETRACTED, recommend removal
- 1 reference: Title mismatch, corrected

Action required:
1. Fix/verify DOIs for references 12, 23
2. Remove or update reference 34 (retracted paper)
3. Manually disambiguate reference 44
4. Review title correction for reference 15
```

### Expected Outputs
```
outputs/
├── references_vancouver.txt   (formatted bibliography)
├── doi_validation_report.txt  (CrossRef API results)
├── corrections_needed.md      (list of issues to fix)
├── references.bib            (BibTeX with validated metadata)
└── retracted_papers.txt      (papers marked as retracted)
```

---

## Example 5: Writing Discussion Section with Evidence Evaluation

### Scenario
Write the Discussion section for an observational cohort study on dietary patterns and cardiovascular disease.

### Conversation

```
You: Write Discussion for my cohort study. We found Mediterranean diet associated
     with 25% reduced CVD risk (HR=0.75, 95% CI: 0.68-0.83, p<0.001).
     10,000 participants, 8-year follow-up. Target: American Journal of Clinical Nutrition.

Science Writer:
I'll create a Discussion that appropriately interprets these observational findings:

Step 1: Evaluate Your Own Evidence
→ /bio-logic

## Evidence Assessment

### Study Design
- Cohort study (observational, not experimental)
- Can establish temporal precedence (diet → CVD)
- Cannot establish causation (unmeasured confounding possible)

### Claim Strength Evaluation
- HR = 0.75 (25% reduction) is a moderate effect
- 95% CI: 0.68-0.83 (does not cross 1.0, statistically significant)
- p<0.001 (strong statistical evidence)

BUT:
- Observational design → cannot rule out confounding
- Dietary assessment typically has measurement error
- Healthy user bias possible (Mediterranean diet adherents may have other healthy behaviors)

### Appropriate Language
- ✓ "Associated with reduced risk"
- ✓ "Suggests potential benefit"
- ❌ "Reduces risk" (implies causation)
- ❌ "Prevents CVD" (too strong for observational data)

### GRADE Rating
- Observational study: LOW baseline
- Large effect (HR <0.80): +1
- Dose-response (if shown): +1
- **Estimated GRADE**: MODERATE (if dose-response shown, otherwise LOW)

Step 2: Literature Context
→ /polars-dovmed

Searching PMC for context:
- Query: "Mediterranean diet cardiovascular disease cohort"
- Found: 234 papers (2015-2025)
- Key meta-analyses: 5
- Comparable cohorts: 12

Top relevant papers:
1. PMC9876543 - Meta-analysis of 25 cohorts (2023) - HR=0.79 (0.75-0.84)
2. PMC9765432 - Lyon Diet Heart Study (RCT, 1999) - 70% reduction in recurrent MI
3. PMC9654321 - PREDIMED trial (RCT, 2018) - 30% reduction in major CV events

Synthesizing: Your HR=0.75 consistent with meta-analysis (HR=0.79) and RCT evidence

Step 3: Draft Discussion (Two-Stage Process)

Stage 1 - Outline:
```
Paragraph 1: Main findings
- Mediterranean diet → 25% reduced CVD risk (cite your results)
- Consistent with prior meta-analyses (cite PMC9876543, HR=0.79)
- Consistent with RCT evidence (cite PREDIMED, PMC9654321)

Paragraph 2: Potential mechanisms
- Anti-inflammatory effects (omega-3, polyphenols)
- Improved lipid profile
- Reduced oxidative stress
- Cite mechanistic studies

Paragraph 3: Comparison with prior literature
- Lyon Diet Heart Study: 70% reduction (secondary prevention)
- PREDIMED: 30% reduction (primary prevention in high-risk)
- Your study: 25% reduction (general population primary prevention)
- Explain why effects differ (populations, outcomes, diet adherence)

Paragraph 4: Strengths
- Large sample size (n=10,000)
- Long follow-up (8 years)
- Validated FFQ
- Adjudicated outcomes

Paragraph 5: Limitations (specific, not generic)
- Observational → cannot prove causation
- Residual confounding possible (SES, health consciousness)
- Dietary assessment by FFQ → measurement error
- Single baseline assessment → diet changes not captured
- Predominantly white population → generalizability limited

Paragraph 6: Implications
- Supports dietary guidelines recommending Mediterranean diet
- Cohort-based risk prediction tools
- Need for implementation strategies in clinical practice

Paragraph 7: Future directions
- RCTs in diverse populations
- Mechanism studies (metabolomics)
- Gene-diet interactions
```

Stage 2 - Flowing Prose:
→ /science-writing

## Discussion

In this prospective cohort study of 10,000 adults followed for 8 years, we found
that greater adherence to a Mediterranean dietary pattern was associated with a 25%
lower risk of incident cardiovascular disease (HR=0.75, 95% CI: 0.68-0.83). This
finding is consistent with a recent meta-analysis of 25 prospective cohorts that
reported a pooled hazard ratio of 0.79 (95% CI: 0.75-0.84) for the association
between Mediterranean diet and CVD outcomes (Rosato et al., 2023). Moreover, our
observational findings align with randomized controlled trial evidence, particularly
the PREDIMED trial, which demonstrated a 30% reduction in major cardiovascular events
among participants randomly assigned to a Mediterranean diet supplemented with extra-virgin
olive oil or nuts compared to a low-fat control diet (Estruch et al., 2018). The
convergence of evidence across observational and experimental designs strengthens
confidence that the observed association may reflect a true beneficial effect.

Several biological mechanisms may explain the cardiovascular benefits of Mediterranean
dietary patterns. The high content of monounsaturated fatty acids from olive oil,
omega-3 fatty acids from fish, and polyphenols from fruits, vegetables, and red wine
collectively exert anti-inflammatory effects, as evidenced by reduced circulating
C-reactive protein and interleukin-6 levels in intervention studies (Casas et al.,
2014). Additionally, Mediterranean diet adherence improves lipid profiles by increasing
HDL cholesterol and reducing triglycerides and oxidized LDL particles (Schwingshackl
& Hoffmann, 2014). The abundant fiber and antioxidant content may also reduce
oxidative stress and improve endothelial function, both critical pathways in
atherosclerosis development (Ros et al., 2014). These plausible mechanisms, coupled
with consistent epidemiologic and trial data, support a potential causal relationship
despite the observational nature of our study.

When comparing our findings to landmark trials, the magnitude of association we
observed (HR=0.75) falls between estimates from primary and secondary prevention
contexts. The Lyon Diet Heart Study, a secondary prevention trial in post-myocardial
infarction patients, reported a dramatic 70% reduction in recurrent cardiac events
(de Lorgeril et al., 1999), likely reflecting both the Mediterranean diet effect and
the high baseline risk in that population. In contrast, PREDIMED, conducted in
individuals at high cardiovascular risk but without prior events, found a 30% risk
reduction (Estruch et al., 2018), more comparable to our 25% estimate in a general
primary prevention cohort. The slightly smaller effect size in our study may reflect
our inclusion of lower-risk individuals, lower baseline adherence to Mediterranean
diet principles in a North American population, or differences in outcome ascertainment
methods. Importantly, the consistency of direction across these diverse populations
and study designs reinforces the robustness of the Mediterranean diet-CVD association.

Our study has several notable strengths. The large sample size (n=10,000) provided
sufficient statistical power to detect moderate effect sizes with precision, as
evidenced by the narrow confidence interval (0.68-0.83). The prospective design with
8-year follow-up established temporal precedence, a necessary criterion for causal
inference. Dietary intake was assessed using a validated semi-quantitative food
frequency questionnaire that has demonstrated good reproducibility and validity against
multiple diet records (Willett et al., 1985). Cardiovascular outcomes were centrally
adjudicated by a committee of physicians blinded to dietary exposure status, reducing
outcome misclassification bias. Finally, we adjusted for a comprehensive set of
potential confounders including socioeconomic status, physical activity, smoking,
and comorbidities.

However, several limitations warrant consideration when interpreting these findings.
First, as an observational study, we cannot definitively establish causation; residual
confounding from unmeasured or imperfectly measured factors remains possible. In
particular, individuals who adhere to a Mediterranean diet may also engage in other
health-promoting behaviors not fully captured by our covariate adjustment, such as
stress management techniques or stronger social support networks—a phenomenon known
as the "healthy user effect." Second, dietary intake was assessed using self-reported
food frequency questionnaires, which are subject to measurement error due to recall
bias and social desirability bias. Such non-differential misclassification would tend
to attenuate associations toward the null, suggesting our effect estimate may be
conservative. Third, we assessed diet only at baseline, failing to account for dietary
changes over the 8-year follow-up period; participants who initially reported high
Mediterranean diet adherence may have subsequently altered their eating patterns.
Fourth, our study population was predominantly white and middle-to-upper socioeconomic
status, limiting generalizability to more diverse populations with different baseline
dietary patterns and cardiovascular risk profiles. Finally, although we adjusted for
multiple confounders, residual confounding by socioeconomic status—which is difficult
to fully capture with education and income alone—may partly explain the observed
association.

These findings have several implications for public health and clinical practice. They
provide additional epidemiologic support for current dietary guidelines that recommend
Mediterranean-style eating patterns for cardiovascular disease prevention (U.S.
Department of Agriculture, 2020). Our results suggest that even in a general primary
prevention population, meaningful risk reduction may be achievable through dietary
modification. Clinicians may consider integrating Mediterranean diet principles into
individualized nutrition counseling, and public health initiatives could promote
Mediterranean dietary components through policy interventions such as food labeling,
subsidies for fruits and vegetables, and school nutrition programs. However,
implementation challenges remain, particularly regarding the affordability and
accessibility of Mediterranean diet foods in food-insecure communities.

Future research should address several key questions. First, randomized controlled
trials of Mediterranean diet in ethnically and geographically diverse populations are
needed to establish causality and assess generalizability. Second, mechanistic studies
employing metabolomics and gut microbiome profiling could elucidate the specific
biochemical pathways through which Mediterranean diet components confer cardiovascular
protection. Third, gene-diet interaction studies may identify subgroups who derive
greater or lesser benefit based on genetic predisposition. Finally, pragmatic trials
testing scalable intervention strategies—such as medically tailored meal delivery or
produce prescription programs—are essential to translate these findings into real-world
cardiovascular disease prevention.

In conclusion, our large prospective cohort study found that greater adherence to a
Mediterranean dietary pattern was associated with a 25% lower risk of incident
cardiovascular disease over 8 years of follow-up. This association was consistent with
prior observational and experimental evidence, biologically plausible, and robust to
adjustment for multiple confounders. While the observational design precludes definitive
causal inference, these findings support the inclusion of Mediterranean dietary
recommendations in cardiovascular disease prevention guidelines and highlight the need
for continued research to optimize implementation strategies.

---

Validation:
✓ Complete paragraphs (no bullets)
✓ Appropriate hedging ("associated with", "suggests", "may")
✓ Past tense for your findings ("we found")
✓ Present tense for interpretation ("these findings support")
✓ Specific limitations (not generic)
✓ Biological mechanisms cited
✓ Comparison with prior literature
✓ Implications and future directions
✓ AJCN tone: detailed, comprehensive, methodologically rigorous
```

### Expected Outputs
```
outputs/
├── discussion_section.md        (final Discussion with flowing prose)
├── evidence_assessment.md       (GRADE rating and claim evaluation)
├── literature_context.csv       (PMC search results: 234 papers)
└── references.bib              (validated citations with DOIs)
```

---

## Common Workflow Patterns Summary

| Scenario | Skills Used | Key Steps |
|----------|-------------|-----------|
| **Literature review** | polars-dovmed → bio-logic → science-writing | Search → Evaluate → Synthesize |
| **Methods (computational)** | bio-workflow-methods-docwriter → science-writing | Extract → Document → Polish |
| **Manuscript review** | bio-logic + science-writing | Critique methodology + Assess writing |
| **Reference management** | science-writing | DOI validation + Formatting |
| **Discussion writing** | bio-logic → polars-dovmed → science-writing | Evaluate evidence → Context → Interpret |

---

## Tips for Success

1. **Specify target venue** - "Nature", "NEJM", "NeurIPS"
2. **Request evidence evaluation** - "Use /bio-logic to assess if causal claim is justified"
3. **Always validate DOIs** - "Check all DOIs with CrossRef API"
4. **Two-stage process** - Outline with citations → Flowing prose
5. **Match claims to evidence** - Observational = "associated with", RCT = "reduced"
6. **Complete paragraphs only** - Never submit bullets in final manuscripts
