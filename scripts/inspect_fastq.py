#!/usr/bin/env python3
"""Verify supplied SHA256s; validate and save the first 100,000 pairs per sample."""
import argparse
import csv
import gzip
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def read_record(handle):
    header = handle.readline().rstrip(b"\r\n")
    if not header:
        return None
    sequence, plus, quality = [handle.readline().rstrip(b"\r\n") for _ in range(3)]
    if not header.startswith(b"@") or not plus.startswith(b"+"):
        raise ValueError(f"Invalid FASTQ record: {header!r}")
    if not sequence or len(sequence) != len(quality) or min(quality) < 33 or max(quality) > 126:
        raise ValueError(f"Invalid sequence/Phred+33 quality: {header!r}")
    return header, sequence, plus, quality


def pair_id(header, mate):
    name = header.split()[0]
    if name.endswith((b"/1", b"/2")):
        if not name.endswith(f"/{mate}".encode()):
            raise ValueError(f"Wrong mate suffix: {header!r}")
        name = name[:-2]
    return name


def inspect_pair(r1, outdir, pairs):
    sample = r1.parent.name
    r2 = r1.with_name(f"{sample}_2.fq.gz")
    lengths = [set(), set()]
    first = []
    count = 0
    with gzip.open(r1, "rb") as a, gzip.open(r2, "rb") as b, \
            gzip.open(outdir / f"{sample}_1.fq.gz", "wb") as x, \
            gzip.open(outdir / f"{sample}_2.fq.gz", "wb") as y:
        for _ in range(pairs):
            one, two = read_record(a), read_record(b)
            if one is None or two is None:
                if one != two:
                    raise ValueError(f"Unequal mate counts: {sample}")
                break
            if pair_id(one[0], 1) != pair_id(two[0], 2):
                raise ValueError(f"Unsynchronized mates: {sample}, pair {count + 1}")
            if not first:
                first = [one[0].decode(), two[0].decode()]
            for i, (record, output) in enumerate(((one, x), (two, y))):
                lengths[i].add(len(record[1]))
                output.write(b"\n".join(record) + b"\n")
            count += 1
    return dict(sample=sample, pairs_checked=count, first_headers=first,
                r1_lengths=sorted(lengths[0]), r2_lengths=sorted(lengths[1]))


def checksum(item):
    path, expected = item
    with path.open("rb") as handle:
        actual = hashlib.file_digest(handle, "sha256").hexdigest()
    if actual != expected:
        raise ValueError(f"SHA256 mismatch: {path}")
    return path, actual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("--outdir", type=Path, default=Path("qc"))
    parser.add_argument("--pairs", type=int, default=100_000)
    args = parser.parse_args()
    if args.pairs < 1:
        parser.error("--pairs must be positive")
    files = sorted(args.raw.glob("*/*_1.fq.gz"))
    expected_samples = {f"{group}_{rep}" for group in ("WT", "KO3", "KO25") for rep in (1, 2, 3)}
    if {p.parent.name for p in files} != expected_samples or len(list(args.raw.glob("*/*.fq.gz"))) != 18:
        raise ValueError("Expected exactly nine samples and eighteen FASTQs")
    subset_dir = args.outdir / "subsets"
    subset_dir.mkdir(parents=True, exist_ok=True)
    checked = [inspect_pair(path, subset_dir, args.pairs) for path in files]
    (args.outdir / "pairing.json").write_text(json.dumps(checked, indent=2) + "\n")
    entries = {}
    for line in (args.raw / "SHA256SUMS.flat").read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        entries[name.lstrip("*")] = digest
    all_files = sorted(args.raw.glob("*/*.fq.gz"))
    if set(entries) != {p.name for p in all_files}:
        raise ValueError("Checksum manifest does not match FASTQ inventory")
    with ThreadPoolExecutor(max_workers=2) as pool:
        verified = list(pool.map(checksum, [(p, entries[p.name]) for p in all_files]))
    with (args.outdir / "SHA256SUMS.cluster").open("w") as handle:
        for path, digest in verified:
            handle.write(f"{digest}  {path.name}\n")
    with (args.outdir / "inventory.tsv").open("w") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["sample", "mate", "bytes", "relative_path", "sha256"])
        for path, digest in verified:
            writer.writerow([path.parent.name, path.stem.split("_")[-1].split(".")[0],
                             path.stat().st_size, str(path.relative_to(args.raw)), digest])
    print(f"Validated {len(verified)} SHA256s and {sum(x['pairs_checked'] for x in checked):,} paired records")


if __name__ == "__main__":
    main()
