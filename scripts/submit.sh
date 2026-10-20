#!/usr/bin/env bash
set -euo pipefail
stage=${1:-all}
case "$stage" in
    all|vast|betas) ;;
    *) echo 'Usage: bash scripts/submit.sh [all|vast|betas]' >&2; exit 2 ;;
esac
cd "$(dirname "${BASH_SOURCE[0]}")/.."
project=$PWD
source config/cluster.env
export RAW_DIR VAST_PIPELINE VASTDB BETAS_REPO SCRATCH_DIR REFERENCE_DIR
if [[ $stage == betas ]]; then
    test -s results/vast/inclusion_tables/murielle_saade_2026_INCLUSION_LEVELS_FULL-hg38.tab
    if [[ ! -s $BETAS_REPO/scripts/run_R.sh ]]; then
        echo "Missing existing betAS environment: $BETAS_REPO/scripts/run_R.sh" >&2
        exit 1
    fi
    mkdir -p logs
    exec sbatch --parsable --export=ALL --output="$project/logs/betas.%A_%a.log" \
        scripts/run_betas.sbatch "$project"
fi
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
dependency=()
if [[ $stage == all ]]; then
    rna_job=$(sbatch --parsable --export=ALL --job-name=murielle_rnaseq \
        --output="$project/logs/rnaseq.%j.log" scripts/run_pipeline.sbatch rnaseq "$project")
    dependency=(--dependency="afterok:${rna_job%%;*}")
    printf 'RNA-seq: %s\n' "$rna_job"
fi
vast_job=$(sbatch --parsable --export=ALL --job-name=murielle_vast "${dependency[@]}" \
    --output="$project/logs/vast.%j.log" scripts/run_pipeline.sbatch vast "$project")
printf 'VAST: %s\n' "$vast_job"
