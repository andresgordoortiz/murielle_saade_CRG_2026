#!/usr/bin/env bash
set -euo pipefail
if [[ -z ${SLURM_JOB_ID:-} && -z ${MURIELLE_QC_LIMITED:-} ]]; then
    qc_cpu=$(python3 -c 'import os; print(min(os.sched_getaffinity(0)))')
    export MURIELLE_QC_LIMITED=1
    ulimit -v 3145728
    exec ionice -c 3 nice -n 19 taskset -c "$qc_cpu" bash "$0" "$@"
fi
cd "$(dirname "${BASH_SOURCE[0]}")/.."
raw=${1:-/home/andgortiz/Downloads/Murielle_Saade_API}
mkdir -p qc/fastp
python scripts/inspect_fastq.py "$raw"
for group in WT KO3 KO25; do
    for rep in 1 2 3; do
        sample=${group}_${rep}
        # Reports only: fastp evaluates trimming/filtering without writing altered reads.
        fastp --in1 "qc/subsets/${sample}_1.fq.gz" \
            --in2 "qc/subsets/${sample}_2.fq.gz" --thread 1 \
            --detect_adapter_for_pe --overrepresentation_analysis \
            --json "qc/fastp/$sample.json" --html "qc/fastp/$sample.html" \
            > "qc/fastp/$sample.log" 2>&1
        echo "Finished fastp: $sample"
    done
done
# Full-file scans belong on Slurm; nf-core also scans all raw reads there.
if [[ -n ${SLURM_JOB_ID:-} ]]; then
    seqkit stats --all --tabular --threads 2 "$raw"/*/*.fq.gz > qc/seqkit_stats.tsv
else
    echo 'Full FASTQ scans skipped locally; run on Slurm or use nf-core raw-read QC.'
fi
