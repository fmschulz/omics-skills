from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "bio-prefect-dask-nextflow"


class PrefectDaskNextflowTests(unittest.TestCase):
    def test_prefect_example_defers_cluster_creation_to_task_runner(self) -> None:
        text = (SKILL_ROOT / "prefect-hpc-slurm.md").read_text(encoding="utf-8")
        self.assertIn('cluster_class="dask_jobqueue.SLURMCluster"', text)
        self.assertNotIn("address=build_cluster()", text)

    def test_compound_fastq_suffix_has_explicit_normalizer(self) -> None:
        text = (SKILL_ROOT / "prefect-dask.md").read_text(encoding="utf-8")
        self.assertIn('(".fastq.gz", ".fq.gz", ".fastq", ".fq")', text)
        self.assertNotIn("sample_out = outdir / reads.stem", text)


if __name__ == "__main__":
    unittest.main()
