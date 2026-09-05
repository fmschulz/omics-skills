from __future__ import annotations

import csv
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "tracking-taxonomy-updates"
CONVERTER = SKILL_ROOT / "scripts" / "quickclade_to_routing.py"
FIXTURE = SKILL_ROOT / "fixtures" / "quickclade-machine.tsv"


class TrackingTaxonomyUpdatesTests(unittest.TestCase):
    def test_quickclade_fixture_routes_all_domains(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "domain_routing.tsv"
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "--no-project",
                    "python",
                    str(CONVERTER),
                    str(FIXTURE),
                    "--sample-id",
                    "sample-1",
                    "--output",
                    str(output),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with output.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            self.assertEqual([row["downstream_tool"] for row in rows], ["gtdbtk", "eukcc", "gvclass", ""])
            self.assertEqual(rows[-1]["review_flag"], "true")


if __name__ == "__main__":
    unittest.main()
