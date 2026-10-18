#!/usr/bin/env python3
"""Competitive transcriptome screen, not a comprehensive contamination assay."""
import argparse
import csv
import gzip
import re
import subprocess
from collections import Counter
from pathlib import Path


def build_reference():
    with Path("qc/references/human_mouse.fa").open("w") as out:
        for species in ("human", "mouse"):
            for kind in ("cdna", "ncrna"):
                with gzip.open(f"qc/references/{species}.{kind}.fa.gz", "rt") as handle:
                    for line in handle:
                        out.write(f">{species}|{line[1:]}" if line.startswith(">") else line)


def summarize(lines):
    stats = Counter()
    genes = set()
    for line in lines:
        fields = line.rstrip().split("\t")
        if line.startswith("@"):
            continue
        flag, mapq = int(fields[1]), int(fields[4])
        if flag & (256 | 2048):
            continue
        stats["primary_reads"] += 1
        if flag & 4:
            continue
        species = fields[2].split("|")[0]
        stats[f"{species}_mapped"] += 1
        aligned = sum(int(n) for n, op in re.findall(r"(\d+)([MIDNSHP=X])", fields[5]) if op in "MI=X")
        nm = next((int(tag[5:]) for tag in fields[11:] if tag.startswith("NM:i:")), aligned)
        if mapq < 20 or aligned < 100 or nm > 7:
            continue
        stats[f"{species}_confident"] += 1
        genes.add(fields[2])
        if species == "human":
            stats["human_confident_R1" if flag & 64 else "human_confident_R2"] += 1
            if flag & 16:
                stats["human_reverse_R1" if flag & 64 else "human_reverse_R2"] += 1
    stats["confident_transcripts"] = len(genes)
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-reference", action="store_true")
    args = parser.parse_args()
    if args.build_reference:
        build_reference()
        return
    columns = ["sample", "primary_reads", "human_mapped", "mouse_mapped", "human_confident",
               "mouse_confident", "confident_transcripts", "human_confident_R1", "human_reverse_R1",
               "human_confident_R2", "human_reverse_R2"]
    with Path("qc/species_screen.tsv").open("w") as out:
        writer = csv.DictWriter(out, fieldnames=columns, delimiter="\t")
        writer.writeheader()
        for bam in sorted(Path("qc/species_alignments").glob("*.bam")):
            with subprocess.Popen(["samtools", "view", str(bam)], stdout=subprocess.PIPE, text=True) as proc:
                row = summarize(proc.stdout)
                if proc.wait():
                    raise RuntimeError(f"samtools failed: {bam}")
            writer.writerow({"sample": bam.stem, **{key: row[key] for key in columns[1:]}})


if __name__ == "__main__":
    main()
