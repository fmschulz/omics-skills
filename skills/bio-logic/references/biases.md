# Bias Detection Reference

## Cognitive Biases (Researcher)

| Bias | Signs | Mitigation |
|------|-------|------------|
| Confirmation | Only supporting evidence cited | Preregister, seek disconfirming data |
| HARKing | Hypotheses match results perfectly | Check registration vs publication |
| Publication | Missing negative results | Include grey literature, funnel plots |
| Hindsight | Post-hoc rationalization | Document predictions before data |

## Selection Biases

| Bias | Signs | Mitigation |
|------|-------|------------|
| Sampling | Non-representative sample | Compare to target population |
| Volunteer | Self-selected participants | Document who declined, why |
| Attrition | Differential dropout | Compare dropouts to completers |
| Survivorship | Only "survivors" in sample | Consider who's missing |
| Berkson's | Hospital-based sample | Use population-based controls |

## Measurement Biases

| Bias | Signs | Mitigation |
|------|-------|------------|
| Observer | Unblinded assessors | Blind outcome assessment |
| Recall | Retrospective self-report | Use records, prospective design |
| Social desirability | Sensitive topics | Anonymous, validated scales |
| Instrument | Systematic measurement error | Calibration, validation |

## Analysis Biases

| Bias | Signs | Mitigation |
|------|-------|------------|
| P-hacking | p-values clustered at .049 | Preregister analysis plan |
| Outcome switching | Different outcomes than registered | Compare to registration |
| Subgroup fishing | Many subgroups, no correction | Require prespecification |
| Selective reporting | Missing planned outcomes | Use reporting checklists |

## Confounding

**Detection questions**:
- What affects both exposure AND outcome?
- Were these measured and controlled?
- Could unmeasured confounding explain findings?
- Is there residual confounding after adjustment?

**Control methods**: Randomization balances measured and unmeasured confounders. Restriction, matching, stratification, and statistical adjustment control only the confounders that were measured.

## Study-Level Bias Assessment

### Cochrane Risk of Bias 2 (RoB 2) Domains for Randomized Trials

1. **Randomization process**: sequence generation, allocation concealment, baseline imbalance
2. **Deviations from intended interventions**: blinding of participants and personnel, adherence
3. **Missing outcome data**: attrition and how it was handled
4. **Measurement of the outcome**: blinding of outcome assessors, measurement method
5. **Selection of the reported result**: outcomes and analyses chosen after seeing the data

Rate each assessed result, not the whole study: give a judgment for each domain and an overall judgment for every outcome and time point assessed (Low risk / Some concerns / High risk)

### Newcastle-Ottawa Scale (Observational)

- **Selection** (max 4 stars): Representativeness, selection of controls, exposure ascertainment
- **Comparability** (max 2 stars): Confounding control
- **Outcome** (max 3 stars): Assessment, follow-up adequacy
