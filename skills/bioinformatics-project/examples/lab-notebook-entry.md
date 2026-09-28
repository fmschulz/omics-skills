# Lab notebook — arctic_metagenome_2026

Chronological, dated decision log kept at the root of `results/` (Noble 2009). Entries run oldest -> newest top to bottom; the most recent entry (current state) is at the bottom. Be verbose: record what was done, why, the evidence, and links to the result files. Document failures and how you knew they failed, so dead ends are not repeated.

---

## 2026-03-20 — metaSPAdes co-assembly attempt — FAILED

**Goal.** Co-assemble stations A+B to recover MAGs.

**How I knew it failed.** The co-assembly N50 was 412 bp and BUSCO completeness on the recovered bins was 6% (`results/2026-03-20_spades/logs/busco.log`). Cause: adapter contamination was NOT removed — the fastp adapter-detection had been disabled in the config by mistake (`--disable_adapter_trimming` left on from a test).

**Fix / next.** Re-enable adapter trimming in the fastp stage, rerun trimming, then re-assemble. Do not delete this entry — this is the second time the test flag leaked into a real run.

---

## 2026-03-30 — QC, trim, assemble, bin (stations A & B)

**Goal.** Get a QC'd co-assembly and a first set of MAGs from the two arctic stations, with adapter trimming re-enabled after the 2026-03-20 failure.

**What I ran.** `results/2026-03-30_qc_trim_assemble_bin/runall` (commit `a1b2c3d`). Stages: FastQC -> fastp (adapter trimming ON) -> metaSPAdes -> bwa mem (reads mapped back to the assembly) -> samtools sort/index -> per-contig depth -> MetaBAT2 binning (seed 42).

**Decisions.**
- Confirmed adapter trimming was on this time; N50 recovered to 14.2 kbp (vs 412 bp on 2026-03-20).
- Mapped the trimmed reads back to the metaSPAdes contigs to get per-contig coverage; coverage + tetranucleotide composition is what MetaBAT2 bins on.
- Set MetaBAT2 `--seed 42` so the (stochastic) clustering reproduces bit-for-bit; seed recorded in `results/2026-03-30_qc_trim_assemble_bin/provenance.txt`.

**Observations.** Station A: 41.2M read pairs, 96.8% mapped back to the co-assembly. 18 bins recovered, total 142 Mbp (see `figures/bin_sizes_data.tsv`, plotted in `figures/bin_sizes.png`). MultiQC read-QC summary: `qc/multiqc_report.html`.

**Provenance.** Tool versions + git commit + seed in `results/2026-03-30_qc_trim_assemble_bin/provenance.txt` (metaSPAdes 3.15.5, bwa 0.7.18, samtools 1.21, MetaBAT2 2.15).

**Next.** Run CheckM on the bins, then dereplicate across stations.

---

## 2026-04-10 — MAG dereplication across stations (dRep)

**Goal.** Collapse the per-station MAGs into a non-redundant species-level set.

**What I ran.** `results/2026-04-10_drep/runall` (commit `e4f5g6h`); CheckM on all bins, then `dRep dereplicate` on the medium-or-better MAGs (completeness >= 50%, contamination <= 10%).

**Decision (approved 2026-04-01; see the project decision record).** Use a 95% ANI secondary cutoff for species-level clustering, consistent with the dRep run in the 2025 paper.

Applied that 95% ANI secondary cutoff (`dRep dereplicate -sa 0.95`); clustering table at `results/2026-04-10_drep/derep/Cdb.csv`.

**Observations.** 18 + 21 input MAGs -> 27 dereplicated species-level MAGs (`figures/mag_quality_data.tsv`, plotted in `figures/mag_quality.png`). Summary regenerated from partial results via `summarize.py` while CheckM on station B was still running.

**Next.** Tag the commit behind `figures/mag_quality.png` (`git tag fig2-mags`) once CheckM on station B finishes.
