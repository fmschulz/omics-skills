#!/usr/bin/env bash
set -euo pipefail

# sbatch also reads SBATCH_CLUSTERS, SBATCH_PARTITION, and SBATCH_QOS from the
# environment; set them for sites that need a cluster, partition, or QOS.
# Run from the project root, or set PROJECT_ROOT. The job starts there
# (--chdir); the root is never derived from this script's path.
if [[ $# -ne 3 ]]; then
    echo "Usage: [PROJECT_ROOT=dir] SLURM_ACCOUNT=account $0 TOOL INPUT OUTPUT_DIR" >&2
    exit 2
fi
: "${SLURM_ACCOUNT:?Set SLURM_ACCOUNT to the scheduler account}"
tool="$1"
case "$tool" in
    gtdbtk|eukcc|vcontact3|gvclass) ;;
    *) echo "Unsupported taxonomy tool: $tool" >&2; exit 2 ;;
esac

project_root="$(realpath "${PROJECT_ROOT:-$PWD}")"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
input="$(realpath "$2")"
output="$(realpath -m "$3")"
mkdir -p "$output"

exec sbatch --parsable \
    -A "$SLURM_ACCOUNT" \
    --chdir="$project_root" \
    --export="ALL,TAXONOMY_TOOL=$tool,TAXONOMY_INPUT=$input,TAXONOMY_OUTPUT=$output" \
    "$script_dir/../templates/taxonomy-tool.sbatch"
