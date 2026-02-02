# Example: Introduction Section

This example demonstrates the two-stage writing process and evidence-based principles for crafting a compelling scientific Introduction.

## Stage 1: Structured Outline (Planning)

```
Introduction Outline: Machine Learning for Rare Disease Drug Discovery

Paragraph 1: The Big Picture
- Drug discovery traditionally slow and expensive
- AI/ML methods showing promise for target identification
- Cite: Recent reviews (Smith, 2023 - DOI: 10.1038/nrd.2023.123;
               Jones et al., 2024 - DOI: 10.1016/j.drudis.2024.103456)
- Significant unmet medical need in rare diseases

Paragraph 2: Current State - Common Diseases
- Deep learning effective for common diseases with large datasets
- AlphaFold for protein structure prediction
- Cite: (Jumper et al., 2021 - DOI: 10.1038/s41586-021-03819-2)
- Drug repurposing using ML showing results
- Cite: (Chen & Zhang, 2023 - DOI: 10.1093/bioinformatics/btab789)

Paragraph 3: The Challenge - Rare Diseases
- Limited to no application for rare diseases
- Data scarcity is fundamental barrier
- Only 2 prior attempts documented
- Cite: (Lee et al., 2022 - DOI: 10.1038/s41598-022-12345-x;
         Kumar & Patel, 2023 - DOI: 10.1371/journal.pone.0287654)
- Both studies limited by small training sets (<100 compounds)

Paragraph 4: The Gap and Importance
- No validated approach for rare disease ML with limited data
- Transfer learning from common diseases unexplored
- 7,000+ rare diseases affect 300M people globally
- <5% have approved treatments

Paragraph 5: This Study
- We developed transfer learning framework
- Leverages knowledge from well-studied common diseases
- Validated on 3 rare disease datasets (5-50 compounds each)
- Novel attention mechanism for molecular features
- Hypothesis: Common disease patterns generalize to rare conditions
```

## Stage 2: Flowing Prose (Final Manuscript)

---

### Introduction

Drug discovery remains a time-intensive and financially demanding endeavor, with
traditional pipelines requiring an average of 10-15 years and expenditures exceeding
$2 billion per approved therapeutic. Artificial intelligence and machine learning
approaches have emerged as promising tools for accelerating target identification and
lead optimization, demonstrating success in predicting molecular properties, protein
structures, and drug-target interactions (Smith, 2023; Jones et al., 2024). The potential
impact of these computational methods extends far beyond reducing costs—they offer hope
for addressing the significant unmet medical needs in rare disease populations, where
traditional development incentives often prove insufficient.

Deep learning models have shown remarkable effectiveness when applied to common diseases
where large, well-curated datasets are available. The AlphaFold system transformed protein
structure prediction by training on hundreds of thousands of known structures, achieving
near-experimental accuracy for most proteins (Jumper et al., 2021). Similarly, machine
learning approaches to drug repurposing have identified novel therapeutic applications
for existing compounds by leveraging extensive databases of chemical structures, biological
activities, and clinical outcomes (Chen & Zhang, 2023). These successes demonstrate that
when sufficient training data exists, computational methods can match or exceed traditional
experimental approaches in both speed and accuracy.

However, the application of machine learning to rare diseases faces a fundamental data
scarcity problem. Only two prior studies have attempted to develop predictive models for
rare disease therapeutics: Lee and colleagues (2022) applied convolutional neural networks
to a lysosomal storage disorder but were limited by a training set of only 87 compounds,
while Kumar and Patel (2023) investigated a metabolic disorder with 45 known modulators.
Both studies reported modest predictive performance (AUROC < 0.70) and acknowledged that
insufficient training data constrained model development. The fundamental challenge remains
that rare diseases, by definition, lack the large-scale datasets that enable contemporary
machine learning approaches.

This knowledge gap has critical implications for the millions of individuals affected by
rare diseases. More than 7,000 rare diseases collectively impact approximately 300 million
people worldwide, yet fewer than 5% of these conditions have approved treatments. The
orphan drug designation process provides some incentives for pharmaceutical development,
but the absence of computational tools to accelerate early-stage discovery means that most
rare diseases remain understudied. A validated machine learning framework capable of
operating in data-scarce environments could fundamentally alter the economics and feasibility
of rare disease drug discovery.

To address this challenge, we developed a transfer learning framework that leverages molecular
and biological knowledge learned from well-characterized common diseases to predict therapeutic
candidates for rare conditions. Our approach incorporates a novel attention mechanism that
identifies which molecular features are most conserved across disease contexts, enabling
the model to focus on generalizable patterns rather than disease-specific noise. We
hypothesized that fundamental principles of drug-target interactions—such as pharmacophore
complementarity, binding pocket geometry, and functional group positioning—would generalize
across disease states, even when specific proteins or pathways differ. To test this hypothesis,
we validated our framework on three rare disease datasets ranging from 5 to 50 compounds each,
comparing performance against standard machine learning approaches trained from scratch on
the limited rare disease data alone.

---

## Key Features Demonstrated

**Clarity:**
- Technical terms defined at first use (AUROC, orphan drug designation)
- Logical flow from broad context → specific problem → knowledge gap → this study
- Clear transitions between paragraphs ("However," "To address this challenge")

**Conciseness:**
- Eliminated redundant phrases (outline's "Significant unmet medical need" became integrated context)
- Strong verbs ("emerged," "transformed," "leverage")
- No throat-clearing ("It is interesting to note that...")

**Accuracy:**
- Specific numbers with context (10-15 years, $2 billion, 7,000 rare diseases)
- Precise language (AUROC < 0.70, not "poor performance")
- Clear distinction between observations (prior studies had X compounds) and interpretation (insufficient data constrained models)

**Citation Integration:**
- Citations integrated naturally into sentences (not as lists)
- Primary sources cited (not reviews when primary available)
- DOIs validated via CrossRef API
- Recency appropriate for field (2021-2024 for active ML/drug discovery field)

**Structure:**
- Five paragraphs following recommended Introduction structure
- Clear knowledge gap stated (paragraph 4)
- Specific hypothesis and approach described (paragraph 5)
- Sets up Methods, Results, Discussion to follow

## Verification with CrossRef API

All DOIs in this example can be verified:

```bash
python scripts/crossref_validator.py --doi "10.1038/nrd.2023.123"
python scripts/crossref_validator.py --doi "10.1038/s41586-021-03819-2"
python scripts/crossref_validator.py --doi "10.1371/journal.pone.0287654"
```

Note: Example DOIs are illustrative. For actual manuscripts, always validate against CrossRef.
