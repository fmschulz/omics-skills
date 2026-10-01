#!/usr/bin/env bash
#SBATCH --job-name=taxonomy-route
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=24:00:00

set -euo pipefail
: "${TAXONOMY_TOOL:?Missing TAXONOMY_TOOL}"
: "${TAXONOMY_INPUT:?Missing TAXONOMY_INPUT}"
: "${TAXONOMY_OUTPUT:?Missing TAXONOMY_OUTPUT}"
mkdir -p "$TAXONOMY_OUTPUT"
threads="${SLURM_CPUS_PER_TASK:-16}"

case "$TAXONOMY_TOOL" in
    gtdbtk)
        : "${GTDBTK_DATA_PATH:?Set GTDBTK_DATA_PATH}"
        gtdbtk check_install
        gtdbtk classify_wf --genome_dir "$TAXONOMY_INPUT" --out_dir "$TAXONOMY_OUTPUT" \
            --cpus "$threads" -x "${GTDBTK_EXTENSION:-fa}"
        ;;
    eukcc)
        : "${EUKCC2_DB:?Set EUKCC2_DB}"
        eukcc folder --db "$EUKCC2_DB" --out "$TAXONOMY_OUTPUT" --threads "$threads" "$TAXONOMY_INPUT"
        ;;
    vcontact3)
        # vConTACT3 requires --db-path and defaults --threads to every CPU on the node.
        : "${VCONTACT3_DB:?Set VCONTACT3_DB to the vcontact3 prepare_databases location}"
        vcontact3 run --nucleotide "$TAXONOMY_INPUT" --output "$TAXONOMY_OUTPUT" \
            --db-path "$VCONTACT3_DB" --threads "$threads"
        ;;
    gvclass)
        gvclass "$TAXONOMY_INPUT" -o "$TAXONOMY_OUTPUT" -t "$threads"
        ;;
esac

find "$TAXONOMY_OUTPUT" -type f -size +0c -print -quit | grep -q .
