#!/usr/bin/env bash
set -euo pipefail
# Supply TOWER_ACCESS_TOKEN in the environment, or paste it at the hidden prompt.
if [[ -z ${TOWER_ACCESS_TOKEN:-} ]]; then
    read -r -s -p 'Seqera access token: ' TOWER_ACCESS_TOKEN
    printf '\n'
fi
if [[ -z $TOWER_ACCESS_TOKEN ]]; then
    echo 'A Seqera access token is required.' >&2
    exit 1
fi
export TOWER_ACCESS_TOKEN
cd "$(dirname "${BASH_SOURCE[0]}")/.."
project=$PWD
source config/cluster.env
export RAW_DIR VAST_PIPELINE VASTDB SCRATCH_DIR REFERENCE_DIR
test -s "$VAST_PIPELINE/main.nf"
test -s "$VAST_PIPELINE/nextflow.config"
test -s samples/SHA256SUMS
bash scripts/check_references.sh
while IFS=$'\t' read -r sample condition replicate; do
    [[ $sample == sample ]] && continue
    for mate in 1 2; do
        fastq=$RAW_DIR/${sample}_${mate}.fq.gz
        if [[ ! -s $fastq ]]; then
            echo "Missing or empty FASTQ: $fastq" >&2
            exit 1
        fi
    done
done < samples/metadata.tsv
mkdir -p logs
rna_job=$(sbatch --parsable --export=ALL --job-name=murielle_rnaseq \
    --output="$project/logs/rnaseq.%j.log" scripts/run_pipeline.sbatch rnaseq "$project")
vast_job=$(sbatch --parsable --export=ALL --job-name=murielle_vast --dependency="afterok:${rna_job%%;*}" \
    --output="$project/logs/vast.%j.log" scripts/run_pipeline.sbatch vast "$project")
printf 'RNA-seq: %s\nVAST: %s\n' "$rna_job" "$vast_job"
