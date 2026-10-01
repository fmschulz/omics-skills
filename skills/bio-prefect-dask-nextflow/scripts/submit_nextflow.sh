#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
    echo "Usage: SLURM_ACCOUNT=account $0 PIPELINE READS_GLOB RESULT_DIR" >&2
    exit 2
fi
: "${SLURM_ACCOUNT:?Set SLURM_ACCOUNT to the scheduler account}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pipeline="$(realpath "$1")"
reads_glob="$2"
result_dir="$(realpath -m "$3")"
mkdir -p "$result_dir"

# Nextflow writes .nextflow/ and work/ in the launch directory: submit from the
# project root and pin it with --chdir instead of relying on the spooled script path.
exec sbatch --parsable \
    -A "$SLURM_ACCOUNT" \
    --chdir="$PWD" \
    --export="ALL,NXF_PIPELINE=$pipeline,NXF_READS=$reads_glob,NXF_RESULTS=$result_dir" \
    "$script_dir/../templates/nextflow-run.sbatch"
