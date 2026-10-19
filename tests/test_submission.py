import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from make_samplesheets import SAMPLES


class ClusterSubmission(unittest.TestCase):
    def test_success_dependencies_and_paths_with_spaces(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix="murielle launch ") as temp:
            project = Path(temp)
            for name in ("scripts", "config"):
                shutil.copytree(repo / name, project / name)
            raw, vast = project / "raw", project / "vast"
            raw.mkdir()
            vast.mkdir()
            (vast / "main.nf").write_text("workflow {}\n")
            (vast / "nextflow.config").write_text("process.executor = 'slurm'\n")
            (project / "qc").mkdir()
            (project / "qc/SHA256SUMS.cluster").write_text("placeholder\n")
            for sample, _, _ in SAMPLES:
                for mate in (1, 2):
                    (raw / f"{sample}_{mate}.fq.gz").write_bytes(b"test")
            executable = project / "bin"
            executable.mkdir()
            sbatch = executable / "sbatch"
            sbatch.write_text(
                f"#!{sys.executable}\n"
                "import json,os,sys\n"
                "from pathlib import Path\n"
                "p=Path(os.environ['SUBMIT_LOG'])\n"
                "rows=json.loads(p.read_text()) if p.exists() else []\n"
                "rows.append(sys.argv[1:])\n"
                "p.write_text(json.dumps(rows))\n"
                "print(100+len(rows))\n"
            )
            sbatch.chmod(0o755)
            log = project / "submitted.json"
            env = dict(os.environ, RAW_DIR=str(raw), VAST_PIPELINE=str(vast),
                       SUBMIT_LOG=str(log), PATH=f"{executable}:{os.environ['PATH']}")
            subprocess.run(["bash", str(project / "scripts/submit.sh")], env=env,
                           check=True, capture_output=True, text=True)
            calls = json.loads(log.read_text())
            self.assertEqual(len(calls), 3)
            self.assertIn("--dependency=afterok:101", calls[1])
            self.assertIn("--dependency=afterok:102", calls[2])
            self.assertEqual([call[-2] for call in calls], ["references", "rnaseq", "vast"])
            self.assertTrue(all(call[-1] == str(project) for call in calls))


if __name__ == "__main__":
    unittest.main()
