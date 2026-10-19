#!/usr/bin/env bash
set -euo pipefail
: "${REFERENCE_DIR:?Source config/cluster.env first}"
: "${VASTDB:?Source config/cluster.env first}"
if [[ ! -s $VASTDB/Hs2/FILES/gDNA.1.ebwt ]]; then
    echo "Missing or incomplete installed Hs2 database: $VASTDB/Hs2" >&2
    exit 1
fi
for name in Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz Homo_sapiens.GRCh38.115.gtf.gz; do
    if [[ ! -s $REFERENCE_DIR/$name ]]; then
        echo "Missing RNA-seq reference: $REFERENCE_DIR/$name" >&2
        echo 'Set REFERENCE_DIR in config/cluster.env to the existing genome/GTF directory. No files will be downloaded.' >&2
        exit 1
    fi
    echo "Using existing reference: $REFERENCE_DIR/$name"
done
echo "Using existing VASTDB: $VASTDB/Hs2"
