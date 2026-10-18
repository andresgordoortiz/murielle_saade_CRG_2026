import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from inspect_fastq import pair_id, read_record


class FastqValidation(unittest.TestCase):
    def test_matching_mates_and_valid_record(self):
        one = read_record(io.BytesIO(b"@cluster/1\nACGT\n+\nIIII\n"))
        self.assertEqual(pair_id(one[0], 1), pair_id(b"@cluster/2", 2))
        self.assertEqual(read_record(io.BytesIO(b"@x/1\nA\n+\nK\n"))[3], b"K")
        self.assertIsNone(read_record(io.BytesIO()))

    def test_truncated_or_invalid_records(self):
        for data in (b"@x/1\nACGT\n+\nIII\n", b"x\nA\n+\nI\n", b"@x\nA\n-\nI\n"):
            with self.assertRaises(ValueError):
                read_record(io.BytesIO(data))
        with self.assertRaises(ValueError):
            pair_id(b"@cluster/2", 1)


if __name__ == "__main__":
    unittest.main()
