---
name: omics-pipeline
description: Run omics pipeline stages from reads QC and mapping to assembly, binning, gene calling, phylogenomics and structure, and open the annotation, viromics and HGT stage skills. Use when a genome, metagenome or viral analysis needs a stage page, a driver or the shared pipeline rules.
---

# Omics Pipeline

This skill is the entry for omics pipeline work. It holds the shared rules, one decision page per stage that has no skill of its own, and the table of stage skills.

## Instructions

### Stage pages

A stage page sits in `references/` and holds the tool choice, the traps and the outputs of one stage. The agent runs the tools and writes the outputs. There is no driver.

| Stage | Use when | Page |
| --- | --- | --- |
| Reads QC and mapping | Raw FASTQ, adapters, contaminants, mapping and coverage | [reads-qc-mapping.md](references/reads-qc-mapping.md) |
| Assembly | QC-passed reads to contigs, QUAST | [assembly.md](references/assembly.md) |
| Binning | Bin contigs, score MAG completeness and contamination | [binning.md](references/binning.md) |
| Gene calling | CDS prediction, tRNA and rRNA census | [gene-calling.md](references/gene-calling.md) |
| Phylogenomics | Marker alignments, ML trees, closest relatives | [phylogenomics.md](references/phylogenomics.md) |
| Structure | Weak sequence hits, fold or complex prediction | [structure.md](references/structure.md) |

Tool notes that the pages link: [quickbin.md](references/quickbin.md), [autocycler.md](references/autocycler.md), [pyrodigal-gv.md](references/pyrodigal-gv.md), [infernal.md](references/infernal.md), [boltz.md](references/boltz.md), [tm-vec.md](references/tm-vec.md). For Nextflow or Prefect with Dask, read [workflow-engines.md](references/workflow-engines.md).

### Stage skills

Stage skills are sibling directories of this skill's own directory: read `../<name>/SKILL.md` relative to this file, which works in a plugin install and a checkout install alike. A checkout install links them at `~/.agents/skills/<name>/`, and the stage skills write their commands with that path. A driver always runs from its stage skill's own `scripts/` directory, as `uv run --script <stage directory>/scripts/<file>`.

| Stage | Use when | Skill |
| --- | --- | --- |
| Domain routing (first gate) | Any assembly, MAG, SAG, genome, bin set or contig FASTA, before any domain-specific stage | `tracking-taxonomy-updates` |
| Annotation | Function, domains, homology taxonomy, marker and family census | `bio-annotation` |
| Viromics | Viral contigs, CheckV grades, phage and giant-virus taxonomy | `bio-viromics` |
| Interdomain HGT | Virus-host gene exchange, donor direction | `bio-interdomain-hgt` |
| Taxonomy release tracking | Compare NCBI, GTDB or ICTV releases, renamed taxa | `tracking-taxonomy-updates` |

### Shared rules

Every stage skill and stage page points here. Each rule is stated once.

1. **Domain routing first.** Run QuickClade through `tracking-taxonomy-updates` (BBTools container, `percontig`) on every nucleotide input before choosing a domain-specific stage. Skip it only when the user supplies a trusted domain label and asks to skip triage. QuickClade routes; it is not the final authority. The one routing table is `results/taxonomy/domain_routing.tsv`. Routes:
   - Bacteria and Archaea: GTDB-Tk.
   - Phage and prokaryotic viruses: `bio-viromics`, then vConTACT3.
   - Giant viruses: `bio-viromics`, then GVClass and a marker-gene phylogeny.
   - Eukaryota: eukaryote-aware gene calling and EukCC.
   - Mixed or low-confidence contigs (`low_confidence` is `true`): split or flag first.
2. **Large ONT reads.** Do not spend the first full read pass on `gzip -t` or raw `seqkit stats` unless asked. Record raw `stat` metadata (path, size, mtime), optionally check a small sample, make the first full pass the filtering step, then run `seqkit stats` on every produced read set. Check file type by content, not suffix: when `gzip -t` fails on a `.gz` name, inspect the magic bytes before calling the file corrupt, because it may be plain FASTQ. Write long-running outputs to `.tmp`, check them, then `mv`; reuse an output only when it is non-empty and its stage `.done` marker exists.
3. **Hypotheses and axes.** Before the first analysis step, register at least five distinct hypotheses, with technical artifacts and nulls among them. If fewer are plausible, say why and add negative controls. After each major result or QC gate, write a short reflection: what was seen, whether QC passed, which hypotheses gained or lost support, which alternatives remain, the next discriminating check. Revise the register as evidence comes in; never drop a hypothesis silently. When close relatives or a reference set exist, run the query against all five axes, or write the reason for skipping one, and persist one table per axis:
   - genome-property frontier (`relative_genome_metrics.tsv`, `genome_size_frontier.tsv`)
   - marker-gene census (`marker_census.tsv`)
   - per-family copy number (`family_copy_number_comparison.tsv`)
   - conserved neighborhoods (`conserved_neighborhoods.tsv`)
   - ncRNA census (`ncRNA_census.tsv`)

   Required columns of the comparative tables. Extra columns are allowed, and the `bio-viromics` driver rejects a table that lacks one:
   - `relative_genome_metrics.tsv`: `genome`, `role` (`query` or `reference`), `group`, `genome_size`, `gene_count`, `literature_min`, `literature_max`, `literature_doi`, in this order. It is the metrics input of the `bio-viromics` driver.
   - `marker_census.tsv`: `genome`, `category`, `family_id`, `copy_number`. The `bio-annotation` driver adds `family_name`, `evidence_source`, `e_value` and `notes`.
   - `family_copy_number_comparison.tsv`: `family_id`, `query_copy_number`, `relative_median`, `status`.
   - `conserved_neighborhoods.tsv`: `query_block_id`, `relative`, `members`.
   - `ncRNA_census.tsv`: `assembly`, `class`, `model`, `count`.

   The `bio-annotation` driver writes `marker_census.tsv` and the family copy-number matrix. The `bio-viromics` driver copies the four tables after `relative_genome_metrics.tsv` and computes `genome_size_frontier.tsv`. The agent writes every other table. An expected marker or RNA class that is absent is a result, never silence.
4. **Failures and drivers.** On execution failure, keep the logs and report the failed command. Retry only after diagnosing the cause and recording the changed parameters. Thresholds are project choices: record each one. Report an unmet biological threshold as a result; never tune parameters only to pass a gate. The three drivers (`bio-annotation`, `bio-viromics`, `bio-interdomain-hgt`) print one JSON envelope as the last line of stdout: `{"ok": true, "skill", "out", "manifest", "warnings"}`, or `{"ok": false, "skill", "error": {"code", "message"}}` with exit code 2. Tools started under `--execute` may print first, so read the last line.
5. **Environment.** Use the project's pinned pixi environment from `bioinformatics-project`; versions follow `tool-versions`. Python tooling runs through uv, never system Python or conda. A version in a stage skill or page is the one its commands were checked against, not an install pin. Record tool, version, thread count and database release in `tasks/METHODS.md`.
6. **Scheduler.** Load `hpc-slurm` before any batch or cluster work. Stage skills and pages hold no account, QOS or cluster flags. Login-node limits follow `hpc-slurm`. Pass an explicit thread count to every tool and match it to the allocated CPUs. Queue and QOS choice follows `hpc-slurm` and the site skill it names; do not pick a debug queue or debug QOS unless that site's rules allow it.
7. **Figures.** Figures follow `beautiful-data-viz`.
8. **Discovery.** For a genome, MAG, viral genome or protein set:
   - Infer the group first. Search the literature for how that group is analyzed, and take methods and comparison sets from it.
   - Compare like with like: run the query and its references through the same tools, databases and thresholds.
   - Say why each analysis fits, and name the plausible ones you skipped.
   - End with an interesting-findings table. Its columns are candidate, evidence, confidence, comparison baseline, literature context and follow-up test.
   - Separate query-specific findings from features common to the comparison set, and state negative findings.
   - The final report lists the hypotheses considered, the reflections, the literature context, the revised ranking, the findings table and the next analyses that would best separate the remaining alternatives.
9. **Literature and reporting.**
   - Search with `polars-dovmed` after the first hypothesis register and after any unexpected, central or final finding. Use one corpus per query, never `--corpus both`.
   - Record the corpus, the query string and the hit count. If a search fails, report the failure and its cause; do not drop the step silently.
   - Summarize script or API JSON in Markdown, and return raw JSON only when the user asks for it. Write large payloads to disk and report the path; never paste them into the reply.
   - Re-run a lookup or driver instead of trusting tool output from earlier in a long conversation.
   - When a script returns `ok: false`, state the error code and message before you propose a fix.

## Input Requirements

- A project made with `bioinformatics-project`, with a locked pixi environment.
- The inputs of the stage you run; each stage page and stage skill lists them.

## Output

- No files of its own. Stage outputs sit under the run directory that `bioinformatics-project` defines (`results/<date>_<name>/<stage>/`), as each stage page and stage skill names them.
- `results/taxonomy/domain_routing.tsv` is the shared routing table (agent-authored path, written by `tracking-taxonomy-updates`).

## Quality Gates

- [ ] The routing table exists for every nucleotide input before a domain-specific stage runs, or the skipped screen has a recorded reason.
- [ ] At least five hypotheses are registered before analysis, and one reflection exists per QC gate.
- [ ] The environment lock file is committed, and each tool has an explicit thread count.
- [ ] Each of the five axes has a persisted table, or a written reason for skipping it.
- [ ] Each literature search has its corpus, query string and hit count recorded.
- [ ] The final report has the contents rule 8 lists.
