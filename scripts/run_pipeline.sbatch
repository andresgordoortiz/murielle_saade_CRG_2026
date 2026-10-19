#!/bin/bash -l
#SBATCH --job-name=murielle
#SBATCH --partition=genoa64
#SBATCH --qos=pipelines
#SBATCH --cpus-per-task=1
#SBATCH --mem=6G
#SBATCH --no-requeue

set -euo pipefail
stage=${1:?Usage: run_pipeline.sbatch references|rnaseq|vast PROJECT_DIR}
PROJECT_DIR=${2:?Missing project directory}
cd "$PROJECT_DIR"
source config/cluster.env
export RAW_DIR VAST_PIPELINE VASTDB SCRATCH_DIR REFERENCE_DIR
mkdir -p "$SCRATCH_DIR" logs results runs

if [[ $stage == references ]]; then
    exec bash scripts/prepare_references.sh
fi

module load Nextflow
module load Java
module load Singularity/4.0.2
export NXF_VER=25.10.4
export NXF_JVM_ARGS='-Xms1g -Xmx5g'
export NXF_OPTS='-XX:ActiveProcessorCount=2'
export SLURM_CONF=${SLURM_CONF:-/etc/slurm/slurm.conf}
export SLURM_EXPORT_ENV=ALL
export NXF_SINGULARITY_CACHEDIR=$SCRATCH_DIR/singularity
mkdir -p "$NXF_SINGULARITY_CACHEDIR" "runs/$stage"
seqera_args=()
if [[ -n ${TOWER_ACCESS_TOKEN:-} ]]; then
    seqera_args=(-with-tower)
fi

case "$stage" in
    rnaseq)
        (cd "$RAW_DIR" && sha256sum -c "$PROJECT_DIR/qc/SHA256SUMS.cluster")
        python3 scripts/make_samplesheets.py "$RAW_DIR" "$PROJECT_DIR/samples"
        cd runs/rnaseq
        exec nextflow run nf-core/rnaseq -r 3.27.0 \
            -profile singularity -c "$PROJECT_DIR/config/crg.config" \
            -params-file "$PROJECT_DIR/config/rnaseq.json" \
            --input "$PROJECT_DIR/samples/rnaseq.csv" \
            --fasta "$REFERENCE_DIR/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz" \
            --gtf "$REFERENCE_DIR/Homo_sapiens.GRCh38.115.gtf.gz" \
            --outdir "$PROJECT_DIR/results/rnaseq" \
            -work-dir "$SCRATCH_DIR/murielle_saade_CRG_2026/work_rnaseq" -resume -ansi-log false "${seqera_args[@]}"
        ;;
    vast)
        test -s "$VAST_PIPELINE/main.nf"
        test -d "$VASTDB/Hs2"
        python3 scripts/make_samplesheets.py "$RAW_DIR" "$PROJECT_DIR/samples" \
            --trimmed "$PROJECT_DIR/results/rnaseq/fastp"
        python3 scripts/prepare_vast_workflow.py "$VAST_PIPELINE/main.nf" "$PROJECT_DIR/runs/vast/main.nf"
        cd runs/vast
        exec nextflow run "$PROJECT_DIR/runs/vast/main.nf" \
            -c "$VAST_PIPELINE/nextflow.config" -c "$PROJECT_DIR/config/crg.config" \
            --sample_csv "$PROJECT_DIR/samples/vast_trimmed.csv" \
            --data_dir "$PROJECT_DIR/results/rnaseq/fastp" \
            --vastdb_path "$VASTDB" --species hg38 \
            --project_name murielle_saade_2026 --outdir "$PROJECT_DIR/results/vast" \
            --skip_trimming --skip_fastqc --skip_compare --skip_matt --skip_betas \
            -work-dir "$SCRATCH_DIR/murielle_saade_CRG_2026/work_vast" -resume -ansi-log false "${seqera_args[@]}"
        ;;
    *) echo "Unknown stage: $stage" >&2; exit 2 ;;
esac
