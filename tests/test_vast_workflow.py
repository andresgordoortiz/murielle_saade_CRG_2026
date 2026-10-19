import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_vast_workflow import fix_eej2_filters


class HumanJunctionFilters(unittest.TestCase):
    def test_human_and_mouse_records_survive_and_empty_files_are_valid(self):
        source = r'''valid=\$(grep -cP '^ENSMUSG\\d+\\t\\d+-\\d+\\t' "\$eej2" 2>/dev/null || echo 0)
grep -aP '^ENSMUSG\\d+\\t\\d+-\\d+\\t' "\$eej2" > "\${eej2}.clean" 2>/dev/null
'''
        patched = fix_eej2_filters(source)
        self.assertEqual(fix_eej2_filters(patched), patched)
        # Render the escaping used inside the Nextflow multiline script.
        bash = patched.replace(r"\\", "\\").replace(r"\$", "$")
        with tempfile.TemporaryDirectory() as temp:
            eej2 = Path(temp) / "sample.eej2"
            for data, expected in (
                ("ENSG000001\t1-2\t3\tNA\t4\nENSMUSG000001\t2-3\t4\tNA\t5\njunk\n", 2),
                ("", 0),
                ("corrupt\n", 0),
            ):
                eej2.write_text(data)
                result = subprocess.run(["bash", "-euc", bash + '\nprintf "%s" "$valid"',
                                         "test", str(eej2)],
                                        env={"eej2": str(eej2)}, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, str(expected))
                cleaned = Path(f"{eej2}.clean").read_text()
                self.assertEqual(len(cleaned.splitlines()), expected)
                self.assertNotIn("junk", cleaned)
            eej2.unlink()
            result = subprocess.run(["bash", "-euc", bash], env={"eej2": str(eej2)},
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
