"""Every skill that submits to Slurm ships a thin wrapper around `sbatch`.

Each wrapper had its own copy of the same 25-line test: put a fake `sbatch` on
PATH, run the wrapper, assert the account and the job template reached it. One
table-driven test covers them all, so the next wrapper is one row rather than
another copy.
"""

from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

# wrapper script -> (arguments, the template name that must reach sbatch)
WRAPPERS = {
    "bio-prefect-dask-nextflow/scripts/submit_nextflow.sh": (
        lambda root: [str(root / "main.nf"), "data/*.fastq.gz", str(root / "results")],
        "nextflow-run.sbatch",
    ),
    "tracking-taxonomy-updates/scripts/submit_taxonomy.sh": (
        lambda root: ["gtdbtk", str(root / "bins"), str(root / "out")],
        "taxonomy-tool.sbatch",
    ),
}


class SlurmWrapperTests(unittest.TestCase):
    def test_wrappers_forward_the_account_and_job_template_to_sbatch(self) -> None:
        for relative, (build_args, template) in WRAPPERS.items():
            with self.subTest(wrapper=relative):
                wrapper = REPO_ROOT / "skills" / relative
                self.assertTrue(wrapper.is_file(), wrapper)
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    (root / "bins").mkdir()
                    (root / "main.nf").write_text("nextflow.enable.dsl=2\n", encoding="utf-8")

                    fake_bin = root / "bin"
                    fake_bin.mkdir()
                    sbatch = fake_bin / "sbatch"
                    sbatch.write_text(
                        '#!/usr/bin/env bash\nprintf "%s\\n" "$@"\n', encoding="utf-8"
                    )
                    sbatch.chmod(sbatch.stat().st_mode | stat.S_IXUSR)

                    result = subprocess.run(
                        [str(wrapper), *build_args(root)],
                        cwd=REPO_ROOT,
                        env=os.environ
                        | {
                            "PATH": f"{fake_bin}:{os.environ['PATH']}",
                            "SLURM_ACCOUNT": "test-account",
                        },
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("test-account", result.stdout)
                self.assertIn(template, result.stdout)

    def test_a_wrapper_refuses_to_submit_without_an_account(self) -> None:
        """The account is what binds a job to the right scheduler; submitting
        without it is how a job lands on the wrong cluster."""
        for relative, (build_args, _template) in WRAPPERS.items():
            with self.subTest(wrapper=relative):
                wrapper = REPO_ROOT / "skills" / relative
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    (root / "bins").mkdir()
                    (root / "main.nf").write_text("nextflow.enable.dsl=2\n", encoding="utf-8")
                    env = {k: v for k, v in os.environ.items() if k != "SLURM_ACCOUNT"}
                    result = subprocess.run(
                        [str(wrapper), *build_args(root)],
                        cwd=REPO_ROOT,
                        env=env,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                self.assertNotEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
