#!/usr/bin/env python3
"""Generate sheets for the observed nine samples; require intact directory layout."""
import argparse
import csv
from pathlib import Path

SAMPLES = [(f"{group}_{rep}", group, rep) for group in ("WT", "KO3", "KO25") for rep in (1, 2, 3)]


def make_samplesheets(raw, outdir, trimmed=None):
    raw = raw.resolve()
    raw_pairs = [[raw / sample / f"{sample}_{mate}.fq.gz" for mate in (1, 2)]
                 for sample, _, _ in SAMPLES]
    trimmed_pairs = ([[trimmed.resolve() / f"{sample}_R{mate}.fastp.fastq.gz" for mate in (1, 2)]
                      for sample, _, _ in SAMPLES] if trimmed else [])
    for pair in raw_pairs + trimmed_pairs:
        for path in pair:
            if not path.is_file() or not path.stat().st_size:
                raise ValueError(f"Missing or empty FASTQ: {path}")
    outdir.mkdir(parents=True, exist_ok=True)
    with (outdir / "rnaseq.csv").open("w") as out:
        writer = csv.writer(out)
        writer.writerow(["sample", "fastq_1", "fastq_2", "strandedness"])
        for (sample, _, _), pair in zip(SAMPLES, raw_pairs):
            writer.writerow([sample, *pair, "auto"])
    with (outdir / "vast_raw.csv").open("w") as out:
        writer = csv.writer(out)
        writer.writerow(["sample", "fastq_1", "fastq_2", "type", "group"])
        for (sample, group, _), pair in zip(SAMPLES, raw_pairs):
            writer.writerow([sample, *(p.relative_to(raw) for p in pair), "paired", group])
    with (outdir / "metadata.tsv").open("w") as out:
        writer = csv.writer(out, delimiter="\t")
        writer.writerow(["sample", "condition", "replicate"])
        writer.writerows(SAMPLES)
    if trimmed:
        with (outdir / "vast_trimmed.csv").open("w") as out:
            writer = csv.writer(out)
            writer.writerow(["sample", "fastq_1", "fastq_2", "type", "group"])
            for (sample, group, _), pair in zip(SAMPLES, trimmed_pairs):
                writer.writerow([sample, *pair, "paired", group])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("outdir", type=Path)
    parser.add_argument("--trimmed", type=Path)
    args = parser.parse_args()
    make_samplesheets(args.raw, args.outdir, args.trimmed)


if __name__ == "__main__":
    main()
