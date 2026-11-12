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

# cd and pwd -P resolve a path on GNU and BSD systems; realpath -m is GNU only.
project_root="$(cd "${PROJECT_ROOT:-$PWD}" && pwd -P)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
input_dir="$(cd "$(dirname "$2")" && pwd -P)"
input="$input_dir/$(basename "$2")"
mkdir -p "$3"
output="$(cd "$3" && pwd -P)"
# The template writes its Slurm logs to logs/ in the project root; Slurm does
# not create the directory, and a job whose log directory is missing fails.
mkdir -p "$project_root/logs"

exec sbatch --parsable \
    -A "$SLURM_ACCOUNT" \
    --chdir="$project_root" \
    --export="ALL,TAXONOMY_TOOL=$tool,TAXONOMY_INPUT=$input,TAXONOMY_OUTPUT=$output" \
    "$script_dir/../templates/taxonomy-tool.sbatch"
