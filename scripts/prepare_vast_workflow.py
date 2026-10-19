#!/usr/bin/env python3
"""Copy the shared VAST workflow with junction filters that retain human genes."""
import argparse
from pathlib import Path


def fix_eej2_filters(source):
    lines = []
    for line in source.replace("ENSMUSG", "ENS[A-Z]*G").splitlines(keepends=True):
        if "grep " in line and "'^ENS[A-Z]*G" in line:
            # grep status 1 means zero matches; real read/regex errors must still fail.
            line = line.replace("|| echo 0", r"|| [ \$? -eq 1 ]")
            if "grep -aP " in line and " || " not in line:
                line = line.rstrip("\n") + r" || [ \$? -eq 1 ]" + "\n"
        lines.append(line)
    return "".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.target.resolve():
        parser.error("Target must be a working copy, not the shared workflow")
    args.target.parent.mkdir(parents=True, exist_ok=True)
    args.target.write_text(fix_eej2_filters(args.source.read_text()))


if __name__ == "__main__":
    main()
