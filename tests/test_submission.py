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
            for name in ("scripts", "config", "samples"):
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
            # The cluster login node has a broken Python; submission must never call it.
            (executable / "python3").write_text("#!/bin/sh\necho 'broken login-node Python' >&2\nexit 97\n")
            (executable / "python3").chmod(0o755)
            sbatch = executable / "sbatch"
            sbatch.write_text(
                f"#!{sys.executable}\n"
                "import json,os,sys\n"
                "from pathlib import Path\n"
                "assert os.environ.get('TOWER_ACCESS_TOKEN') == os.environ['EXPECTED_TOKEN']\n"
                "p=Path(os.environ['SUBMIT_LOG'])\n"
                "rows=json.loads(p.read_text()) if p.exists() else []\n"
                "rows.append(sys.argv[1:])\n"
                "p.write_text(json.dumps(rows))\n"
                "print(100+len(rows))\n"
            )
            sbatch.chmod(0o755)
            log = project / "submitted.json"
            env = dict(os.environ, RAW_DIR=str(raw), VAST_PIPELINE=str(vast),
                       EXPECTED_TOKEN="dummy-test-token",
                       SUBMIT_LOG=str(log), PATH=f"{executable}:{os.environ['PATH']}")
            env.pop("TOWER_ACCESS_TOKEN", None)
            result = subprocess.run(["bash", str(project / "scripts/submit.sh")], env=env,
                                    input="dummy-test-token\n", check=True, capture_output=True, text=True)
            self.assertNotIn("dummy-test-token", result.stdout + result.stderr)
            calls = json.loads(log.read_text())
            self.assertEqual(len(calls), 3)
            self.assertIn("--dependency=afterok:101", calls[1])
            self.assertIn("--dependency=afterok:102", calls[2])
            self.assertEqual([call[-2] for call in calls], ["references", "rnaseq", "vast"])
            self.assertTrue(all(call[-1] == str(project) for call in calls))
            self.assertTrue(all("--export=ALL" in call for call in calls))
            log.unlink()
            env["TOWER_ACCESS_TOKEN"] = "dummy-test-token"
            result = subprocess.run(["bash", str(project / "scripts/submit.sh")], input="", env=env,
                                    check=True, capture_output=True, text=True)
            self.assertEqual(len(json.loads(log.read_text())), 3)
            self.assertNotIn("dummy-test-token", result.stdout + result.stderr)
            log.unlink()
            (raw / "WT_1_2.fq.gz").unlink()
            result = subprocess.run(["bash", str(project / "scripts/submit.sh")], input="", env=env,
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Missing or empty FASTQ", result.stderr)
            self.assertFalse(log.exists())

    def test_empty_token_stops_before_submission(self):
        repo = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env.pop("TOWER_ACCESS_TOKEN", None)
        result = subprocess.run(["bash", str(repo / "scripts/submit.sh")], input="\n", env=env,
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("token is required", result.stderr)


if __name__ == "__main__":
    unittest.main()
