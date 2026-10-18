import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from summarize_species import summarize


class SpeciesScreen(unittest.TestCase):
    def test_primary_confident_species_and_strand(self):
        sam = [
            "r\t83\thuman|tx\t1\t60\t150M\t=\t1\t0\tA\tI\tNM:i:1",
            "r\t163\thuman|tx\t1\t60\t150M\t=\t1\t0\tA\tI\tNM:i:1",
            "r\t339\tmouse|tx\t1\t60\t150M\t=\t1\t0\tA\tI\tNM:i:1",
            "x\t0\tmouse|tx\t1\t60\t50M100S\t*\t0\t0\tA\tI\tNM:i:0",
            "y\t0\tmouse|tx\t1\t60\t150M\t*\t0\t0\tA\tI\tNM:i:12",
            "z\t4\t*\t0\t0\t*\t*\t0\t0\tA\tI",
        ]
        result = summarize(sam)
        self.assertEqual(result["primary_reads"], 5)
        self.assertEqual(result["human_confident"], 2)
        self.assertEqual(result["mouse_confident"], 0)
        self.assertEqual(result["human_reverse_R1"], 1)
        self.assertEqual(result["human_reverse_R2"], 0)


if __name__ == "__main__":
    unittest.main()
