#!/usr/bin/env bash
#
# runall.sh — driver for a metagenome QC -> trim -> co-assembly -> map -> bin pipeline.
#
# This is an EXAMPLE following Noble 2009's six rules of thumb for driver scripts:
#   1. Record every operation        — every command is here, nothing typed by hand.
#   2. Comment generously            — readable from the comments alone.
#   3. No hand-edited intermediates  — transforms use scripted tools only.
#   4. Store names in variables       — all paths/names are variables at the top.
#   5. Relative paths                 — runs after checkout to a different location.
#   6. Restartable                    — each stage is skipped if its output exists,
#                                       and outputs are written temp-then-renamed.
#
# Usage:
#   ./runall.sh                 # run the whole experiment (resumes if partial)
#   ./runall.sh --help          # print this usage
#
# Real metagenomics tools are referenced (fastqc, fastp, metaspades.py, bwa/minimap2,
# samtools, jgi_summarize_bam_contig_depths, metabat2). A missing tool, input, or
# expected intermediate exits non-zero so an incomplete run cannot look successful.
#
# --- END USAGE ---

# --- Abort on error: fail fast, undefined vars are errors, pipe failures propagate.
set -euo pipefail

# --- Usage statement: print the header block up to the END USAGE sentinel.
usage() { sed -n '2,/^# --- END USAGE ---$/p' "$0"; }
case "${1:-}" in -h|--help) usage; exit 0 ;; esac

# --- Rule 5: work from the experiment directory using RELATIVE paths only.
# Under Slurm the batch script runs from a spooled copy, so its own path is not the
# experiment directory: submit from the project root (sbatch --chdir=PROJECT_ROOT)
# with the absolute experiment directory exported as EXPERIMENT_DIR.
if [[ -n "${EXPERIMENT_DIR:-}" ]]; then
  cd "$EXPERIMENT_DIR"
elif [[ -z "${SLURM_JOB_ID:-}" ]]; then
  cd "$(dirname "${BASH_SOURCE[0]}")"
else
  echo "Under Slurm, export the absolute EXPERIMENT_DIR (sbatch --export=ALL,EXPERIMENT_DIR=...)." >&2
  exit 1
fi

# --- Rule 4: every file and directory name lives here. Swap inputs in one place.
RAW_DIR="../../data/raw"               # immutable raw reads (relative to experiment dir)
SAMPLE="stationA"                      # sample id (the key shared across tables)
R1="${RAW_DIR}/${SAMPLE}_R1.fastq.gz"
R2="${RAW_DIR}/${SAMPLE}_R2.fastq.gz"

QC_DIR="qc"
TRIM_DIR="trimmed"
ASM_DIR="assembly"
ALN_DIR="aligned"
DEPTH_DIR="depth"
BINS_DIR="bins"
LOG_DIR="logs"
FIG_DIR="figures"

TRIM_R1="${TRIM_DIR}/${SAMPLE}_R1.trim.fastq.gz"
TRIM_R2="${TRIM_DIR}/${SAMPLE}_R2.trim.fastq.gz"
CONTIGS="${ASM_DIR}/contigs.fasta"
SORTED_BAM="${ALN_DIR}/${SAMPLE}.sorted.bam"
DEPTH_TSV="${DEPTH_DIR}/contig_depth.tsv"
BIN_PREFIX="${BINS_DIR}/bin"            # MetaBAT2 writes ${BIN_PREFIX}.1.fa, .2.fa, ...
BIN_TSV="${FIG_DIR}/bin_sizes_data.tsv"
PROV="provenance.txt"

# --- Rule 6 (Sandve rule 6): one fixed RANDOM SEED for every stochastic step.
SEED=42                                 # passed to MetaBAT2 (--seed) below

# --- Generate the below-the-date structure automatically (Noble 2009).
for d in "$QC_DIR" "$TRIM_DIR" "$ASM_DIR" "$ALN_DIR" "$DEPTH_DIR" "$BINS_DIR" "$LOG_DIR" "$FIG_DIR"; do
  [ -d "$d" ] || mkdir -p "$d"
done

# --- have <tool>: true if the tool is on PATH (used by fail-fast stage checks).
have() { command -v "$1" >/dev/null 2>&1; }

# --- log <msg>: timestamped message to stderr (Noble: errors/status to stderr).
log() { printf '[%s] %s\n' "$(date -u +%H:%M:%S)" "$*" >&2; }

# === Stage 0: PROVENANCE — record exactly how this result was produced =========
# Sandve rule 1/3/6: capture host, git commit, seed, and exact tool versions.
if [ ! -s "$PROV" ]; then
  log "stage 0: writing provenance -> $PROV"
  {
    echo "# provenance  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "host: $(uname -srm)"
    echo "git:  $(git rev-parse HEAD 2>/dev/null || echo 'not a git repo')"
    echo "seed: ${SEED}"
    echo "# tool versions:"
    for tool in fastqc fastp metaspades.py bwa minimap2 samtools metabat2; do
      if have "$tool"; then
        printf '%s: ' "$tool"; "$tool" --version 2>&1 | head -n1
      else
        echo "${tool}: NOT INSTALLED"
      fi
    done
  } > "${PROV}.tmp" && mv "${PROV}.tmp" "$PROV"   # temp-then-rename
fi

# === Stage 1: QC — FastQC on the raw reads ====================================
# Restartable: skip if the report already exists.
QC_DONE="${QC_DIR}/${SAMPLE}_R1_fastqc.zip"
if [ -s "$QC_DONE" ]; then
  log "stage 1: QC already done, skipping"
elif have fastqc && [ -s "$R1" ]; then
  log "stage 1: FastQC on raw reads"
  fastqc -q -o "$QC_DIR" "$R1" "$R2" > "${LOG_DIR}/fastqc.log" 2>&1
else
  log "ERROR stage 1: fastqc missing or raw reads absent at $R1 / $R2"
  exit 1
fi

# === Stage 2: TRIM — fastp adapter/quality trimming ===========================
# Write to a temp name, rename only on success (Noble: never confuse partial output).
if [ -s "$TRIM_R1" ]; then
  log "stage 2: trimmed reads exist, skipping"
elif have fastp && [ -s "$R1" ]; then
  log "stage 2: fastp trimming"
  fastp -i "$R1" -I "$R2" \
        -o "${TRIM_R1}.tmp" -O "${TRIM_R2}.tmp" \
        --json "${TRIM_DIR}/${SAMPLE}.fastp.json" \
        > "${LOG_DIR}/fastp.log" 2>&1
  mv "${TRIM_R1}.tmp" "$TRIM_R1"
  mv "${TRIM_R2}.tmp" "$TRIM_R2"
else
  log "ERROR stage 2: fastp missing or raw reads absent"
  exit 1
fi

# === Stage 3: ASSEMBLE — metaSPAdes assembly of the trimmed reads =============
# Output is a contigs FASTA (standard format) the rest of the pipeline maps onto.
if [ -s "$CONTIGS" ]; then
  log "stage 3: assembly exists, skipping"
elif have metaspades.py && [ -s "$TRIM_R1" ]; then
  log "stage 3: metaSPAdes assembly"
  metaspades.py -1 "$TRIM_R1" -2 "$TRIM_R2" -t 8 -o "${ASM_DIR}.tmp" \
    > "${LOG_DIR}/metaspades.log" 2>&1
  mv "${ASM_DIR}.tmp/contigs.fasta" "$CONTIGS"
else
  log "ERROR stage 3: metaspades.py missing or trimmed reads absent"
  exit 1
fi

# === Stage 4: MAP — map trimmed reads back to the assembly, sort, index =======
# Coverage per contig is needed for binning. Keep standard sorted+indexed BAM.
if [ -s "$SORTED_BAM" ]; then
  log "stage 4: sorted BAM exists, skipping"
elif have samtools && [ -s "$CONTIGS" ] && [ -s "$TRIM_R1" ]; then
  if have bwa; then
    log "stage 4: bwa mem mapping reads back to assembly"
    [ -s "${CONTIGS}.bwt" ] || bwa index "$CONTIGS" > "${LOG_DIR}/bwa_index.log" 2>&1
    bwa mem -t 8 "$CONTIGS" "$TRIM_R1" "$TRIM_R2" 2> "${LOG_DIR}/map.log" \
      | samtools sort -o "${SORTED_BAM}.tmp" -
    mv "${SORTED_BAM}.tmp" "$SORTED_BAM"
    samtools index "$SORTED_BAM"
  elif have minimap2; then
    log "stage 4: minimap2 mapping reads back to assembly"
    minimap2 -ax sr -t 8 "$CONTIGS" "$TRIM_R1" "$TRIM_R2" 2> "${LOG_DIR}/map.log" \
      | samtools sort -o "${SORTED_BAM}.tmp" -
    mv "${SORTED_BAM}.tmp" "$SORTED_BAM"
    samtools index "$SORTED_BAM"
  else
    log "ERROR stage 4: no aligner found; install bwa or minimap2"
    exit 1
  fi
else
  log "ERROR stage 4: samtools, contigs, or trimmed reads missing"
  exit 1
fi

# === Stage 5: DEPTH — per-contig coverage table for binning ===================
# jgi_summarize_bam_contig_depths ships with MetaBAT2; standard TSV format.
if [ -s "$DEPTH_TSV" ]; then
  log "stage 5: depth table exists, skipping"
elif have jgi_summarize_bam_contig_depths && [ -s "$SORTED_BAM" ]; then
  log "stage 5: summarizing contig depth -> $DEPTH_TSV"
  jgi_summarize_bam_contig_depths --outputDepth "${DEPTH_TSV}.tmp" "$SORTED_BAM" \
    > "${LOG_DIR}/depth.log" 2>&1
  mv "${DEPTH_TSV}.tmp" "$DEPTH_TSV"
else
  log "ERROR stage 5: depth tool missing or sorted BAM absent"
  exit 1
fi

# === Stage 6: BIN — MetaBAT2 binning, the stochastic step with the FIXED SEED ==
# MetaBAT2 clustering is stochastic; --seed makes it reproducible (Sandve rule 6).
if ls "${BIN_PREFIX}".*.fa >/dev/null 2>&1; then
  log "stage 6: bins exist, skipping"
elif have metabat2 && [ -s "$CONTIGS" ] && [ -s "$DEPTH_TSV" ]; then
  log "stage 6: MetaBAT2 binning with seed ${SEED}"
  metabat2 -i "$CONTIGS" -a "$DEPTH_TSV" -o "$BIN_PREFIX" --seed "$SEED" \
    > "${LOG_DIR}/metabat2.log" 2>&1
else
  log "ERROR stage 6: metabat2, contigs, or depth table missing"
  exit 1
fi

# === Stage 7: SUMMARIZE — store RAW DATA behind the plot (Sandve rule 7) =======
# Build a per-bin size table from the binning output; a plotting script reads this
# table, not live state, so the figure re-renders without rerunning the analysis.
if [ -s "$BIN_TSV" ]; then
  log "stage 7: bin-size table exists, skipping"
elif ls "${BIN_PREFIX}".*.fa >/dev/null 2>&1 && have seqkit; then
  log "stage 7: writing bin-size table -> $BIN_TSV"
  {
    printf 'bin\tcontigs\ttotal_bp\n'
    # seqkit stats -T columns: file format type num_seqs sum_len ...
    for bin in "${BIN_PREFIX}".*.fa; do
      seqkit stats -T "$bin" | awk -v b="$bin" 'NR==2 {print b"\t"$4"\t"$5}'
    done
  } > "${BIN_TSV}.tmp" && mv "${BIN_TSV}.tmp" "$BIN_TSV"
else
  log "ERROR stage 7: bins missing or seqkit unavailable"
  exit 1
fi

for output in "$TRIM_R1" "$TRIM_R2" "$CONTIGS" "$SORTED_BAM" "${SORTED_BAM}.bai" "$DEPTH_TSV" "$BIN_TSV"; do
  if [ ! -s "$output" ]; then
    log "ERROR final validation: missing or empty output $output"
    exit 1
  fi
done
samtools quickcheck "$SORTED_BAM"

log "runall finished. Provenance in $PROV ; outputs under $PWD"
