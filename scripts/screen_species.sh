#!/usr/bin/env bash
set -euo pipefail
if [[ -z ${SLURM_JOB_ID:-} ]]; then
    echo 'Run species screening on Slurm with 4 CPUs and at least 12 GB RAM; the index uses about 7 GB.' >&2
    exit 2
fi
cd "$(dirname "${BASH_SOURCE[0]}")/.."
mkdir -p qc/references qc/species_alignments
for species in human mouse; do
    if [[ $species == human ]]; then
        organism=homo_sapiens
        assembly=Homo_sapiens.GRCh38
    else
        organism=mus_musculus
        assembly=Mus_musculus.GRCm39
    fi
    for kind in cdna ncrna; do
        ref=qc/references/$species.$kind.fa.gz
        suffix=$kind
        [[ $kind != cdna ]] || suffix=cdna.all
        if [[ ! -s $ref ]]; then
            curl -fL --retry 3 "https://ftp.ensembl.org/pub/release-115/fasta/$organism/$kind/$assembly.$suffix.fa.gz" \
                -o "$ref.part"
            mv "$ref.part" "$ref"
        fi
    done
done
python scripts/summarize_species.py --build-reference
minimap2 -x sr -t 4 -d qc/references/human_mouse.mmi qc/references/human_mouse.fa \
    2> qc/references/minimap2_index.log
for r1 in qc/subsets/*_1.fq.gz; do
    sample=$(basename "$r1" _1.fq.gz)
    minimap2 -ax sr --secondary=no -t 4 qc/references/human_mouse.mmi \
        "$r1" "qc/subsets/${sample}_2.fq.gz" \
        2> "qc/species_alignments/$sample.log" \
        | samtools view -b -o "qc/species_alignments/$sample.bam"
done
python scripts/summarize_species.py
