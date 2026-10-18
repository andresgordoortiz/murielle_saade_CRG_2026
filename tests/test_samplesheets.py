import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from make_samplesheets import SAMPLES, make_samplesheets


class SampleSheets(unittest.TestCase):
    def test_nine_independent_paired_samples_and_missing_mate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            raw, trimmed, sheets = root / "raw", root / "trimmed", root / "sheets"
            trimmed.mkdir()
            for sample, _, _ in SAMPLES:
                (raw / sample).mkdir(parents=True)
                for mate in (1, 2):
                    (raw / sample / f"{sample}_{mate}.fq.gz").write_bytes(b"test")
                    (trimmed / f"{sample}_R{mate}.fastp.fastq.gz").write_bytes(b"test")
            make_samplesheets(raw, sheets, trimmed)
            with (sheets / "rnaseq.csv").open() as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 9)
            self.assertEqual({r["strandedness"] for r in rows}, {"auto"})
            self.assertEqual(len({r["sample"] for r in rows}), 9)
            with (sheets / "vast_trimmed.csv").open() as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(all(r["type"] == "paired" for r in rows))
            self.assertEqual([r["group"] for r in rows].count("WT"), 3)
            (trimmed / "WT_1_R2.fastp.fastq.gz").unlink()
            with self.assertRaisesRegex(ValueError, "Missing or empty FASTQ"):
                make_samplesheets(raw, sheets, trimmed)


if __name__ == "__main__":
    unittest.main()
