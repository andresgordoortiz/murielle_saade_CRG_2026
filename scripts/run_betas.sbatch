#!/bin/bash -l
#SBATCH --job-name=murielle_betAS
#SBATCH --partition=genoa64
#SBATCH --qos=vlong
#SBATCH --time=2-00:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --array=0-2
#SBATCH --no-requeue

set -euo pipefail
PROJECT_DIR=${1:?Missing project directory}
cd "$PROJECT_DIR"
source config/cluster.env
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export TMPDIR=$SCRATCH_DIR/murielle_saade_CRG_2026/betas/${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}
mkdir -p "$TMPDIR"
comparisons=(WT_vs_KO3 WT_vs_KO25 KO3_vs_KO25)
exec bash "$BETAS_REPO/scripts/run_R.sh" "$PROJECT_DIR/scripts/run_betas.R" \
    "$PROJECT_DIR" "${comparisons[$SLURM_ARRAY_TASK_ID]}"
