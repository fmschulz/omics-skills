# Prose-quality audits

These audits are applied by the `reviewer` and `reviser` roles. They cover sentence-level prose quality: clutter, voice and verbs, sentence architecture, terminology, numbers and citations. They do not assess the underlying science.

The methodology is drawn from Sainani's *Writing in the Sciences* (Stanford, Coursera).

Use the audits as a checklist, not as mechanical find-and-replace. Every flagged item must be reviewed in context — some phrases on the lookup tables below are correct in standard methodological language, and some "rules" are appropriately broken for emphasis or rhythm.

---

## Pass 1 — Clutter

Strip every sentence to its cleanest components. Each word must earn its place.

### Dead-weight phrases → concise replacements

| Cluttered phrase | Replace with |
|---|---|
| due to the fact that | because |
| a majority of | most |
| are of the same opinion | agree |
| give rise to | cause |
| have an effect on | affect |
| in the event that | if |
| at the present time | now / currently |
| in order to | to |
| a number of | several / many |
| on the basis of | based on |
| in light of the fact that | because / since |
| it is worth noting that | (delete — state the point) |
| it is important to note that | (delete) |
| it is interesting to note that | (delete) |
| in terms of | (rewrite to be specific) |

### Dead-weight openers — flag for deletion

- "As it is well known..." → replace with a direct citation
- "It should be emphasized that..."
- "It can be regarded that..."
- "As it has been shown..."
- "It is noteworthy that..."

### Redundancy

Adjectives or adverbs that repeat information already carried by the noun or verb:

- "successful solutions" → "solutions" (success is inherent)
- "completely eliminate" → "eliminate"
- "future plans" → "plans"
- "unexpected surprise" → "surprise"
- "currently underway" → "underway"
- "fully complete" → "complete"

---

## Pass 2 — Voice and verb vitality

Scientific transparency requires accountability: identify who did what.

### Passive → active conversion

1. Spot the pattern: a "to-be" verb plus a past participle (`was observed`, `were analyzed`).
2. Identify the actor. Default to "we" when the authors did the action.
3. Rebuild as Subject–Verb–Object.

Example:

- Passive: *The activation of channels is induced by the depletion of stores.*
- Active: *Depleting stores activates channels.*

### Smothered verbs (nominalizations) → resurrected verbs

| Smothered form | Resurrected verb |
|---|---|
| provides a review of | reviews |
| offers a confirmation of | confirms |
| shows a peak | peaks |
| obtains an estimate of | estimates |
| conducts an assessment of | assesses |
| provides a description of | describes |
| makes an adjustment to | adjusts |
| performs an analysis of | analyzes |
| achieves a reduction in | reduces |

Flag every "noun + of" construction and check whether a direct verb exists.

### When passive voice is acceptable

- The actor is genuinely unknown or irrelevant (*the sample was collected in 2019*).
- Methods sections in journals where passive voice is the house style.
- Deliberate emphasis on the object over the actor.

Do not mechanically convert every passive. Flag the ones where the passive obscures accountability.

---

## Pass 3 — Sentence architecture

### Buried-predicate audit

Count words between the subject and its main verb. If more than ~12 words intervene, the predicate is buried — recommend restructuring.

- Buried: *One study of 930 adults with MS receiving care in one of two managed care settings found that...*
- Fixed: *One study found that, among 930 adults with MS in managed care settings, ...*

### Punctuation for compression

- **Colon** sets up a list or specific explanation, replacing wordy openings.
- **Em dash (—)** marks emphatic parentheticals or merges sentences where a transition feels forced.
- **Semicolon** links closely related independent clauses without a transition word.

### Sentence-length variation

Flag paragraphs where every sentence is roughly the same length (±5 words). Recommend mixing short declarative sentences for emphasis with longer ones for explanation.

---

## Pass 4 — Terminology and keyword consistency

In scientific prose, terminological consistency is a virtue, not a defect.

### Banana Rule

Do not call a banana an "elongated yellow fruit" to avoid repetition. If Methods defines "obese group", Results must not switch to "heavier group". Synonym variation for technical terms forces the reader to wonder whether a new category has been introduced.

### Keyword consistency audit

1. Extract every key term from Methods (group names, variable names, technique names, abbreviations).
2. Verify that the same terms appear in Results, Discussion, tables, and figure captions.
3. Flag every instance where a synonym replaces a defined term.

### Acronym austerity

- Reject non-standard acronyms invented only for author convenience.
- Permit widely recognized acronyms (DNA, RNA, PCR, MAG, ORF, etc.).
- Each acronym must be defined at first use in the Abstract AND in the main text AND in each table or figure legend — readers do not read linearly.

---

## Pass 5 — Numbers and citations

### Numerical consistency checklist

- Sample size (N) in the Abstract matches Table 1.
- Percentages in the text match raw numbers in the tables.
- Significant figures match the measurement precision throughout.
- Figure graphics match the corresponding table values.

### Citation integrity ("telephone game" audit)

Flag any statistic presented as established fact but cited only through secondary sources (reviews, textbooks). Recommend tracing it back to the primary source. Common pattern: *"According to [Review, 2020], the prevalence is 15–62%..."* — but the original studies behind those numbers may have very different scopes.

---

## Severity tags

Every audit finding carries a severity. The `reviser` role addresses CRITICAL and MAJOR first; MINOR may be deferred.

| Tag | Meaning |
|---|---|
| **CRITICAL** | Actively misleads the reader (wrong number, term inconsistency that implies a different variable, passive voice that hides important accountability). |
| **MAJOR** | Significantly impairs clarity (buried predicates, heavy nominalization, dense clutter, inconsistent acronym definitions, secondary-source statistics). |
| **MINOR** | Worth fixing but does not impede understanding (small wordiness, optional style improvements, rhythm). |

---

## Output format for prose-quality reviews

Every finding must include:

- file or section reference (e.g. `Introduction, paragraph 2` or `Results §3.2`)
- the original text
- a concrete revision
- a one-line rationale that names the audit pass
- the severity tag

A `reviewer` report that ends with "consider tightening the language" without a concrete revision fails the rules. Each suggestion must show the substitution.

---

## Constraints

- **Never alter scientific content.** Improve delivery, not substance. If a claim looks wrong, flag it as a content note rather than rewriting it.
- **Respect disciplinary conventions.** Some fields and journals require passive voice in Methods. Ask about the target venue when it is unclear.
- **Preserve author voice.** Clarity, not homogeneity. A sentence that is clear and effective despite breaking one of these rules should be left alone.
- **Be specific.** Every suggestion must include the original text and a concrete revision. "Consider improving clarity" is not a finding.
