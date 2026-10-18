#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
project=$PWD
source config/cluster.env
export RAW_DIR VAST_PIPELINE VASTDB SCRATCH_DIR REFERENCE_DIR
test -s "$VAST_PIPELINE/main.nf"
test -s qc/SHA256SUMS.cluster
python3 scripts/make_samplesheets.py "$RAW_DIR" "$project/samples"
mkdir -p logs
ref_job=$(sbatch --parsable --job-name=murielle_refs --qos=normal --time=08:00:00 \
    --output="$project/logs/references.%j.log" scripts/run_pipeline.sbatch references "$project")
rna_job=$(sbatch --parsable --job-name=murielle_rnaseq --dependency="afterok:${ref_job%%;*}" \
    --output="$project/logs/rnaseq.%j.log" scripts/run_pipeline.sbatch rnaseq "$project")
vast_job=$(sbatch --parsable --job-name=murielle_vast --dependency="afterok:${rna_job%%;*}" \
    --output="$project/logs/vast.%j.log" scripts/run_pipeline.sbatch vast "$project")
printf 'References: %s\nRNA-seq: %s\nVAST: %s\n' "$ref_job" "$rna_job" "$vast_job"
