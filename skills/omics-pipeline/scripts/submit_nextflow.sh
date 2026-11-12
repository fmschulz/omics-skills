#!/usr/bin/env bash
# Submit a Nextflow launcher job through Slurm.
# Usage: SLURM_ACCOUNT=account [PROJECT_ROOT=dir] submit_nextflow.sh PIPELINE READS_GLOB RESULT_DIR
# The caller passes the account; partition, QOS and cluster come from the
# SBATCH_PARTITION, SBATCH_QOS and SBATCH_CLUSTERS environment variables.
set -euo pipefail

if [[ $# -ne 3 ]]; then
    echo "Usage: SLURM_ACCOUNT=account $0 PIPELINE READS_GLOB RESULT_DIR" >&2
    exit 2
fi
: "${SLURM_ACCOUNT:?Set SLURM_ACCOUNT to the scheduler account}"

# cd and pwd -P resolve a path on GNU and BSD systems; realpath is not portable
# (macOS has no -m).
pipeline_dir="$(cd "$(dirname "$1")" && pwd -P)"
pipeline="$pipeline_dir/$(basename "$1")"
reads_glob="$2"
mkdir -p "$3"
result_dir="$(cd "$3" && pwd -P)"
# Nextflow writes .nextflow/ and work/ in the launch directory. Slurm spools the
# batch script, so pin the project root with --chdir instead of deriving it
# from the script path.
project_root="$(cd "${PROJECT_ROOT:-$PWD}" && pwd -P)"
mkdir -p "$result_dir/run-metadata"

launcher="$result_dir/run-metadata/nextflow-run.sbatch"
cat > "$launcher" <<'SBATCH'
#!/usr/bin/env bash
#SBATCH --job-name=nextflow-launch
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=24:00:00

set -euo pipefail
: "${NXF_PIPELINE:?Missing NXF_PIPELINE}"
: "${NXF_READS:?Missing NXF_READS}"
: "${NXF_RESULTS:?Missing NXF_RESULTS}"

mkdir -p "$NXF_RESULTS/run-metadata"
nextflow run "$NXF_PIPELINE" \
    -profile slurm \
    -resume \
    --reads "$NXF_READS" \
    --outdir "$NXF_RESULTS" \
    -with-trace "$NXF_RESULTS/run-metadata/trace.tsv" \
    -with-report "$NXF_RESULTS/run-metadata/report.html" \
    -with-timeline "$NXF_RESULTS/run-metadata/timeline.html"

test -s "$NXF_RESULTS/run-metadata/trace.tsv"
find "$NXF_RESULTS" -type f -size +0c ! -path '*/run-metadata/*' -print -quit | grep -q .
SBATCH

exec sbatch --parsable \
    -A "$SLURM_ACCOUNT" \
    --chdir="$project_root" \
    --export="ALL,NXF_PIPELINE=$pipeline,NXF_READS=$reads_glob,NXF_RESULTS=$result_dir" \
    "$launcher"
