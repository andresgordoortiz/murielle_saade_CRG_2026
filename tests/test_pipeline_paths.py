import csv
import hashlib
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


class PipelinePaths(unittest.TestCase):
    def test_flat_reads_shared_trimmed_pairs_and_separate_results(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix="murielle pipelines ") as temp:
            project = Path(temp)
            for name in ("scripts", "config"):
                shutil.copytree(repo / name, project / name)
            raw, vast, db = project / "raw_data_2026", project / "shared_vast", project / "VASTDB"
            raw.mkdir()
            vast.mkdir()
            (db / "Hs2").mkdir(parents=True)
            (vast / "main.nf").write_text("workflow {} // ENSMUSG\n")
            (vast / "nextflow.config").write_text("process.executor = 'slurm'\n")
            (project / "qc").mkdir()
            digest = hashlib.sha256(b"test").hexdigest()
            with (project / "qc/SHA256SUMS.cluster").open("w") as manifest:
                for sample, _, _ in SAMPLES:
                    for mate in (1, 2):
                        name = f"{sample}_{mate}.fq.gz"
                        (raw / name).write_bytes(b"test")
                        manifest.write(f"{digest}  {name}\n")
            executable = project / "bin"
            executable.mkdir()
            (executable / "module").write_text(
                '#!/bin/sh\nif [ "$1" = load ] && [ "$2" = Python ]; then touch "$PYTHON_READY"; fi\n'
            )
            (executable / "python3").write_text(
                '#!/bin/sh\n[ -f "$PYTHON_READY" ] || exit 97\n'
                f'exec "{sys.executable}" "$@"\n'
            )
            (executable / "nextflow").write_text(
                f"#!{sys.executable}\n"
                "import csv,json,os,sys\n"
                "from pathlib import Path\n"
                "args=sys.argv[1:]\n"
                "assert os.environ.get('TOWER_ACCESS_TOKEN') == 'dummy-test-token'\n"
                "def value(flag): return args[args.index(flag)+1]\n"
                "out=Path(value('--outdir'))\n"
                "if '--input' in args:\n"
                "    (out/'fastp').mkdir(parents=True)\n"
                "    with open(value('--input')) as handle: rows=list(csv.DictReader(handle))\n"
                "    for row in rows:\n"
                "        for mate in (1,2): (out/'fastp'/f\"{row['sample']}_R{mate}.fastp.fastq.gz\").write_bytes(b'test')\n"
                "Path(os.environ['COMMAND_LOG']).write_text(json.dumps(args))\n"
            )
            for path in executable.iterdir():
                path.chmod(0o755)
            log = project / "command.json"
            env = dict(os.environ, VAST_PIPELINE=str(vast), VASTDB=str(db),
                       TOWER_ACCESS_TOKEN="dummy-test-token",
                       PYTHON_READY=str(project / "python-module-loaded"),
                       SCRATCH_DIR=str(project / "scratch"), COMMAND_LOG=str(log),
                       PATH=f"{executable}:{os.environ['PATH']}")
            for name in ("RAW_DIR", "REFERENCE_DIR", "PROJECT_DIR"):
                env.pop(name, None)
            for stage in ("rnaseq", "vast"):
                Path(env["PYTHON_READY"]).unlink(missing_ok=True)
                subprocess.run(["bash", str(project / "scripts/run_pipeline.sbatch"), stage, str(project)],
                               env=env, check=True, capture_output=True, text=True)
                args = json.loads(log.read_text())
                def value(flag):
                    return args[args.index(flag) + 1]
                self.assertEqual(value("--outdir"), str(project / "results" / stage))
                self.assertIn("-with-tower", args)
                self.assertNotIn("dummy-test-token", args)
                self.assertEqual(value("-work-dir"), str(project / "scratch/murielle_saade_CRG_2026" / f"work_{stage}"))
                if stage == "rnaseq":
                    self.assertIn("GRCh38", value("--fasta"))
                    self.assertEqual(value("--input"), str(project / "samples/rnaseq.csv"))
                else:
                    self.assertEqual(value("--species"), "hg38")
                    self.assertEqual(args[1], str(project / "runs/vast/main.nf"))
                    for flag in ("--skip_trimming", "--skip_compare", "--skip_matt", "--skip_betas"):
                        self.assertIn(flag, args)
                    with open(value("--sample_csv")) as handle:
                        rows = list(csv.DictReader(handle))
                    self.assertEqual(len(rows), 9)
                    self.assertTrue(all(Path(row["fastq_1"]).is_file() for row in rows))
                    self.assertTrue(all(row["type"] == "paired" for row in rows))
            self.assertIn("ENSMUSG", (vast / "main.nf").read_text())
            self.assertNotIn("ENSMUSG", (project / "runs/vast/main.nf").read_text())


if __name__ == "__main__":
    unittest.main()
