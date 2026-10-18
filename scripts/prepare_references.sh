#!/usr/bin/env bash
set -euo pipefail
: "${REFERENCE_DIR:?Source config/cluster.env first}"
: "${VASTDB:?Source config/cluster.env first}"
mkdir -p "$REFERENCE_DIR" "$VASTDB"

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
if [[ ! -d $VASTDB/Hs2 ]]; then
    archive=$REFERENCE_DIR/vastdb.hs2.23.06.20.tar.gz
    download https://vastdb.crg.eu/libs/vastdb.hs2.23.06.20.tar.gz "$archive"
    staging=$(mktemp -d "$VASTDB/.murielle_Hs2.XXXXXX")
    trap 'rm -rf "$staging"' EXIT
    tar -xzf "$archive" -C "$staging"
    mv -T "$staging/Hs2" "$VASTDB/Hs2"
fi
test -s "$VASTDB/Hs2/FILES/gDNA.1.ebwt"
