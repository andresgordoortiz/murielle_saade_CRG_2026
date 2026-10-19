#!/usr/bin/env bash
set -euo pipefail
: "${REFERENCE_DIR:?Source config/cluster.env first}"
: "${VASTDB:?Source config/cluster.env first}"
if [[ ! -s $VASTDB/Hs2/FILES/gDNA.1.ebwt ]]; then
    echo "Missing or incomplete installed Hs2 database: $VASTDB/Hs2" >&2
    exit 1
fi
mkdir -p "$REFERENCE_DIR"

download() {
    local url=$1 target=$2
    if [[ ! -s $target ]]; then
        curl -fL --retry 3 --connect-timeout 30 "$url" -o "$target.part"
        gzip -t "$target.part"
        mv "$target.part" "$target"
    fi
}

download https://ftp.ensembl.org/pub/release-115/fasta/homo_sapiens/dna/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz \
    "$REFERENCE_DIR/Homo_sapiens.GRCh38.dna.primary_assembly.fa.gz"
download https://ftp.ensembl.org/pub/release-115/gtf/homo_sapiens/Homo_sapiens.GRCh38.115.gtf.gz \
    "$REFERENCE_DIR/Homo_sapiens.GRCh38.115.gtf.gz"
