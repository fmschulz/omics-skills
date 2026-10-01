#!/usr/bin/env bash
set -euo pipefail

# sbatch also reads SBATCH_CLUSTERS, SBATCH_PARTITION, and SBATCH_QOS from the
# environment; set them for sites that need a cluster, partition, or QOS.
if [[ $# -ne 3 ]]; then
    echo "Usage: SLURM_ACCOUNT=account $0 TOOL INPUT OUTPUT_DIR" >&2
    exit 2
fi
: "${SLURM_ACCOUNT:?Set SLURM_ACCOUNT to the scheduler account}"
tool="$1"
case "$tool" in
    gtdbtk|eukcc|vcontact3|gvclass) ;;
    *) echo "Unsupported taxonomy tool: $tool" >&2; exit 2 ;;
esac

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
input="$(realpath "$2")"
output="$(realpath -m "$3")"
mkdir -p "$output"

exec sbatch --parsable \
    -A "$SLURM_ACCOUNT" \
    --export="ALL,TAXONOMY_TOOL=$tool,TAXONOMY_INPUT=$input,TAXONOMY_OUTPUT=$output" \
    "$script_dir/../templates/taxonomy-tool.sbatch"
