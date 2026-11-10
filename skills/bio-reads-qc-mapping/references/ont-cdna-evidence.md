# ONT cDNA transcript evidence for gene calling

Use for eukaryotic or protist drafts that have ONT cDNA or other transcriptome reads. Build the evidence bundle before gene calling (`bio-gene-calling`).

1. Orient and filter full-length ONT cDNA reads with `Pychopper` (SKILL.md step 3): plain `.fastq` output names, and resume from existing classified reads after a report-plotting failure.
2. Map transcript reads splice-aware to each candidate draft genome with minimap2 (`-ax splice` family settings suited to the organism and data). Sort and index the BAMs, and compute a per-genome mapped fraction table.
3. Use the best-supported draft genome as the primary evidence target, but keep the full mapping table: it documents the sample-to-genome assignment and cross-sample ambiguity.
4. Produce a StringTie long-read GTF and transcript FASTA and, when useful, a reference-free transcript assembly such as RNA-Bloom.
5. Summarize these paths in `gene_calling_evidence.tsv` with columns `sample_id`, `evidence_type`, `genome_id`, `path`, `notes`. BRAKER4 or another eukaryote-aware caller must be able to use the bundle directly.

Recovery: when the workflow fails after `Pychopper` but classified reads exist, verify and rename plain FASTQ outputs, run lightweight stats, resume the mapping, StringTie and RNA-Bloom steps, and keep the failure and the resume command in the methods record.

Gates: the mapping summaries show which draft genome the reads support and whether competing drafts have negligible, ambiguous, or substantial mapping. The bundle records every evidence path in enough detail for a reproducible caller run.
