---
name: omics-pipeline
description: Route omics pipeline work to its stage skill (reads QC and mapping, assembly, binning, gene calling, annotation, viromics, phylogenomics, pangenomes, HGT, structure, statistics). Use when a genome, metagenome, or viral analysis needs a stage workflow, a driver script, or the shared pipeline rules.
---

# Omics Pipeline

Router for the omics stage skills. Only this skill is listed to the model. Each stage skill is a reference: read its `SKILL.md` when the task reaches that stage. Stage skills keep their directories, names, drivers, fixtures and tests, so existing projects keep calling their scripts by path.

## Instructions

### Stages

Stage skills are sibling directories of this skill's own directory: read `../<name>/SKILL.md` relative to this file, which works in a plugin install and a checkout install alike. A checkout install links them at `~/.agents/skills/<name>/`, and the stage skills write their commands with that path. A driver always runs from its stage skill's own `scripts/` directory, as `uv run --script <stage directory>/scripts/<file>`.

| Stage | Use when | Skill |
| --- | --- | --- |
| Domain routing (first gate) | Any assembly, MAG, SAG, genome, bin set or contig FASTA, before any domain-specific stage | `tracking-taxonomy-updates` |
| Reads QC and mapping | Raw FASTQ, adapters, contaminants, mapping and coverage | `bio-reads-qc-mapping` |
| Assembly | QC-passed reads to contigs, QUAST | `bio-assembly-qc` |
| Binning | Bin contigs, score MAG completeness and contamination | `bio-binning-qc` |
| Gene calling | CDS prediction, tRNA and rRNA census | `bio-gene-calling` |
| Annotation | Function, domains, homology taxonomy, marker and family census | `bio-annotation` |
| Viromics | Viral contigs, CheckV grades, phage and giant-virus taxonomy | `bio-viromics` |
| Phylogenomics | Marker alignments, ML trees, closest relatives | `bio-phylogenomics` |
| Pangenome | Orthogroups, presence and copy-number matrices, synteny | `bio-protein-clustering-pangenome` |
| Interdomain HGT | Virus-host gene exchange, donor direction | `bio-interdomain-hgt` |
| Structure | Weak sequence hits, fold or complex prediction | `bio-structure-annotation` |
| Statistics and ML | Hypothesis tests, classifiers, evidence rollup, report | `bio-stats-ml-reporting` |
| FASTA curation | Standardize headers, deduplicate, build search databases | `bio-fasta-database-curator` |
| Metadata catalog | Schema-checked tables and a DuckDB catalog | `bio-foundation-housekeeping` |
| Taxonomy release tracking | Compare NCBI, GTDB or ICTV releases, renamed taxa | `tracking-taxonomy-updates` |

Workflow engines (Nextflow or Prefect with Dask): [references/workflow-engines.md](references/workflow-engines.md).

### Shared rules

Every stage skill points here. Each rule is stated once.

1. **Domain routing first.** Run QuickClade through `tracking-taxonomy-updates` (BBTools container, `percontig`) on every nucleotide input before choosing a domain-specific stage. Skip it only when the user supplies a trusted domain label and asks to skip triage. QuickClade routes; it is not the final authority. The one routing table is `results/taxonomy/domain_routing.tsv`. Routes: Bacteria and Archaea to GTDB-Tk; phage and prokaryotic viruses to `bio-viromics` then vConTACT3; giant viruses to `bio-viromics` then GVClass and a marker-gene phylogeny; Eukaryota to eukaryote-aware gene calling and EukCC; mixed or low-confidence contigs are split or flagged first.
2. **Large ONT reads.** Do not spend the first full read pass on `gzip -t` or raw `seqkit stats` unless asked. Record raw `stat` metadata (path, size, mtime), optionally check a small sample, make the first full pass the filtering step, then run `seqkit stats` on every produced read set. Check file type by content, not suffix: when `gzip -t` fails on a `.gz` name, inspect the magic bytes before calling the file corrupt, because it may be plain FASTQ. Write long-running outputs to `.tmp`, check them, then `mv`; reuse an output only when it is non-empty and its stage `.done` marker exists.
3. **Hypotheses and axes.** Before the first analysis step, register at least five distinct hypotheses, with technical artifacts and nulls among them. If fewer are plausible, say why and add negative controls. After each major result or QC gate, write a short reflection: what was seen, whether QC passed, which hypotheses gained or lost support, which alternatives remain, the next discriminating check. Revise the register as evidence comes in; never drop a hypothesis silently. Search the literature (`polars-dovmed`) after the first register and after any unexpected, central or final finding. Choose methods and comparison sets from the literature for the inferred group, and compare like with like. When close relatives or a reference set exist, run the query against all five axes, or write the reason for skipping one, and persist one table per axis:
   - genome-property frontier (`relative_genome_metrics.tsv`, `genome_size_frontier.tsv`)
   - marker-gene census (`marker_census.tsv`)
   - per-family copy number (`family_copy_number_comparison.tsv`)
   - conserved neighborhoods (`conserved_neighborhoods.tsv`)
   - ncRNA census (`ncRNA_census.tsv`)

   An expected marker or RNA class that is absent is a result, never silence.
4. **Failures and drivers.** On execution failure, keep the logs and report the failed command. Retry only after diagnosing the cause and recording the changed parameters. Report unmet biological thresholds as results; never tune parameters only to pass a gate. A driver prints one JSON envelope as the last line of stdout: `{"ok": true, "skill", "out", "manifest", "warnings"}`, or `{"ok": false, "error": {"code", "message"}}` with exit code 2. Tools started under `--execute` may print first, so read the last line.
5. **Environment.** Use the project's pinned pixi environment from `bioinformatics-project`; versions follow `tool-versions`. A version in a stage skill is the one its commands were checked against, not an install pin. Record tool, version, thread count and database release in `tasks/METHODS.md`.
6. **Scheduler.** Load `hpc-slurm` before any batch or cluster work. Stage skills hold no account, QOS or cluster flags. Login-node limits follow `hpc-slurm`. Pass an explicit thread count to every tool and match it to the allocated CPUs. Queue and QOS choice follows `hpc-slurm` and the site skill it names; do not pick a debug queue or debug QOS unless that site's rules allow it.
7. **Figures and literature.** Figures follow `beautiful-data-viz`. Literature searches follow `polars-dovmed`.

## Input Requirements

- A project made with `bioinformatics-project`, with a locked pixi environment.
- The inputs of the stage you run; each stage skill lists them.

## Output

- No files of its own. Stage outputs sit under `results/<stage-skill>/`.
- `results/taxonomy/domain_routing.tsv` is the shared routing table (agent-authored path, written by `tracking-taxonomy-updates`).

## Quality Gates

- [ ] The routing table exists for every nucleotide input before a domain-specific stage runs, or the skipped screen has a recorded reason.
- [ ] At least five hypotheses are registered before analysis, and one reflection exists per QC gate.
- [ ] The environment lock file is committed, and each tool has an explicit thread count.
- [ ] Each of the five axes has a persisted table, or a written reason for skipping it.
